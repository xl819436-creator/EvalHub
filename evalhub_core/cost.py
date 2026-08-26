"""模型调用成本计算（Day 19 起提供，Day 21/25 复用）。

约定：
- 价格为“每百万 token”的美元单价；
- calculate_cost 只做纯计算，价格由调用方传入，便于参数化测试；
- 价格数据请以厂商官方定价页为准，DEFAULT_PRICING 只是示例。
"""

from typing import Mapping

# 示例价格表：请以 DeepSeek 官方定价页为准，随时更新。
DEFAULT_PRICING: Mapping[str, Mapping[str, float]] = {
    "deepseek-chat": {"input": 0.27, "output": 1.10},
}


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    pricing: Mapping[str, float],
) -> float:
    """按百万 token 单价计算一次调用的美元成本。

    参数:
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数
        pricing: 必须包含 "input" 和 "output" 两个单价（美元/百万 token）

    返回:
        四舍五入到 6 位小数的美元成本
    """

    if prompt_tokens < 0 or completion_tokens < 0:
        raise ValueError("token 数量不能为负数")

    input_price = pricing.get("input", 0.0)
    output_price = pricing.get("output", 0.0)

    if input_price < 0 or output_price < 0:
        raise ValueError("单价不能为负数")

    input_cost = prompt_tokens / 1_000_000 * input_price
    output_cost = completion_tokens / 1_000_000 * output_price

    return round(input_cost + output_cost, 6)
