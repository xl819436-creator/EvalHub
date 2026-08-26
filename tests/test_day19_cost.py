"""Day 19：成本计算的参数化测试。"""

import pytest

from evalhub_core.cost import calculate_cost

# 固定的测试价格表（不依赖真实价格，保证测试可复现）
TEST_PRICING = {"input": 1.0, "output": 2.0}


@pytest.mark.parametrize(
    ("prompt_tokens", "completion_tokens", "pricing", "expected"),
    [
        (0, 0, TEST_PRICING, 0.0),
        (1_000_000, 0, TEST_PRICING, 1.0),
        (0, 1_000_000, TEST_PRICING, 2.0),
        (1_000_000, 1_000_000, TEST_PRICING, 3.0),
        (500_000, 250_000, TEST_PRICING, 1.0),
        (8, 10, TEST_PRICING, 0.000028),
        (123_456, 7_890, {"input": 0.27, "output": 1.10}, 0.042012),
    ],
)
def test_calculate_cost(prompt_tokens, completion_tokens, pricing, expected):
    assert calculate_cost(prompt_tokens, completion_tokens, pricing) == expected


@pytest.mark.parametrize(
    ("prompt_tokens", "completion_tokens"),
    [
        (-1, 0),
        (0, -1),
        (-100, -200),
    ],
)
def test_calculate_cost_rejects_negative_tokens(prompt_tokens, completion_tokens):
    with pytest.raises(ValueError, match="token 数量不能为负数"):
        calculate_cost(prompt_tokens, completion_tokens, TEST_PRICING)


def test_calculate_cost_rejects_negative_price():
    with pytest.raises(ValueError, match="单价不能为负数"):
        calculate_cost(100, 100, {"input": -1.0, "output": 1.0})
