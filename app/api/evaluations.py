"""评测任务路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_evaluation_service
from app.schemas.evaluation import EvaluationCreate, JobResponse, JobStatusResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["evaluations"])


@router.post("/evaluations", status_code=202, response_model=JobResponse)
def create_evaluation(
    payload: EvaluationCreate,
    service: EvaluationService = Depends(get_evaluation_service),
) -> JobResponse:
    """创建评测任务。"""
    return service.create(payload)


@router.get("/evaluations/{job_id}", response_model=JobStatusResponse)
def get_evaluation(
    job_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: EvaluationService = Depends(get_evaluation_service),
) -> JobStatusResponse:
    """查询任务状态和已持久化的运行记录。"""
    return service.get_status(job_id, offset=offset, limit=limit)


@router.post("/evaluations/{job_id}/cancel", response_model=JobResponse)
def cancel_evaluation(
    job_id: str,
    service: EvaluationService = Depends(get_evaluation_service),
) -> JobResponse:
    """取消任务；对终态任务重复取消保持幂等。"""
    job = service.cancel(job_id)
    return service.to_response(job)


@router.get(
    "/evaluations/{job_id}/report",
    response_class=PlainTextResponse,
    responses={404: {"description": "任务不存在"}},
)
def get_evaluation_report(
    job_id: str,
    service: EvaluationService = Depends(get_evaluation_service),
) -> PlainTextResponse:
    """返回当前已持久化结果生成的 Markdown 报告。"""
    return PlainTextResponse(service.build_report(job_id), media_type="text/markdown")
