"""评测任务数据库 Repository：只做 CRUD，不含业务规则。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationJob, EvaluationRun


class JobRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_job(self, job: EvaluationJob) -> EvaluationJob:
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job

    def get_job(self, job_id: str) -> EvaluationJob | None:
        return self._db.get(EvaluationJob, job_id)

    def update_progress(self, job: EvaluationJob, status: str) -> EvaluationJob:
        job.status = status
        self._db.commit()
        self._db.refresh(job)
        return job

    def list_runs(self, job_id: str, offset: int = 0, limit: int = 10) -> list[EvaluationRun]:
        stmt = (
            select(EvaluationRun)
            .where(EvaluationRun.job_id == job_id)
            .order_by(EvaluationRun.sample_index)
            .offset(offset)
            .limit(limit)
        )
        return list(self._db.scalars(stmt))