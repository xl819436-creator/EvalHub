"""Day 25：聚合指标测试（含 P95 手算核对）。"""

import pytest

from evalhub_core.evaluators import EvaluationItem, ExactMatchEvaluator, JsonSchemaEvaluator
from evalhub_core.metrics import aggregate, percentile, token_cost


def test_percentile_empty_list_returns_zero():
    assert percentile([], 95) == 0.0


def test_percentile_single_value():
    assert percentile([5.0], 50) == 5.0
    assert percentile([5.0], 95) == 5.0


def test_percentile_p50_hand_calculated():
    # 实战题 1：10 个延迟值手算中位数核对
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    # 排序后第 (10-1)*0.5 = 4.5 个位置 → 插值 (50+60)/2 = 55
    assert percentile(values, 50) == pytest.approx(55.0)


def test_percentile_p95_hand_calculated():
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    # 第 (10-1)*0.95 = 8.55 个位置 → 0.45*90 + 0.55*100 = 95.5
    assert percentile(values, 95) == pytest.approx(95.5)


def test_percentile_duplicates():
    assert percentile([3, 3, 3], 95) == 3.0


def test_aggregate_success_rate_and_accuracy():
    exact = ExactMatchEvaluator()
    items = [
        EvaluationItem(id="1", category="math", input="q", expected="2", actual="2"),
        EvaluationItem(id="2", category="math", input="q", expected="2", actual="3"),
    ]
    for item in items:
        exact.evaluate(item)
    report = aggregate(items)
    assert report["total"] == 2
    assert report["success_rate"] == 0.5
    assert report["accuracy"] == 0.5


def test_content_correct_but_format_invalid_separate_scores():
    # 实战题 2：内容对但 JSON 非法 → accuracy=1 而 format_rate=0
    exact = ExactMatchEvaluator()
    json_schema = JsonSchemaEvaluator()
    item = EvaluationItem(id="2", category="json", input="q", expected="ok", actual="ok")
    exact.evaluate(item)
    assert item.scores["accuracy"] == 1.0
    json_schema.evaluate(item)
    assert item.scores["format_rate"] == 0.0  # "ok" 不是 JSON


def test_token_cost_configurable():
    # 验收④：成本公式可配置（价格表传入）
    assert token_cost(1_000_000, 3.0) == 3.0
    assert token_cost(500_000, 9.0) == 4.5