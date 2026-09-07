"""评测任务业务逻辑：状态转换、执行与持久化。"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, NotFoundError
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationJob, EvaluationRun
from app.repositories.job_repository import JobRepository
from app.schemas.evaluation import (
    EvaluationCreate,
    JobResponse,
    JobStatusResponse,
    RunResponse,
)
from evalhub_core.report_builder import build_markdown_report
from evalhub_core.evaluators import EvaluationItem, EvaluatorRegistry
from evalhub_core.llm_config import LLMConfig
from evalhub_core.llm_provider import ProviderFactory
from evalhub_core.schemas import LLMRequest

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running", "cancelled"},
    "running": {"completed", "completed_with_errors", "failed", "cancelled"},
    "completed": set(),
    "completed_with_errors": set(),
    "failed": set(),
    "cancelled": set(),
}

TERMINAL_STATUSES = {"completed", "completed_with_errors", "failed", "cancelled"}
LOCAL_EXECUTABLE_PROVIDERS = {"mock", "dummy"}


class EvaluationService:
    """创建任务 + 状态转换校验。"""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = JobRepository(db)

    def create(self, payload: EvaluationCreate) -> JobResponse:
        dataset = self._db.get(Dataset, payload.dataset_id)
        if dataset is None:
            raise NotFoundError(f"dataset {payload.dataset_id!r} not found")
        job = EvaluationJob(
            id=f"job-{payload.dataset_id}-{len(dataset.jobs) + 1}",
            dataset_id=payload.dataset_id,
            status="pending",
            providers=payload.providers,
            evaluators=payload.evaluators,
            concurrency=payload.concurrency,
            temperature=payload.temperature,
        )
        self._repo.create_job(job)
        return JobResponse(
            job_id=job.id,
            status=job.status,
            dataset_id=job.dataset_id,
            providers=job.providers,
            evaluators=job.evaluators,
            concurrency=job.concurrency,
        )

    def run(self, job_id: str):
        """同步执行一个小型本地任务，并把每条样本结果写入数据库。

        # ponytail: 先提供可复现的同步入口；需要吞吐量时再替换成队列/Worker。
        """
        job = self.get(job_id)
        if job.status in TERMINAL_STATUSES:
            return job
        if job.status != "pending":
            raise BadRequestError(f"job {job_id!r} is not ready to run")
        if len(job.providers) != 1:
            raise BadRequestError("当前执行入口每个任务只支持一个 provider")

        provider_name = job.providers[0]
        if provider_name not in LOCAL_EXECUTABLE_PROVIDERS:
            raise BadRequestError(
                f"provider {provider_name!r} 暂不支持本地执行，请使用 mock 或 dummy"
            )
        try:
            evaluators = [EvaluatorRegistry.get(name) for name in job.evaluators]
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc

        dataset = self._db.get(Dataset, job.dataset_id)
        samples = (dataset.samples if dataset is not None else None) or []
        if not samples:
            raise BadRequestError("dataset 没有可执行的 samples")

        self._repo.update_progress(job, "running")
        provider = ProviderFactory.create(
            LLMConfig(
                provider=provider_name,
                model=provider_name,
                temperature=job.temperature,
            )
        )
        failed_runs = 0
        for index, sample in enumerate(samples):
            run_status = "completed"
            score = 0.0
            actual = ""
            expected = sample["expected_output"]
            expected_text = (
                expected
                if isinstance(expected, str)
                else json.dumps(expected, ensure_ascii=False, sort_keys=True)
            )
            reason = None
            try:
                response = provider.generate(
                    LLMRequest(
                        model=provider_name,
                        input=sample["input"],
                        temperature=job.temperature,
                    )
                )
                actual = response.content or ""
                if not response.success:
                    run_status = "failed"
                    reason = response.error_type or "provider_error"
                else:
                    item = EvaluationItem(
                        id=f"{job.id}-run-{index}",
                        category="all",
                        input=sample["input"],
                        expected=expected_text,
                        actual=actual,
                    )
                    for evaluator in evaluators:
                        item = evaluator.evaluate(item)
                    score = sum(item.scores.values()) / len(item.scores)
                    if not item.passed:
                        run_status = "failed"
                        reason = item.reason
            except Exception as exc:
                run_status = "failed"
                reason = f"{type(exc).__name__}: {exc}"

            if run_status == "failed":
                failed_runs += 1
            self._db.add(
                EvaluationRun(
                    id=f"{job.id}-run-{index}",
                    job_id=job.id,
                    sample_index=index,
                    status=run_status,
                    score=score,
                    input=sample["input"],
                    expected=expected_text,
                    actual=actual,
                    reason=reason,
                )
            )

        self._db.commit()
        final_status = "completed_with_errors" if failed_runs else "completed"
        return self._repo.update_progress(job, final_status)

    def transition(self, job_id: str, new_status: str) -> None:
        job = self._repo.get_job(job_id)
        if job is None:
            raise NotFoundError(f"job {job_id!r} not found")
        if new_status not in ALLOWED_TRANSITIONS.get(job.status, set()):
            raise ValueError(
                f"invalid transition {job.status!r} -> {new_status!r}"
            )
        self._repo.update_progress(job, new_status)

    def get(self, job_id: str):
        """查询任务；不存在时使用统一业务异常。"""
        job = self._repo.get_job(job_id)
        if job is None:
            raise NotFoundError(f"job {job_id!r} not found")
        return job

    def get_status(self, job_id: str, offset: int = 0, limit: int = 100) -> JobStatusResponse:
        """返回任务状态、计数和分页后的 run 摘要。"""
        job = self.get(job_id)
        all_runs = sorted(job.runs, key=lambda run: run.sample_index)
        runs = all_runs[offset : offset + limit]
        completed = sum(run.status == "completed" for run in all_runs)
        failed = sum(run.status == "failed" for run in all_runs)
        cancelled = sum(run.status == "cancelled" for run in all_runs)
        return JobStatusResponse(
            **self._job_response_data(job),
            total_runs=len(all_runs),
            completed_runs=completed,
            failed_runs=failed,
            cancelled_runs=cancelled,
            runs=[
                RunResponse(
                    run_id=run.id,
                    sample_index=run.sample_index,
                    status=run.status,
                    score=run.score,
                )
                for run in runs
            ],
        )

    def cancel(self, job_id: str):
        """取消未终止任务；终止任务重复取消时原样返回。"""
        job = self.get(job_id)
        if job.status in TERMINAL_STATUSES:
            return job
        return self._repo.update_progress(job, "cancelled")

    def to_response(self, job) -> JobResponse:
        """把 ORM 任务转换为创建/取消接口共用的响应模型。"""
        return JobResponse(**self._job_response_data(job))

    def build_report(self, job_id: str) -> str:
        """从已持久化的 runs 生成 Markdown 报告，不补造缺失字段。"""
        job = self.get(job_id)
        runs = sorted(job.runs, key=lambda run: run.sample_index)
        completed = sum(run.status == "completed" for run in runs)
        scores = [run.score for run in runs if run.score is not None]
        accuracy = sum(scores) / len(scores) if scores else 0.0
        total = len(runs)
        failures = [
            {
                "id": run.id,
                "expected": run.expected or "未持久化",
                "actual": run.actual or "未持久化",
                "reason": run.reason or run.status,
            }
            for run in runs
            if run.status != "completed"
        ]
        manifest = {
            "dataset_hash": "未由当前 API 持久化",
            "git_commit": "未由当前 API 持久化",
            "provider": ", ".join(job.providers),
            "model": "未由当前 API 持久化",
            "seed": "未由当前 API 持久化",
            "start_time": "未由当前 API 持久化",
        }
        return build_markdown_report(
            job_id,
            manifest=manifest,
            groups={
                "all": {
                    "total": total,
                    "success_rate": completed / total if total else 0.0,
                    "accuracy": accuracy,
                }
            },
            failures=failures,
        )

    @staticmethod
    def _job_response_data(job) -> dict:
        return {
            "job_id": job.id,
            "status": job.status,
            "dataset_id": job.dataset_id,
            "providers": job.providers,
            "evaluators": job.evaluators,
            "concurrency": job.concurrency,
        }

"""Day 26：任务管理器（内存版）——状态机 + 取消幂等。"""

from evalhub_core.eval_runner import EvalJob, run_job
from evalhub_core.job_state_machine import TERMINAL_STATES


class EvaluationManager:
    def __init__(self) -> None:
        self.jobs: dict[str, EvalJob] = {}
        self._cancel_flags: dict[str, list[bool]] = {}

    def create(self, job_id: str, total: int) -> EvalJob:
        job = EvalJob(job_id=job_id, status="pending")
        self.jobs[job_id] = job
        self._cancel_flags[job_id] = [False]
        return job

    def execute(self, job_id: str, total: int, seed: int = 42,
                fail_indexes: set[int] | None = None) -> EvalJob:
        job = self.jobs[job_id]
        return run_job(job, total, lambda i: None, seed=seed,
                       cancel_flag=self._cancel_flags[job_id], fail_indexes=fail_indexes)

    def cancel(self, job_id: str) -> EvalJob:
        """幂等取消：终态任务重复取消直接返回，不重复修改计数。"""
        job = self.jobs.get(job_id)
        if job is None:
            raise KeyError(f"任务不存在：{job_id}")
        if job.status in TERMINAL_STATES:
            return job  # 幂等：不重复修改
        self._cancel_flags[job_id][0] = True
        return job

    def status(self, job_id: str) -> EvalJob:
        if job_id not in self.jobs:
            raise KeyError(f"任务不存在：{job_id}")
        return self.jobs[job_id]
