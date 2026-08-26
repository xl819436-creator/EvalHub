"""Day 21：厂商响应映射的离线测试（伪造 payload，零真实调用）。"""

import pytest

from evalhub_core.deepseek import (
    InvalidJSONResponse,
    extract_json_object,
    map_deepseek_response,
)
from evalhub_core.schemas import LLMResponse


def make_success_payload(content='{"answer": 42}', **overrides):
    payload = {
        "id": "chatcmpl-xxx",
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 20,
            "total_tokens": 32,
        },
    }
    payload.update(overrides)
    return payload


def test_success_payload_maps_to_llm_response():
    response = map_deepseek_response(make_success_payload(), latency_ms=123.4)

    assert isinstance(response, LLMResponse)
    assert response.success is True
    assert response.error_type is None
    assert response.latency_ms == 123.4
    assert response.token_usage.total_tokens == 32
    assert response.token_usage.prompt_tokens == 12


def test_missing_usage_keeps_token_usage_none():
    payload = make_success_payload()
    del payload["usage"]

    response = map_deepseek_response(payload, latency_ms=10.0)

    assert response.success is True
    assert response.token_usage is None


def test_error_payload_maps_to_provider_error():
    payload = {
        "error": {"message": "Insufficient Balance", "type": "invalid_request_error"}
    }

    response = map_deepseek_response(payload, latency_ms=50.0)

    assert response.success is False
    assert response.error_type == "provider_error"


def test_extract_json_object_parses_valid_content():
    assert extract_json_object('{"answer": 42}') == {"answer": 42}


def test_extract_json_object_rejects_invalid_json():
    with pytest.raises(InvalidJSONResponse, match="不是合法 JSON"):
        extract_json_object('{"answer": 42')


def test_extract_json_object_rejects_non_object():
    with pytest.raises(InvalidJSONResponse, match="不是对象"):
        extract_json_object("[1, 2, 3]")
