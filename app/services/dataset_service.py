"""数据集业务逻辑：转发 repository，后续可在此叠加业务规则。"""
from __future__ import annotations

from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import DatasetCreate, DatasetOut


class DatasetService:
    """数据集业务服务：把存储委托给 repository。"""

    def __init__(self, repository: DatasetRepository) -> None:
        self._repository = repository

    def create(self, payload: DatasetCreate) -> DatasetOut:
        return self._repository.create(payload)

    def exists(self, dataset_id: str) -> bool:
        return self._repository.exists(dataset_id)
