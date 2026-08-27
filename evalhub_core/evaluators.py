"""Day 25：评分器接口与实现（BaseEvaluator / ExactMatchEvaluator / JsonSchemaEvaluator）。"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict

from evalhub_core.evaluator import exact_match


@dataclass
class EvaluationItem:
    """一条评测结果（失败案例保留 input / expected / actual / reason）。"""

    id: str
    category: str
    input: str
    expected: str
    actual: str
    scores: Dict[str, float] = field(default_factory=dict)
    passed: bool = True
    reason: str | None = None


class BaseEvaluator(ABC):
    """所有评分器的统一接口。"""

    name: str = "base"

    @abstractmethod
    def evaluate(self, item: EvaluationItem) -> EvaluationItem:
        """对一条记录打分，把分数写进 item.scores。"""
        raise NotImplementedError


class ExactMatchEvaluator(BaseEvaluator):
    """正确性评分器：预测与标准答案完全一致（复用 Day 5 的 exact_match）。"""

    name = "exact_match"

    def evaluate(self, item: EvaluationItem) -> EvaluationItem:
        matched = exact_match(item.actual, item.expected)
        item.scores["accuracy"] = 1.0 if matched else 0.0
        if not matched:
            item.passed = False
            item.reason = (
                f"exact_match 不匹配：actual={item.actual!r}, expected={item.expected!r}"
            )
        return item


class JsonSchemaEvaluator(BaseEvaluator):
    """格式评分器：输出是否为合法 JSON 对象（与内容正确性分开，验收③）。"""

    name = "json_schema"

    def evaluate(self, item: EvaluationItem) -> EvaluationItem:
        try:
            data = json.loads(item.actual)
            valid = isinstance(data, dict)
            item.scores["format_rate"] = 1.0 if valid else 0.0
            if not valid:
                item.reason = "输出是 JSON 但不是对象"
        except json.JSONDecodeError as exc:
            item.scores["format_rate"] = 0.0
            item.reason = f"非法 JSON：{exc.msg}"
        return item


class EvaluatorRegistry:
    """评分器注册表：新增评分器只注册一行（对应 Day 22 的工厂思想）。"""

    _registry: Dict[str, BaseEvaluator] = {}

    @classmethod
    def register(cls, evaluator: BaseEvaluator) -> None:
        cls._registry[evaluator.name] = evaluator

    @classmethod
    def get(cls, name: str) -> BaseEvaluator:
        if name not in cls._registry:
            raise ValueError(f"未知评分器：{name}，可用：{sorted(cls._registry)}")
        return cls._registry[name]

    @classmethod
    def names(cls) -> list[str]:
        return sorted(cls._registry)


# 内置注册：新增评分器就在这里加一行
EvaluatorRegistry.register(ExactMatchEvaluator())
EvaluatorRegistry.register(JsonSchemaEvaluator())