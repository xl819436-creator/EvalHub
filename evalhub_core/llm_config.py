"""LLM Provider 配置（Day 22）。

配置只包含 provider / model / base_url / timeout；
密钥不直接写进配置，而是用环境变量名引用（api_key_env）。
"""

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Provider 配置：新增 Provider 时通常只需新增 provider 类型，无需改业务层。"""

    provider: str = Field(description="provider 类型：deepseek / mock / dummy")
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"
    timeout: float = 30.0
    api_key_env: str = "DEEPSEEK_API_KEY"
    temperature: float = 0.7
    max_tokens: int = 512
    # 仅 mock provider 使用：success / timeout / 429 / invalid_json
    behavior: str = "success"
