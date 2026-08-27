"""Day 26：评测执行器——队列逐条跑，局部失败不扩散。"""

import random
from dataclasses import dataclass, field
from typing import Callable, List

from evalhub_core.job_state_machine import transition


@dataclass
class RunResult:
    """单条 run 的结果。"""

    run_id: str
    status: str  # completed / failed / cancelled
    reason: str | None = None


@dataclass
class EvalJob:
    """一个评测任务。"""

    job_id: str
    status: str = "pending"
    runs: List[RunResult] = field(default_factory=list)


def run_job(
    job: EvalJob,
    total: int,
    execute_one: Callable[[int], None],
    seed: int = 42,
    cancel_flag: List[bool] | None = None,
    fail_indexes: set[int] | None = None,
) -> EvalJob:
    """按顺序执行 total 条；遇到 cancel_flag 停止未开始的；返回更新后的 job。"""
    random.seed(seed)
    cancel = cancel_flag or [False]
    failures = fail_indexes or set()

    transition(job.status, "running")
    job.status = "running"

    for index in range(total):
        if cancel[0]:
            # 取消：停止未开始任务（当前 index 起标记 cancelled）
            for rest in range(index, total):
                job.runs.append(RunResult(run_id=f"run-{rest}", status="cancelled"))
            job.status = "cancelled"
            return job
        try:
            execute_one(index)
            status = "failed" if index in failures else "completed"
            job.runs.append(RunResult(run_id=f"run-{index}", status=status))
        except Exception as exc:
            job.runs.append(RunResult(run_id=f"run-{index}", status="failed", reason=str(exc)))

    failed_count = sum(1 for run in job.runs if run.status == "failed")
    job.status = "completed_with_errors" if failed_count > 0 else "completed"
    return job