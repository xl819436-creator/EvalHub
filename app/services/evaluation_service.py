"""评测任务业务逻辑：状态转换 + 持久化。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationJob
from app.repositories.job_repository import JobRepository
from app.schemas.evaluation import EvaluationCreate, JobResponse

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}


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