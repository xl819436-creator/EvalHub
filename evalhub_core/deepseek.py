"""DeepSeek 厂商响应 → 统一 LLMResponse 的映射（Day 21）。"""

import json

from evalhub_core.schemas import LLMResponse, TokenUsage


class InvalidJSONResponse(Exception):
    """模型返回的内容不是合法 JSON 对象。"""


def map_deepseek_response(payload: dict, latency_ms: float) -> LLMResponse:
    """把 DeepSeek chat completions 原始响应映射为统一 LLMResponse。

    payload 两种形态：
    - 成功：{"choices": [{"message": {"content": "..."}}], "usage": {...}}
    - 失败：{"error": {"message": "...", "type": "..."}}
    """
    if "error" in payload:
        return LLMResponse(
            content=None,
            latency_ms=latency_ms,
            error_type="provider_error",
            token_usage=None,
        )

    content = payload["choices"][0]["message"]["content"]

    token_usage = None
    usage = payload.get("usage")
    if usage:
        token_usage = TokenUsage(
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
        )

    return LLMResponse(
        content=content,
        latency_ms=latency_ms,
        error_type=None,
        token_usage=token_usage,
    )


def extract_json_object(content: str) -> dict:
    """从模型输出中提取 JSON 对象；失败时抛出结构化错误。"""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise InvalidJSONResponse(f"模型返回的内容不是合法 JSON：{exc.msg}") from exc

    if not isinstance(data, dict):
        raise InvalidJSONResponse("模型返回的 JSON 不是对象")

    return data
