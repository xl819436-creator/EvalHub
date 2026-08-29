"""评测任务相关模型。"""
from __future__ import annotations

from typing import List

from pydantic import ConfigDict, Field, field_validator

from app.schemas.dataset import ApiModel


class EvaluationCreate(ApiModel):
    dataset_id: str = Field(min_length=1)
    providers: List[str] = Field(min_length=1)
    evaluators: List[str] = Field(min_length=1)
    concurrency: int = Field(default=3, ge=1, le=20)
    temperature: float = Field(default=0.7, ge=0, le=2)

    @field_validator("dataset_id")
    @classmethod
    def dataset_id_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("dataset_id 不能为空")
        return cleaned

    @field_validator("providers", "evaluators")
    @classmethod
    def items_not_blank(cls, values: List[str]) -> List[str]:
        cleaned = [v.strip() for v in values]
        if any(v == "" for v in cleaned):
            raise ValueError("列表元素不能为空")
        return cleaned


class JobResponse(ApiModel):
    job_id: str
    status: str
    dataset_id: str
    providers: List[str]
    evaluators: List[str]
    concurrency: int

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{
                "job_id": "job-1",
                "status": "pending",
                "dataset_id": "ds-1",
                "providers": ["mock"],
                "evaluators": ["exact_match"],
                "concurrency": 3,
            }]
        },
    )


class RunResponse(ApiModel):
    """任务中的一条持久化运行记录。"""

    run_id: str
    sample_index: int = Field(ge=0)
    status: str
    score: float | None = None


class JobStatusResponse(JobResponse):
    """任务详情和当前已持久化的 run 摘要。"""

    total_runs: int = Field(ge=0)
    completed_runs: int = Field(ge=0)
    failed_runs: int = Field(ge=0)
    cancelled_runs: int = Field(ge=0)
    runs: List[RunResponse]
