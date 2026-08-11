import json

import pytest

from evalhub_core.loader import DatasetFormatError, load_jsonl


def test_load_valid_utf8_jsonl(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.jsonl"
    records = [
        {
            "id": "case-001",
            "input": "中国的首都是哪里？",
            "expected": "北京",
            "category": "knowledge",
        },
        {
            "id": "case-002",
            "input": "1 + 1 等于多少？",
            "expected": "2",
            "category": "math",
        },
    ]
    dataset_path.write_text(
        "\n".join(
            json.dumps(record, ensure_ascii=False)
            for record in records
        ),
        encoding="utf-8",
    )

    assert load_jsonl(str(dataset_path)) == records


def test_missing_file_has_actionable_message(tmp_path) -> None:
    missing_path = tmp_path / "missing.jsonl"

    with pytest.raises(FileNotFoundError, match="项目根目录"):
        load_jsonl(str(missing_path))


def test_invalid_json_reports_line_number(tmp_path) -> None:
    dataset_path = tmp_path / "invalid.jsonl"
    dataset_path.write_text(
        '{"id":"ok","input":"a","expected":"b","category":"test"}\n'
        '{"id":"broken"',
        encoding="utf-8",
    )

    with pytest.raises(DatasetFormatError, match="第 2 行"):
        load_jsonl(str(dataset_path))


def test_missing_field_is_rejected(tmp_path) -> None:
    dataset_path = tmp_path / "missing-field.jsonl"
    dataset_path.write_text(
        '{"id":"case-001","input":"a","expected":"b"}',
        encoding="utf-8",
    )

    with pytest.raises(DatasetFormatError, match="category"):
        load_jsonl(str(dataset_path))


def test_empty_dataset_is_rejected(tmp_path) -> None:
    dataset_path = tmp_path / "empty.jsonl"
    dataset_path.write_text("\n", encoding="utf-8")

    with pytest.raises(DatasetFormatError, match="数据集为空"):
        load_jsonl(str(dataset_path))
