"""EvalHub - Day 16：稳定 API Schema + 统一错误契约。"""
from __future__ import annotations

import uuid

from fastapi import FastAPI, Request

from app.errors import ConflictError, NotFoundError, register_error_handlers
from app.schemas import (
    DatasetCreate,
    DatasetOut,
    EvaluationCreate,
    JobResponse,
)

app = FastAPI(
    title="EvalHub API",
    description="EvalHub 评测平台核心 API（Day 16：统一错误契约）",
    version="0.1.0",
)
register_error_handlers(app)

# 内存暂存（Day 18 将替换为 SQLAlchemy）
DATASETS: dict[str, dict] = {}
DATASET_NAMES: set[str] = set()
_NEXT_DATASET_ID = 1
_NEXT_JOB_ID = 1


def _next_dataset_id() -> str:
    global _NEXT_DATASET_ID
    value = f"ds-{_NEXT_DATASET_ID}"
    _NEXT_DATASET_ID += 1
    return value


def _next_job_id() -> str:
    global _NEXT_JOB_ID
    value = f"job-{_NEXT_JOB_ID}"
    _NEXT_JOB_ID += 1
    return value


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    """为每个请求生成 request_id，写入响应头，供错误响应使用。"""
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


@app.get("/")
def root() -> dict[str, str]:
    """服务信息。"""
    return {"service": "evalhub", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok", "service": "evalhub"}


@app.post("/datasets", status_code=201, response_model=DatasetOut)
def create_dataset(payload: DatasetCreate) -> DatasetOut:
    """创建数据集；同名重复返回 409（实战 2）。"""
    if payload.name in DATASET_NAMES:
        raise ConflictError(f"dataset name {payload.name!r} already exists")
    dataset_id = _next_dataset_id()
    DATASETS[dataset_id] = {
        "id": dataset_id,
        "name": payload.name,
        "samples": [s.model_dump() for s in payload.samples],
    }
    DATASET_NAMES.add(payload.name)
    return DatasetOut(
        dataset_id=dataset_id,
        name=payload.name,
        sample_count=len(payload.samples),
    )


@app.post("/evaluations", status_code=202, response_model=JobResponse)
def create_evaluation(payload: EvaluationCreate) -> JobResponse:
    """创建评测任务；dataset 不存在返回 404（实战 1）。"""
    if payload.dataset_id not in DATASETS:
        raise NotFoundError(f"dataset {payload.dataset_id!r} not found")
    return JobResponse(
        job_id=_next_job_id(),
        status="pending",
        dataset_id=payload.dataset_id,
        providers=payload.providers,
        evaluators=payload.evaluators,
        concurrency=payload.concurrency,
    )