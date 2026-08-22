"""EvalHub - Day 15：FastAPI 应用入口（四个基础接口）。"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.schemas import (
    DatasetCreate,
    DatasetOut,
    EvaluationCreate,
    JobResponse,
)

app = FastAPI(
    title="EvalHub API",
    description="EvalHub 评测平台核心 API（Day 15）",
    version="0.1.0",
)

# 内存暂存（Day 18 将替换为 SQLAlchemy）
DATASETS: dict[str, dict] = {}
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


@app.get("/")
def root() -> dict[str, str]:
    """服务信息。"""
    return {"service": "evalhub", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查（与 evalhub_core.health.get_health 同款）。"""
    return {"status": "ok", "service": "evalhub"}


@app.post("/datasets", status_code=201, response_model=DatasetOut)
def create_dataset(payload: DatasetCreate) -> DatasetOut:
    """创建数据集（暂存内存）。"""
    dataset_id = _next_dataset_id()
    DATASETS[dataset_id] = {
        "id": dataset_id,
        "name": payload.name,
        "samples": [s.model_dump() for s in payload.samples],
    }
    return DatasetOut(
        dataset_id=dataset_id,
        name=payload.name,
        sample_count=len(payload.samples),
    )


@app.post("/evaluations", status_code=202, response_model=JobResponse)
def create_evaluation(payload: EvaluationCreate) -> JobResponse:
    """创建评测任务（占位实现，Day 26 接入后台执行）。"""
    if payload.dataset_id not in DATASETS:
        raise HTTPException(
            status_code=404,
            detail=f"dataset {payload.dataset_id!r} not found",
        )
    return JobResponse(
        job_id=_next_job_id(),
        status="pending",
        dataset_id=payload.dataset_id,
        providers=payload.providers,
        evaluators=payload.evaluators,
        concurrency=payload.concurrency,
    )
