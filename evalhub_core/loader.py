import json
from pathlib import Path
from typing import Any


class DatasetFormatError(Exception):
    """当 JSONL 数据集格式不符合要求时抛出。"""


REQUIRED_FIELDS = ("id", "input", "expected", "category")


def load_jsonl(file_path: str) -> list[dict[str, Any]]:
    """读取并验证 EvalHub JSONL 数据集。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"数据集文件不存在：{path}\n"
            "请确认终端位于项目根目录，并检查文件路径。"
        )

    if not path.is_file():
        raise DatasetFormatError(
            f"指定的路径不是文件：{path}"
        )

    records: list[dict[str, Any]] = []

    try:
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise DatasetFormatError(
                        f"第 {line_number} 行不是合法的 JSON：{exc.msg}\n"
                        f"文件位置：{path}"
                    ) from exc

                if not isinstance(record, dict):
                    raise DatasetFormatError(
                        f"第 {line_number} 行必须是 JSON 对象，"
                        f"当前类型为：{type(record).__name__}"
                    )

                for field_name in REQUIRED_FIELDS:
                    if field_name not in record:
                        raise DatasetFormatError(
                            f"第 {line_number} 行缺少 {field_name} 字段。"
                        )

                if not isinstance(record["id"], str):
                    raise DatasetFormatError(
                        f"第 {line_number} 行的 id 必须是字符串。"
                    )

                if not isinstance(record["input"], str):
                    raise DatasetFormatError(
                        f"第 {line_number} 行的 input 必须是字符串。"
                    )

                if not isinstance(record["expected"], str):
                    raise DatasetFormatError(
                        f"第 {line_number} 行的 expected 必须是字符串。"
                    )

                if not isinstance(record["category"], str):
                    raise DatasetFormatError(
                        f"第 {line_number} 行的 category 必须是字符串。"
                    )

                records.append(record)

    except UnicodeDecodeError as exc:
        raise DatasetFormatError(
            f"数据集不是有效的 UTF-8 编码：{path}"
        ) from exc

    if not records:
        raise DatasetFormatError(
            f"数据集为空：{path}"
        )

    return records