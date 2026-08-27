"""Day 25：聚合指标（成功率/准确率/格式率/均值/P50/P95/Token/成本）与分组。"""

from typing import Any, Dict, List, Optional

from evalhub_core.evaluators import EvaluationItem


def percentile(values: List[float], p: float) -> float:
    """百分位数（p 为 0~100）；空列表返回 0.0。"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * p / 100
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    frac = index - lower
    return sorted_values[lower] * (1 - frac) + sorted_values[upper] * frac


def aggregate(items: List[EvaluationItem], latencies: Optional[List[float]] = None) -> Dict[str, Any]:
    """汇总全部评测结果的指标。"""
    total = len(items)
    passed = sum(1 for item in items if item.passed)
    accuracy = sum(item.scores.get("accuracy", 0.0) for item in items) / total if total else 0.0
    format_rate = sum(item.scores.get("format_rate", 0.0) for item in items) / total if total else 0.0
    latency_values = latencies or []
    return {
        "total": total,
        "success_rate": passed / total if total else 0.0,
        "accuracy": accuracy,
        "format_rate": format_rate,
        "latency_ms": {
            "mean": sum(latency_values) / len(latency_values) if latency_values else 0.0,
            "p50": percentile(latency_values, 50),
            "p95": percentile(latency_values, 95),
        },
    }


def token_cost(tokens: int, price_per_million: float) -> float:
    """Token 成本：每百万 token 单价 × token 数 / 1e6；价格可配置（验收④）。"""
    return tokens * price_per_million / 1_000_000


def group_by_category(items: List[EvaluationItem]) -> Dict[str, Dict[str, Any]]:
    """按 category 分组聚合。"""
    groups: Dict[str, List[EvaluationItem]] = {}
    for item in items:
        groups.setdefault(item.category, []).append(item)
    return {category: aggregate(group) for category, group in groups.items()}