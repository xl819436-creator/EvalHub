import json

from evalhub_core.provider import (
    BaseProvider,
    LLMResponse,
    MockProvider,
    SequenceMockProvider,
)
from evalhub_core.service import execute_prompt


def test_success_behavior():
    provider = MockProvider("success")

    response = provider.generate("你好")

    assert isinstance(response, LLMResponse)
    assert response.success is True
    assert response.error_type is None
    assert "你好" in response.content
    assert response.token_usage["total_tokens"] == 18


def test_timeout_behavior():
    provider = MockProvider("timeout")

    response = provider.generate("你好")

    assert response.success is False
    assert response.error_type == "timeout"
    assert response.content == ""


def test_429_behavior():
    provider = MockProvider("429")

    response = provider.generate("你好")

    assert response.success is False
    assert response.error_type == "rate_limit"


def test_invalid_json_behavior():
    provider = MockProvider("invalid_json")

    response = provider.generate("请返回JSON")

    assert response.success is True
    assert response.error_type is None

    try:
        json.loads(response.content)
        is_valid_json = True
    except json.JSONDecodeError:
        is_valid_json = False

    assert is_valid_json is False


def test_business_function_depends_on_base_provider():
    provider: BaseProvider = MockProvider("success")

    response = execute_prompt(
        provider=provider,
        prompt="介绍一下EvalHub",
    )

    assert response.success is True
    assert "EvalHub" in response.content


def test_sequence_mock_provider():
    provider = SequenceMockProvider(
        behaviors=["429", "success"]
    )

    first_response = provider.generate("第一次调用")
    second_response = provider.generate("第二次调用")

    assert first_response.error_type == "rate_limit"
    assert second_response.success is True
    assert second_response.error_type is None