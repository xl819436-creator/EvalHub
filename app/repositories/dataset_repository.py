"""数据集数据库 Repository。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate, DatasetOut


class DatasetRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, payload: DatasetCreate) -> DatasetOut:
        existing = self._db.query(Dataset).filter(Dataset.name == payload.name).first()
        if existing is not None:
            raise ConflictError(f"dataset name {payload.name!r} already exists")
        dataset_id = f"ds-{len(self._db.query(Dataset).all()) + 1}"
        dataset = Dataset(
            id=dataset_id,
            name=payload.name,
            samples=[sample.model_dump() for sample in payload.samples],
        )
        self._db.add(dataset)
        self._db.commit()
        self._db.refresh(dataset)
        return DatasetOut(dataset_id=dataset.id, name=dataset.name, sample_count=len(payload.samples))

    def get(self, dataset_id: str) -> Dataset | None:
        return self._db.get(Dataset, dataset_id)

    def exists(self, dataset_id: str) -> bool:
        return self.get(dataset_id) is not None
