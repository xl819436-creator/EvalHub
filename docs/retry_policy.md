# 重试策略（Day 23）

## 决策：手写重试 vs Tenacity 库

对照 <https://tenacity.readthedocs.io/> 的 stop / wait / retry 三要素：

| 维度 | Tenacity | 本项目选择 | 理由 |
|---|---|---|---|
| 停止条件 | `stop_after_attempt` | `RetryPolicy.max_attempts` | 语义一致，手写更直观 |
| 等待策略 | `wait_exponential + jitter` | `RetryPolicy.delay_for`（指数退避 + 随机抖动） | 同样实现了退避+抖动 |
| 重试条件 | `retry_if_exception` / 自定义 | `should_retry(status_code)` | 我们是"按 HTTP 状态码"而非"按异常"重试 |
| Retry-After | 需自定义 | `parse_retry_after` + 优先等待 | 官方 API 的 429 响应会带 Retry-After，尊重它最稳 |

**结论**：当前只有"按状态码重试"一种需求，手写一个 `RetryPolicy`（纯函数、可单测）比引入 Tenacity 依赖更简单、更贴合 EvalHub 的"可测试、不虚构"原则；将来若出现多种复杂重试策略，再换 Tenacity 也不迟。

## 策略定义

- **可重试**：`429`（限流）、`500 / 502 / 503`（服务端错误）
- **不重试**：`400 / 401 / 403 / 404 / 422`（客户端错误，重试无意义）
- **超时**（`httpx.TimeoutException`）：按可重试处理，重试耗尽返回 `error_type="timeout"`
- **退避**：`base_delay * 2^(attempt-1)`，封顶 `max_delay`，开启抖动时乘 0.5~1.5 随机系数；若响应带 `Retry-After` 则优先按它等待（封顶 max_delay）
- **记录**：统一在 `LLMResponse` 上记录 `error_type` / `status_code` / `retry_count`

## 测试覆盖（tests/test_day23_retry.py，httpx.MockTransport 零真实网络）

- `429 → 429 → 200`：总调用 3 次，最终成功，`retry_count == 2`
- `500 → 200`：总调用 2 次，最终成功，`retry_count == 1`
- `401`：只调用 1 次，立即返回 `provider_error`，`status_code == 401`，`retry_count == 0`
- `should_retry` 分类正确（429/5xx 为 True，4xx 为 False）
- 并发 10 个任务时最大活动请求不超过 `Semaphore(3)` 配置值

## 关键文件

- `evalhub_core/retry_policy.py`：RetryPolicy / should_retry / parse_retry_after（纯函数）
- `evalhub_core/async_deepseek.py`：RetryableDeepSeekProvider（共享 httpx.AsyncClient + 重试 + 错误分类）
- `evalhub_core/schemas.py`：LLMResponse 新增 `status_code`、`retry_count` 字段
- `tests/test_day23_retry.py`：5 个用例
