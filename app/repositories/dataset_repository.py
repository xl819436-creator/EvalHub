"""数据集存储：内存实现（Day 18 将替换为 SQLAlchemy 实现）。"""
from __future__ import annotations

from app.core.errors import ConflictError
from app.schemas.dataset import DatasetCreate, DatasetOut


class DatasetRepository:
    """数据集的内存存储与查询。"""

    def __init__(self) -> None:
        self._datasets: dict[str, dict] = {}
        self._names: set[str] = set()
        self._next_id = 1

    def create(self, payload: DatasetCreate) -> DatasetOut:
        if payload.name in self._names:
            raise ConflictError(f"dataset name {payload.name!r} already exists")
        dataset_id = f"ds-{self._next_id}"
        self._next_id += 1
        self._datasets[dataset_id] = {
            "id": dataset_id,
            "name": payload.name,
            "samples": [s.model_dump() for s in payload.samples],
        }
        self._names.add(payload.name)
        return DatasetOut(
            dataset_id=dataset_id,
            name=payload.name,
            sample_count=len(payload.samples),
        )

    def exists(self, dataset_id: str) -> bool:
        return dataset_id in self._datasets

    def reset(self) -> None:
        """测试用：清空内存状态。"""
        self._datasets.clear()
        self._names.clear()
        self._next_id = 1