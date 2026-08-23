"""评测任务业务逻辑。"""
from __future__ import annotations

from app.core.errors import NotFoundError
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.evaluation import EvaluationCreate, JobResponse


class EvaluationService:
    """创建评测任务：dataset 必须存在。"""

    def __init__(self, repository: DatasetRepository) -> None:
        self._repository = repository
        self._next_job_id = 1

    def create(self, payload: EvaluationCreate) -> JobResponse:
        if not self._repository.exists(payload.dataset_id):
            raise NotFoundError(f"dataset {payload.dataset_id!r} not found")
        job_id = f"job-{self._next_job_id}"
        self._next_job_id += 1
        return JobResponse(
            job_id=job_id,
            status="pending",
            dataset_id=payload.dataset_id,
            providers=payload.providers,
            evaluators=payload.evaluators,
            concurrency=payload.concurrency,
        )