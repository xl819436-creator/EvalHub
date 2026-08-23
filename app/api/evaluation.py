"""评测任务路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_evaluation_service
from app.schemas.evaluation import EvaluationCreate, JobResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["evaluations"])


@router.post("/evaluations", status_code=202, response_model=JobResponse)
def create_evaluation(
    payload: EvaluationCreate,
    service: EvaluationService = Depends(get_evaluation_service),
) -> JobResponse:
    """创建评测任务。"""
    return service.create(payload)