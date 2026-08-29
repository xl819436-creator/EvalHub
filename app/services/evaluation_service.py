"""评测任务业务逻辑：状态转换 + 持久化。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationJob
from app.repositories.job_repository import JobRepository
from app.schemas.evaluation import (
    EvaluationCreate,
    JobResponse,
    JobStatusResponse,
    RunResponse,
)
from evalhub_core.report_builder import build_markdown_report

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running", "cancelled"},
    "running": {"completed", "completed_with_errors", "failed", "cancelled"},
    "completed": set(),
    "completed_with_errors": set(),
    "failed": set(),
    "cancelled": set(),
}

TERMINAL_STATUSES = {"completed", "completed_with_errors", "failed", "cancelled"}


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
                "expected": "未持久化",
                "actual": "未持久化",
                "reason": run.status,
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
