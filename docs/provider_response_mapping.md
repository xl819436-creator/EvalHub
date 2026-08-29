# Provider 响应映射：DeepSeek → LLMResponse

## 目标

业务层不直接依赖 DeepSeek 的响应字段。`evalhub_core.deepseek` 负责把厂商响应转换为项目统一的 `LLMResponse`，这样后续替换 Provider 时，评分和报告代码不需要理解厂商格式。

## 字段映射

| DeepSeek 原始字段 | EvalHub 字段 | 说明 |
|---|---|---|
| `choices[0].message.content` | `LLMResponse.content` | 模型输出文本 |
| `usage.prompt_tokens` | `TokenUsage.prompt_tokens` | 输入 Token 数 |
| `usage.completion_tokens` | `TokenUsage.completion_tokens` | 输出 Token 数 |
| `usage.total_tokens` | `TokenUsage.total_tokens` | 总 Token 数 |
| 本地 `perf_counter()` 计时 | `LLMResponse.latency_ms` | 请求耗时，单位毫秒 |
| 顶层存在 `error` | `LLMResponse.error_type` | 统一为 `provider_error` |
| HTTP 状态码 | Day 23 `LLMResponse.status_code` | 由 Provider 补充 |
| 重试次数 | Day 23 `LLMResponse.retry_count` | 由带重试 Provider 补充 |

## 实现位置

- `evalhub_core/deepseek.py::map_deepseek_response`：成功/厂商错误响应映射。
- `evalhub_core/deepseek.py::extract_json_object`：解析结构化 JSON，并把非法 JSON 转为 `InvalidJSONResponse`。
- `evalhub_core/llm_provider.py::DeepSeekProvider`：同步真实 Provider。
- `evalhub_core/async_deepseek.py::RetryableDeepSeekProvider`：异步请求、重试和错误分类。
- `scripts/day21_real_call.py`：预算检查、一次真实调用、脱敏样例和成本日志。

## 错误边界

1. 顶层存在 `error` 时，不读取 `choices`，直接返回失败响应。
2. 返回内容不是合法 JSON，抛出 `InvalidJSONResponse`，调用方负责捕获。
3. 成功响应必须有非空 `content`；失败响应可以没有内容。
4. 响应缺少 `usage` 时仍可映射，但不能据此计算成本；真实调用脚本会停止记录成本并提示用户。

## 安全与成本

- API Key 只从环境变量 `DEEPSEEK_API_KEY` 读取，不写入源码、样例或日志。
- 真实响应保存前只保留 model、usage、content、finish_reason 和 latency，不保存请求头。
- 成本单价只是默认示例；运行真实调用前，应通过环境变量 `EVALHUB_INPUT_PRICE_PER_MILLION` 和 `EVALHUB_OUTPUT_PRICE_PER_MILLION` 覆盖为当前官方价格。
- `data/cost_log.jsonl` 和 `experiments/raw_response_sample.json` 属于本地运行产物，不能提交。
