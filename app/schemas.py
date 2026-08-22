"""EvalHub API 请求/响应模型（Day 15 基础版；Day 16 会加强约束）。"""
from __future__ import annotations

from typing import List, Union

from pydantic import BaseModel, Field


class DatasetSample(BaseModel):
    """一条测试样本。"""

    input: str = Field(min_length=1, description="测试输入")
    expected_output: Union[str, dict] = Field(description="期望输出")


class DatasetCreate(BaseModel):
    """创建数据集请求体。"""

    name: str = Field(min_length=1, description="数据集名称")
    samples: List[DatasetSample] = Field(default_factory=list, description="样本列表")


class DatasetOut(BaseModel):
    """创建数据集成功响应。"""

    dataset_id: str = Field(description="数据集ID")
    name: str = Field(description="数据集名称")
    sample_count: int = Field(ge=0, description="样本数量")


class EvaluationCreate(BaseModel):
    """创建评测任务请求体。"""

    dataset_id: str = Field(min_length=1, description="目标数据集ID")
    providers: List[str] = Field(description="评测使用的Provider列表")
    evaluators: List[str] = Field(description="评测使用的评分器列表")
    concurrency: int = Field(default=3, ge=1, le=20, description="并发上限")


class JobResponse(BaseModel):
    """创建评测任务成功响应。"""

    job_id: str = Field(description="任务ID")
    status: str = Field(description="任务状态")
    dataset_id: str = Field(description="目标数据集ID")
    providers: List[str] = Field(description="Provider列表")
    evaluators: List[str] = Field(description="评分器列表")
    concurrency: int = Field(description="并发上限")