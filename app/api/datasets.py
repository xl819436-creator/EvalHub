"""数据集与根路径路由：只转发，不写业务。"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_dataset_service
from app.schemas.dataset import DatasetCreate, DatasetOut
from app.services.dataset_service import DatasetService
from evalhub_core.llm_provider import ProviderFactory

router = APIRouter(tags=["datasets"])


@router.get("/")
def root() -> dict[str, str]:
    """服务信息。"""
    return {"service": "evalhub", "docs": "/docs"}


@router.get("/health")
def health() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok", "service": "evalhub"}


@router.get("/models")
def list_models() -> dict[str, list[str]]:
    """列出当前代码注册的 Provider；便于客户端先发现可用模型。"""
    return {"models": ProviderFactory.available()}


@router.post("/datasets", status_code=201, response_model=DatasetOut)
def create_dataset(
    payload: DatasetCreate,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetOut:
    """创建数据集（业务在 service）。"""
    return service.create(payload)


@router.get("/datasets/{dataset_id}", response_model=DatasetOut)
def get_dataset(
    dataset_id: str,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetOut:
    """查询已保存数据集的元信息和样本数量。"""
    return service.get(dataset_id)
