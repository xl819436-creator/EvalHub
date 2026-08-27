"""Day 24：评测数据集版本、校验与可复现性。

统一字段：id / category / input / expected / evaluator_names / metadata
- Schema 校验：pydantic，错误能定位到样本 ID 与字段路径
- 规范化哈希：JSON 键排序后计算 SHA-256，同内容同哈希
- 运行快照：dataset_hash / git_commit / provider config / seed / start_time
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

# 数据集 Schema 版本号
SCHEMA_VERSION = "1.0"


class DatasetRecord(BaseModel):
    """评测数据集的一行记录（统一字段）。"""

    id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    input: str = Field(min_length=1)
    expected: str
    evaluator_names: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("input")
    @classmethod
    def input_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("input 不能为空")
        return value


def normalize_record(record: dict[str, Any]) -> str:
    """规范化 JSON：键排序 + 紧凑分隔符，保证同内容同字符串（键顺序无关）。"""
    return json.dumps(
        record,
        sort_keys=True,      # 键按字母排序 → 键顺序变化不影响结果
        ensure_ascii=False,  # 保留中文，可读
        separators=(",", ":"),
    )


def record_hash(record: dict[str, Any]) -> str:
    """单条记录的 SHA-256。"""
    return hashlib.sha256(normalize_record(record).encode("utf-8")).hexdigest()


def dataset_hash(records: list[dict[str, Any]]) -> str:
    """整份数据集的 SHA-256：所有记录规范化后拼接再哈希。"""
    payload = "\n".join(normalize_record(record) for record in records)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_dataset(records: list[dict[str, Any]]) -> list[str]:
    """校验数据集，返回可读错误列表（带样本 ID 与字段路径）。"""
    errors: list[str] = []
    for index, record in enumerate(records, start=1):
        record_id = record.get("id", f"<第{index}行>")
        try:
            DatasetRecord.model_validate(record)
        except ValidationError as exc:
            for error in exc.errors():
                field_path = ".".join(str(part) for part in error["loc"])
                errors.append(
                    f"record #{index} (id={record_id})："
                    f"字段 [{field_path}] 校验失败：{error['msg']}"
                )
    return errors


def load_dataset(file_path: str) -> list[dict[str, Any]]:
    """读取 JSONL 数据集并返回记录列表（Schema 校验交给 validate_dataset）。"""
    from evalhub_core.loader import load_jsonl

    return load_jsonl(file_path)


def git_commit_sha() -> str:
    """当前仓库 HEAD 的 commit SHA；非 git 仓库时返回 unknown。"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def build_run_manifest(
    records: list[dict[str, Any]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    seed: int = 42,
    start_time: Optional[str] = None,
) -> dict[str, Any]:
    """运行参数快照：dataset_hash、git_commit、provider config、seed、开始时间。"""
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_hash": dataset_hash(records),
        "git_commit": git_commit_sha(),
        "provider": provider,
        "model": model,
        "seed": seed,
        "start_time": start_time or datetime.now().isoformat(timespec="seconds"),
    }
