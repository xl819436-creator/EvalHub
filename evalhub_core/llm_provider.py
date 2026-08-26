"""Day 22：统一 LLM Provider 抽象 + ProviderFactory。

设计（对应实战题 3 的依赖图）：
- BaseLLMProvider 是所有 Provider 的统一接口（依赖倒置：业务层只依赖这个抽象）
- DeepSeekProvider 真实调用 DeepSeek（复用 Day 21 的响应映射）
- MockLLMProvider 不联网，响应模型与真实完全一致（都返回 LLMResponse）
- ProviderFactory 用注册表 + 配置创建实例；新增 Provider 只改注册表和配置
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Type

import httpx

from evalhub_core.deepseek import map_deepseek_response
from evalhub_core.llm_config import LLMConfig
from evalhub_core.schemas import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    """所有模型 Provider 的统一接口（业务层只依赖它，不依赖任何厂商 SDK）。"""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """根据请求生成响应；所有 Provider 都必须返回 LLMResponse。"""
        raise NotImplementedError


class DeepSeekProvider(BaseLLMProvider):
    """真实调用 DeepSeek API 的 Provider（复用 Day 21 的 map_deepseek_response）。"""

    def generate(self, request: LLMRequest) -> LLMResponse:
        api_key = os.environ.get(self.config.api_key_env, "")
        if not api_key:
            raise RuntimeError(
                f"环境变量 {self.config.api_key_env} 未配置，无法调用 DeepSeek"
            )

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "你是评测数据助手，只输出 JSON 对象。"},
                {"role": "user", "content": request.input},
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": request.temperature,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        started = time.perf_counter()
        with httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        ) as client:
            response = client.post("/chat/completions", json=payload, headers=headers)
        latency_ms = (time.perf_counter() - started) * 1000

        return map_deepseek_response(response.json(), latency_ms=latency_ms)


class MockLLMProvider(BaseLLMProvider):
    """不联网的 Mock Provider：success / timeout / 429 / invalid_json。

    响应模型与 DeepSeekProvider 完全一致（都返回 LLMResponse），
    只是不发起真实网络请求——这就是"Mock 与真实响应同模型"。
    """

    def generate(self, request: LLMRequest) -> LLMResponse:
        from evalhub_core.provider import MockProvider

        return MockProvider(behavior=self.config.behavior).generate(request.input)


class DummyProvider(BaseLLMProvider):
    """实战题 1：新增 Provider 只改注册表和配置即可使用，业务层零改动。"""

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=f"dummy: {request.input}",
            latency_ms=1.0,
            error_type=None,
            token_usage=None,
        )


class ProviderFactory:
    """按配置创建 Provider 实例；注册表驱动，未知 provider 给出可读错误。"""

    _registry: Dict[str, Type[BaseLLMProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseLLMProvider]) -> None:
        cls._registry[name] = provider_cls

    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLMProvider:
        provider_cls = cls._registry.get(config.provider)
        if provider_cls is None:
            raise ValueError(
                f"未知 provider：{config.provider}，可用选项：{sorted(cls._registry)}"
            )
        return provider_cls(config)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)


# 内置注册：新增 Provider 就在这里加一行
ProviderFactory.register("deepseek", DeepSeekProvider)
ProviderFactory.register("mock", MockLLMProvider)
ProviderFactory.register("dummy", DummyProvider)
