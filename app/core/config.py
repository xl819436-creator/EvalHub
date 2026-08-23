"""集中配置：应用级参数统一在这里，禁止散落在各模块。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "EvalHub API"
    app_version: str = "0.1.0"
    log_level: str = "INFO"


settings = Settings()