"""统一错误响应模型。"""
from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict, Field

from app.schemas.dataset import ApiModel


class ErrorResponse(ApiModel):
    code: str = Field(description="稳定错误码")
    message: str = Field(description="错误描述")
    request_id: str = Field(description="请求追踪ID")
    details: Optional[dict] = Field(default=None)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{
                "code": "NOT_FOUND",
                "message": "dataset 'ds-99' not found",
                "request_id": "abc-123",
                "details": None,
            }]
        },
    )