"""数据集 ORM 模型。"""
from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # API 目前直接接收小型 JSON 数据集；先持久化样本，执行链路才不会丢数据。
    samples: Mapped[list | None] = mapped_column(JSON, nullable=True)

    jobs: Mapped[list["EvaluationJob"]] = relationship(back_populates="dataset")
