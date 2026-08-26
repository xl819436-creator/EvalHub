"""Day 23：重试与错误分类测试（httpx.MockTransport，零真实网络、不真实 sleep 太久）。

覆盖验收：
- 429 → 429 → 200：重试后成功（总调用 3 次）
- 500 → 200：重试后成功（总调用 2 次）
- 401：不重试（只调用 1 次）
- retry_count 正确；should_retry 分类正确
- 实战题 3：并发 10 个任务时最大活动请求不超过 3
"""

import asyncio

import httpx
import pytest

from evalhub_core.async_deepseek import RetryableDeepSeekProvider
from evalhub_core.llm_config import LLMConfig
from evalhub_core.retry_policy import RetryPolicy, should_retry
from evalhub_core.schemas import LLMRequest


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch):
    """所有重试用例都走 MockTransport，只需一个假 key 通过 generate 的前置检查。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


def make_success_json():
    return {
        "id": "chatcmpl-test",
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": '{"answer": 42}'},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


def make_provider(handler, retry=None):
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://api.deepseek.com")
    config = LLMConfig(provider="deepseek")
    return RetryableDeepSeekProvider(config, retry=retry, client=client)


def fast_retry():
    """测试专用：把退避时间压到几乎为 0，避免真实 sleep 太久。"""
    return RetryPolicy(max_attempts=3, base_delay=0.001, jitter=False)


@pytest.mark.asyncio
async def test_429_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json=make_success_json())

    provider = make_provider(handler, retry=fast_retry())
    response = await provider.generate(LLMRequest(model="m", input="hi"))

    assert calls["n"] == 3  # 实战题 1：429 场景总调用 3 次
    assert response.success is True
    assert response.status_code == 200
    assert response.retry_count == 2


@pytest.mark.asyncio
async def test_500_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(500, json={"error": {"message": "boom"}})
        return httpx.Response(200, json=make_success_json())

    provider = make_provider(handler, retry=fast_retry())
    response = await provider.generate(LLMRequest(model="m", input="hi"))

    assert calls["n"] == 2
    assert response.success is True
    assert response.retry_count == 1


@pytest.mark.asyncio
async def test_401_never_retries():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(401, json={"error": {"message": "unauthorized"}})

    provider = make_provider(handler, retry=fast_retry())
    response = await provider.generate(LLMRequest(model="m", input="hi"))

    assert calls["n"] == 1  # 实战题 2：401 只调用 1 次
    assert response.success is False
    assert response.error_type == "provider_error"
    assert response.status_code == 401
    assert response.retry_count == 0


def test_should_retry_classification():
    for code in (429, 500, 502, 503):
        assert should_retry(code) is True
    for code in (200, 400, 401, 403, 404, 422):
        assert should_retry(code) is False


@pytest.mark.asyncio
async def test_concurrency_limited_to_semaphore():
    # 实战题 3：并发 10 个任务时，最大活动请求不超过配置值（这里演示 Semaphore(3)）
    active = {"now": 0, "max": 0}
    lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(3)

    def handler(request):
        return httpx.Response(200, json=make_success_json())

    provider = make_provider(handler, retry=RetryPolicy(max_attempts=1))

    async def one(i):
        async with semaphore:
            async with lock:
                active["now"] += 1
                active["max"] = max(active["max"], active["now"])
            try:
                await provider.generate(LLMRequest(model="m", input=str(i)))
            finally:
                async with lock:
                    active["now"] -= 1

    await asyncio.gather(*[one(i) for i in range(10)])

    assert active["max"] <= 3
