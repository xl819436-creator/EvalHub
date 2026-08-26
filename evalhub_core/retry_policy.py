"""Day 23：可重试错误分类 + 指数退避重试策略（纯函数，可独立测试）。

验收映射：
- 429（限流）、500/502/503（服务端错误）→ 可重试
- 400/401/403/404/422（客户端错误）→ 不重试，立即失败
"""

import random
from dataclasses import dataclass
from typing import Optional

# 可重试：限流 + 服务端错误
RETRYABLE_STATUS = {429, 500, 502, 503}
# 不可重试：客户端错误（400/401/403/404/422 等）
NON_RETRYABLE_STATUS = {400, 401, 403, 404, 422}


def should_retry(status_code: int) -> bool:
    """该状态码是否值得重试。"""
    return status_code in RETRYABLE_STATUS


def parse_retry_after(header_value: Optional[str]) -> Optional[float]:
    """解析 Retry-After 响应头（秒数形式）；HTTP 日期形式或缺失时返回 None。"""
    if not header_value:
        return None
    value = header_value.strip()
    try:
        return float(value)
    except ValueError:
        # HTTP 日期形式（如 Wed, 21 Oct 2026 07:28:00 GMT）不处理，走默认退避
        return None


@dataclass
class RetryPolicy:
    """指数退避 + 随机抖动（+ Retry-After 优先）的重试策略。"""

    max_attempts: int = 3
    base_delay: float = 0.2
    max_delay: float = 2.0
    jitter: bool = True

    def delay_for(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """第 attempt 次重试前等待的秒数（attempt 从 1 开始）。

        Retry-After 优先；否则 base_delay * 2^(attempt-1)，封顶 max_delay，
        开启抖动时再乘以 0.5~1.5 的随机系数。
        """
        if retry_after is not None:
            return min(retry_after, self.max_delay)
        delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        if self.jitter:
            delay *= random.uniform(0.5, 1.5)
        return delay
