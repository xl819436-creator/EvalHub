"""Day 19：MockProvider 行为参数化 + 防误调用断言。

防误调用断言：即使完全禁止真实网络连接，
MockProvider 依然能正常返回，证明它不依赖任何外部服务。
"""

import json

import pytest

from evalhub_core.provider import MockProvider, SequenceMockProvider
from evalhub_core.schemas import LLMResponse


@pytest.mark.parametrize(
    ("behavior", "expect_success", "error_type", "has_tokens"),
    [
        ("success", True, None, True),
        ("timeout", False, "timeout", False),
        ("429", False, "rate_limit", False),
        ("invalid_json", True, None, True),
    ],
)
def test_mock_provider_behaviors(
    behavior,
    expect_success,
    error_type,
    has_tokens,
):
    provider = MockProvider(behavior)

    response = provider.generate("请输出JSON")

    assert isinstance(response, LLMResponse)
    assert response.success is expect_success
    assert response.error_type is error_type
    assert (response.token_usage is not None) is has_tokens


def test_unknown_behavior_has_readable_error():
    with pytest.raises(ValueError, match="success"):
        MockProvider("unknown_behavior")

def test_invalid_json_content_cannot_be_parsed():
    response = MockProvider("invalid_json").generate("请输出JSON")

    with pytest.raises(json.JSONDecodeError):
        json.loads(response.content)


def test_sequence_provider_falls_back_to_last_behavior():
    provider = SequenceMockProvider(["429", "success"])

    provider.generate("第一次")
    provider.generate("第二次")
    third = provider.generate("第三次")

    assert third.success is True


def test_mock_provider_works_without_network(monkeypatch):
    """防误调用断言：禁网后 MockProvider 依然正常返回。"""

    def blocked_connect(self, address, *args, **kwargs):
        raise OSError(f"禁止真实网络连接：{address}")

    monkeypatch.setattr("socket.socket.connect", blocked_connect)

    response = MockProvider("success").generate("你好")

    assert response.success is True
    assert "你好" in response.content
