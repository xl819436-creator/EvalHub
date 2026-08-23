"""FastAPI 依赖注入：组装 repository -> service 并交给路由。"""
from __future__ import annotations

from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.services.evaluation_service import EvaluationService

_dataset_repository = DatasetRepository()
_dataset_service = DatasetService(_dataset_repository)
_evaluation_service = EvaluationService(_dataset_repository)


def get_dataset_service() -> DatasetService:
    return _dataset_service


def get_evaluation_service() -> EvaluationService:
    return _evaluation_service


def reset_repositories() -> None:
    """测试用：重置内存存储。"""
    _dataset_repository.reset()