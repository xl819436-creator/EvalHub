"""Day 22：Provider 抽象、工厂与配置驱动切换的测试（零真实调用）。"""

import os

import pytest

from evalhub_core.llm_config import LLMConfig
from evalhub_core.llm_provider import (
    DeepSeekProvider,
    DummyProvider,
    MockLLMProvider,
    ProviderFactory,
)
from evalhub_core.schemas import LLMRequest, LLMResponse


def make_request(text: str = "你好") -> LLMRequest:
    return LLMRequest(model="deepseek-chat", input=text)


def test_factory_creates_mock_provider():
    config = LLMConfig(provider="mock", behavior="success")

    provider = ProviderFactory.create(config)

    assert isinstance(provider, MockLLMProvider)


def test_factory_creates_deepseek_provider_without_calling():
    # 创建实例不联网、不读 key；只有 generate 才需要 key
    config = LLMConfig(provider="deepseek")

    provider = ProviderFactory.create(config)

    assert isinstance(provider, DeepSeekProvider)


def test_factory_rejects_unknown_provider_with_readable_error():
    config = LLMConfig(provider="not-exist")

    with pytest.raises(ValueError, match="未知 provider"):
        ProviderFactory.create(config)


@pytest.mark.parametrize(
    ("behavior", "expect_success", "error_type"),
    [
        ("success", True, None),
        ("timeout", False, "timeout"),
        ("429", False, "rate_limit"),
        ("invalid_json", True, None),
    ],
)
def test_mock_provider_returns_llm_response(behavior, expect_success, error_type):
    config = LLMConfig(provider="mock", behavior=behavior)

    provider = ProviderFactory.create(config)
    response = provider.generate(make_request())

    assert isinstance(response, LLMResponse)
    assert response.success is expect_success
    assert response.error_type is error_type


def test_dummy_provider_registered_and_usable():
    # 实战题 1：DummyProvider 注册后，只改配置 provider="dummy" 即可用
    config = LLMConfig(provider="dummy")

    provider = ProviderFactory.create(config)
    response = provider.generate(make_request("测试"))

    assert isinstance(provider, DummyProvider)
    assert response.success is True
    assert "测试" in response.content


def test_deepseek_provider_requires_api_key(monkeypatch):
    # 未配置 key 时，真实 Provider 必须给出明确错误（不静默、不联网）
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    config = LLMConfig(provider="deepseek")

    provider = ProviderFactory.create(config)

    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        provider.generate(make_request())
