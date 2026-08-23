"""数据集与根路径路由：只转发，不写业务。"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_dataset_service
from app.schemas.dataset import DatasetCreate, DatasetOut
from app.services.dataset_service import DatasetService

router = APIRouter(tags=["datasets"])


@router.get("/")
def root() -> dict[str, str]:
    """服务信息。"""
    return {"service": "evalhub", "docs": "/docs"}


@router.get("/health")
def health() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok", "service": "evalhub"}


@router.post("/datasets", status_code=201, response_model=DatasetOut)
def create_dataset(
    payload: DatasetCreate,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetOut:
    """创建数据集（业务在 service）。"""
    return service.create(payload)