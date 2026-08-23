"""数据集相关模型。"""
from __future__ import annotations

from typing import List, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatasetSample(ApiModel):
    input: str = Field(min_length=1)
    expected_output: Union[str, dict]

    @field_validator("input")
    @classmethod
    def input_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("input 不能为空")
        return value


class DatasetCreate(ApiModel):
    name: str = Field(min_length=1)
    samples: List[DatasetSample] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name 不能为空")
        return cleaned


class DatasetOut(ApiModel):
    dataset_id: str
    name: str
    sample_count: int = Field(ge=0)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"dataset_id": "ds-1", "name": "demo", "sample_count": 1}]
        },
    )