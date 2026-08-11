from abc import ABC, abstractmethod
from typing import List

from evalhub_core.schemas import LLMResponse


class BaseProvider(ABC):
    """所有模型Provider都必须遵守的统一接口。"""

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        """
        根据prompt生成模型响应。

        所有Provider都必须返回LLMResponse。
        """

        raise NotImplementedError


class MockProvider(BaseProvider):
    """不调用真实API，用于模拟不同模型响应。"""

    SUPPORTED_BEHAVIORS = {
        "success",
        "timeout",
        "429",
        "invalid_json",
    }

    def __init__(self, behavior: str = "success"):
        if behavior not in self.SUPPORTED_BEHAVIORS:
            raise ValueError(
                f"不支持的Mock行为：{behavior}，"
                f"可选值为：{sorted(self.SUPPORTED_BEHAVIORS)}"
            )

        self.behavior = behavior

    def generate(self, prompt: str) -> LLMResponse:
        """根据指定行为返回模拟响应。"""

        if self.behavior == "success":
            return LLMResponse(
                content=f"Mock response: {prompt}",
                latency_ms=10,
                error_type=None,
                token_usage={
                    "prompt_tokens": 8,
                    "completion_tokens": 10,
                    "total_tokens": 18,
                },
            )

        if self.behavior == "timeout":
            return LLMResponse(
                content="",
                latency_ms=3000,
                error_type="timeout",
                token_usage=None,
            )

        if self.behavior == "429":
            return LLMResponse(
                content="",
                latency_ms=100,
                error_type="rate_limit",
                token_usage=None,
            )

        # invalid_json表示：
        # 模型调用本身成功，所以error_type为None；
        # 但是模型返回的content不是合法JSON。
        return LLMResponse(
            content='{"answer": "缺少右括号"',
            latency_ms=20,
            error_type=None,
            token_usage={
                "prompt_tokens": 8,
                "completion_tokens": 10,
                "total_tokens": 18,
            },
        )


class SequenceMockProvider(BaseProvider):
    """按照预设顺序返回不同结果。"""

    def __init__(self, behaviors: List[str]):
        if not behaviors:
            raise ValueError("behaviors不能为空")

        unsupported_behaviors = [
            behavior
            for behavior in behaviors
            if behavior not in MockProvider.SUPPORTED_BEHAVIORS
        ]

        if unsupported_behaviors:
            raise ValueError(
                f"存在不支持的行为：{unsupported_behaviors}"
            )

        self.behaviors = behaviors
        self.current_index = 0

    def generate(self, prompt: str) -> LLMResponse:
        """
        按照behaviors中的顺序返回响应。

        当调用次数超过行为数量后，
        继续使用最后一个行为。
        """

        if self.current_index >= len(self.behaviors):
            behavior = self.behaviors[-1]
        else:
            behavior = self.behaviors[self.current_index]
            self.current_index += 1

        provider = MockProvider(behavior=behavior)

        return provider.generate(prompt)