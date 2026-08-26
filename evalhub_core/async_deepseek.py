"""Day 23：带重试、限流与错误分类的 DeepSeek Provider（共享 httpx.AsyncClient）。

验收映射：
- 429 / 500 / 502 / 503 → 指数退避重试（最多 max_attempts 次），尊重 Retry-After
- 401 / 403 / 400 → 不重试，立即返回 provider_error
- 超时（httpx.TimeoutException）→ 按可重试处理，重试耗尽返回 error_type="timeout"
- 统一在 LLMResponse 上记录 error_type / status_code / retry_count
"""

import asyncio
import os
import time
from typing import Optional

import httpx

from evalhub_core.deepseek import map_deepseek_response
from evalhub_core.llm_config import LLMConfig
from evalhub_core.retry_policy import RetryPolicy, parse_retry_after, should_retry
from evalhub_core.schemas import LLMRequest, LLMResponse


class RetryableDeepSeekProvider:
    """共享一个 httpx.AsyncClient 的 DeepSeek Provider，内置重试与错误分类。"""

    def __init__(
        self,
        config: LLMConfig,
        retry: Optional[RetryPolicy] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.config = config
        self.retry = retry or RetryPolicy()
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.timeout),
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        api_key = os.environ.get(self.config.api_key_env, "")
        if not api_key:
            raise RuntimeError(f"环境变量 {self.config.api_key_env} 未配置")

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
        attempts = 0

        while True:
            attempts += 1
            try:
                response = await self._client.post(
                    "/chat/completions", json=payload, headers=headers
                )
            except httpx.TimeoutException:
                if attempts >= self.retry.max_attempts:
                    return self._error_response(started, "timeout", None, attempts)
                await asyncio.sleep(self.retry.delay_for(attempts))
                continue

            status_code = response.status_code
            if status_code == 200:
                latency_ms = (time.perf_counter() - started) * 1000
                mapped = map_deepseek_response(response.json(), latency_ms=latency_ms)
                mapped.status_code = 200
                mapped.retry_count = attempts - 1
                return mapped

            if should_retry(status_code) and attempts < self.retry.max_attempts:
                retry_after = parse_retry_after(response.headers.get("Retry-After"))
                await asyncio.sleep(self.retry.delay_for(attempts, retry_after))
                continue

            return self._error_response(started, "provider_error", status_code, attempts)

    def _error_response(
        self,
        started: float,
        error_type: str,
        status_code: Optional[int],
        attempts: int,
    ) -> LLMResponse:
        latency_ms = (time.perf_counter() - started) * 1000
        return LLMResponse(
            content=None,
            latency_ms=latency_ms,
            error_type=error_type,
            token_usage=None,
            status_code=status_code,
            retry_count=attempts - 1,
        )

    async def aclose(self) -> None:
        """关闭自己创建的 AsyncClient（外部传入的 client 由外部负责关闭）。"""
        if self._owns_client:
            await self._client.aclose()
