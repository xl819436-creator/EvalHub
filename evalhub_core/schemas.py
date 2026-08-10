from typing import Dict, List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# 系统内部统一使用的错误类型
ErrorType = Literal[
    "timeout",
    "rate_limit",
    "invalid_json",
    "provider_error",
]


class StrictModel(BaseModel):
    """
    所有业务模型的共同父类。

    extra="forbid"表示：
    如果传入模型未定义的字段，直接校验失败。
    """

    model_config = ConfigDict(extra="forbid")


class TokenUsage(StrictModel):
    """一次大模型调用的Token使用情况。"""

    prompt_tokens: int = Field(
        ge=0,
        description="输入使用的Token数量",
    )
    completion_tokens: int = Field(
        ge=0,
        description="输出使用的Token数量",
    )
    total_tokens: int = Field(
        ge=0,
        description="总Token数量",
    )

    def __getitem__(self, key: str) -> int:
        """
        兼容Day08中的字典访问方式：

        response.token_usage["total_tokens"]
        """

        allowed_keys = {
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
        }

        if key not in allowed_keys:
            raise KeyError(key)

        return getattr(self, key)


class LLMRequest(StrictModel):
    """发送给大模型的统一请求模型。"""

    model: str = Field(
        min_length=1,
        description="模型名称",
    )
    input: str = Field(
        description="发送给模型的输入内容",
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="随机性参数，取值范围为0到2",
    )
    stop: Optional[List[str]] = Field(
        default=None,
        description="可选的停止词列表",
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="可选的附加信息",
    )

    @field_validator("input")
    @classmethod
    def input_must_not_be_blank(cls, value: str) -> str:
        """input不能是空字符串或者纯空格。"""

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("input不能为空")

        return cleaned_value


class LLMResponse(StrictModel):
    """
    大模型的统一响应模型。

    约定：
    error_type为None表示调用成功；
    error_type不为None表示调用失败。
    """

    content: Optional[str] = Field(
        default=None,
        description="模型返回的文本内容",
    )
    latency_ms: float = Field(
        ge=0,
        description="调用耗时，单位为毫秒",
    )
    error_type: Optional[ErrorType] = Field(
        default=None,
        description="失败类型；成功时为None",
    )
    token_usage: Optional[TokenUsage] = Field(
        default=None,
        description="Token使用情况",
    )

    @property
    def success(self) -> bool:
        """
        兼容Day08的response.success访问方式。

        没有error_type时，表示本次模型调用成功。
        """

        return self.error_type is None

    @model_validator(mode="after")
    def success_response_must_have_content(self) -> "LLMResponse":
        """
        成功响应必须包含非空content；
        失败响应允许content为空。
        """

        content_is_empty = (
            self.content is None
            or not self.content.strip()
        )

        if self.success and content_is_empty:
            raise ValueError("成功响应必须包含非空的content")

        return self


class TestCase(StrictModel):
    """EvalHub中的一条测试用例。"""

    case_id: str = Field(
        min_length=1,
        description="测试用例编号",
    )
    input: str = Field(
        description="发送给模型的测试输入",
    )
    expected_output: Union[str, Dict[str, object]] = Field(
        description="期望输出，可以是字符串或者字典",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="测试用例标签",
    )

    @field_validator("input")
    @classmethod
    def input_must_not_be_blank(cls, value: str) -> str:
        """测试用例的input不能为空。"""

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("测试用例的input不能为空")

        return cleaned_value