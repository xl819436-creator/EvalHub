import pytest
from pydantic import ValidationError

from evalhub_core.schemas import (
    LLMRequest,
    LLMResponse,
    TestCase as EvalTestCase,
)


INVALID_CASES = [
    (
        LLMRequest,
        {
            "model": "mock-model",
            "input": "你好",
            "temperature": 3,
        },
    ),
    (
        LLMRequest,
        {
            "model": "mock-model",
            "input": "",
            "temperature": 0.7,
        },
    ),
    (
        LLMRequest,
        {
            "model": "mock-model",
            "temperature": 0.7,
        },
    ),
    (
        LLMResponse,
        {
            "content": None,
            "latency_ms": 10,
            "error_type": "network_down",
        },
    ),
    (
        LLMResponse,
        {
            "content": "模型回答成功",
            "latency_ms": 10,
            "token_usage": {
                "prompt_tokens": -1,
                "completion_tokens": 10,
                "total_tokens": 9,
            },
        },
    ),
    (
        LLMResponse,
        {
            "content": "",
            "latency_ms": 10,
            "error_type": None,
        },
    ),
]


@pytest.mark.parametrize(
    "model_class, invalid_data",
    INVALID_CASES,
)
def test_invalid_data_is_rejected(
    model_class,
    invalid_data,
) -> None:
    """6个错误输入都必须触发ValidationError。"""

    with pytest.raises(ValidationError):
        model_class.model_validate(invalid_data)


def test_valid_request_can_be_created() -> None:
    request = LLMRequest(
        model="mock-model",
        input="请介绍Python",
        temperature=0.7,
        stop=["结束"],
        metadata={"source": "day09"},
    )

    assert request.input == "请介绍Python"
    assert request.temperature == 0.7


def test_success_response_must_have_content() -> None:
    response = LLMResponse(
        content="模型回答成功",
        latency_ms=12.5,
        error_type=None,
        token_usage={
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    )

    assert response.content == "模型回答成功"
    assert response.token_usage is not None
    assert response.token_usage.total_tokens == 30


def test_failed_response_can_have_empty_content() -> None:
    response = LLMResponse(
        content=None,
        latency_ms=3000,
        error_type="timeout",
        token_usage=None,
    )

    assert response.content is None
    assert response.error_type == "timeout"


def test_valid_test_case_can_be_created() -> None:
    test_case = EvalTestCase(
        case_id="case-001",
        input="1加1等于多少？",
        expected_output="2",
        tags=["math", "exact-match"],
    )

    assert test_case.case_id == "case-001"
    assert test_case.tags == ["math", "exact-match"]