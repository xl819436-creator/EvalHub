"""评测任务与运行记录 ORM 模型（一对多）。"""
from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    providers: Mapped[list] = mapped_column(JSON, nullable=False)
    evaluators: Mapped[list] = mapped_column(JSON, nullable=False)
    concurrency: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    dataset: Mapped["Dataset"] = relationship(back_populates="jobs")
    runs: Mapped[list["EvaluationRun"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("evaluation_jobs.id"), nullable=False)
    sample_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[float | None] = mapped_column(nullable=True)

    job: Mapped["EvaluationJob"] = relationship(back_populates="runs")