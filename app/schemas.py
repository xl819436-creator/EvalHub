"""EvalHub API 请求/响应模型（Day 16：约束 + Swagger 示例）。"""
from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiModel(BaseModel):
    """API 层模型基类：未知字段直接校验失败。"""

    model_config = ConfigDict(extra="forbid")


class DatasetSample(ApiModel):
    """一条测试样本。"""

    input: str = Field(min_length=1, description="测试输入")
    expected_output: Union[str, dict] = Field(description="期望输出")

    @field_validator("input")
    @classmethod
    def input_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("input 不能为空")
        return value


class DatasetCreate(ApiModel):
    """创建数据集请求体。"""

    name: str = Field(min_length=1, description="数据集名称")
    samples: List[DatasetSample] = Field(min_length=1, description="样本列表（至少一条）")

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name 不能为空")
        return cleaned


class DatasetOut(ApiModel):
    """创建数据集成功响应。"""

    dataset_id: str = Field(description="数据集ID")
    name: str = Field(description="数据集名称")
    sample_count: int = Field(ge=0, description="样本数量")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"dataset_id": "ds-1", "name": "demo", "sample_count": 1}
            ]
        },
    )


class EvaluationCreate(ApiModel):
    """创建评测任务请求体（Day 16 加强约束）。"""

    dataset_id: str = Field(min_length=1, description="目标数据集ID")
    providers: List[str] = Field(min_length=1, description="Provider列表（至少一个）")
    evaluators: List[str] = Field(min_length=1, description="评分器列表（至少一个）")
    concurrency: int = Field(default=3, ge=1, le=20, description="并发上限 1-20")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度 0-2")

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
    """创建评测任务成功响应。"""

    job_id: str = Field(description="任务ID")
    status: str = Field(description="任务状态")
    dataset_id: str = Field(description="目标数据集ID")
    providers: List[str] = Field(description="Provider列表")
    evaluators: List[str] = Field(description="评分器列表")
    concurrency: int = Field(description="并发上限")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "job_id": "job-1",
                    "status": "pending",
                    "dataset_id": "ds-1",
                    "providers": ["mock"],
                    "evaluators": ["exact_match"],
                    "concurrency": 3,
                }
            ]
        },
    )


class ErrorResponse(ApiModel):
    """统一业务错误响应（code/message/request_id 三个必填字段）。"""

    code: str = Field(description="稳定错误码，如 NOT_FOUND / CONFLICT / VALIDATION_ERROR")
    message: str = Field(description="人类可读的错误描述")
    request_id: str = Field(description="本次请求的追踪ID")
    details: Optional[dict] = Field(default=None, description="可选的补充细节")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "code": "NOT_FOUND",
                    "message": "dataset 'ds-99' not found",
                    "request_id": "abc-123",
                    "details": None,
                }
            ]
        },
    )