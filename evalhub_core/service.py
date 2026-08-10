from evalhub_core.provider import BaseProvider
from evalhub_core.schemas import LLMRequest, LLMResponse


def execute_prompt(
    provider: BaseProvider,
    prompt: str,
) -> LLMResponse:
    """
    Day08使用的业务函数。

    该函数必须保留，否则Day08测试无法导入。
    在调用Provider之前，先使用LLMRequest校验输入。
    """

    request = LLMRequest(
        model=provider.__class__.__name__,
        input=prompt,
    )

    response = provider.generate(request.input)

    if isinstance(response, LLMResponse):
        return response

    if isinstance(response, dict):
        return LLMResponse.model_validate(response)

    raise TypeError(
        "provider.generate()必须返回LLMResponse或者dict，"
        f"但实际返回了：{type(response).__name__}"
    )


def run_generation(
    provider: BaseProvider,
    request: LLMRequest,
) -> LLMResponse:
    """
    Day09新增的模型版业务函数。

    接收已经通过Pydantic校验的LLMRequest，
    并复用Day08的execute_prompt函数。
    """

    return execute_prompt(
        provider=provider,
        prompt=request.input,
    )