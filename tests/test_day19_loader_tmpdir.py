"""Day 19：JSONL loader 的临时目录隔离测试（每个测试独立 tmp_path）。"""

import json

import pytest

from evalhub_core.loader import DatasetFormatError, load_jsonl


def write_dataset(tmp_path, lines):
    """在 pytest 的临时目录中写入一个 JSONL 文件并返回路径。"""
    path = tmp_path / "dataset.jsonl"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("records", "expected_count"),
    [
        (
            [{"id": "c1", "input": "a", "expected": "b", "category": "t"}],
            1,
        ),
        (
            [
                {"id": "c1", "input": "a", "expected": "b", "category": "t"},
                {"id": "c2", "input": "x", "expected": "y", "category": "t"},
            ],
            2,
        ),
    ],
)
def test_loads_valid_datasets(tmp_path, records, expected_count):
    lines = [json.dumps(record, ensure_ascii=False) for record in records]

    path = write_dataset(tmp_path, lines)

    assert len(load_jsonl(str(path))) == expected_count


def test_blank_lines_are_skipped(tmp_path):
    path = write_dataset(
        tmp_path,
        [
            "",
            '{"id":"c1","input":"a","expected":"b","category":"t"}',
            "",
        ],
    )

    assert len(load_jsonl(str(path))) == 1


def test_non_object_line_is_rejected(tmp_path):
    path = write_dataset(tmp_path, ["[1, 2, 3]"])

    with pytest.raises(DatasetFormatError, match="必须是 JSON 对象"):
        load_jsonl(str(path))


@pytest.mark.parametrize(
    ("bad_record", "field_name"),
    [
        ({"id": 1, "input": "a", "expected": "b", "category": "t"}, "id"),
        ({"id": "c1", "input": 1, "expected": "b", "category": "t"}, "input"),
        ({"id": "c1", "input": "a", "expected": 1, "category": "t"}, "expected"),
        ({"id": "c1", "input": "a", "expected": "b", "category": 1}, "category"),
    ],
)
def test_wrong_field_type_is_rejected(tmp_path, bad_record, field_name):
    path = write_dataset(
        tmp_path,
        [json.dumps(bad_record, ensure_ascii=False)],
    )

    with pytest.raises(DatasetFormatError, match=field_name):
        load_jsonl(str(path))


def test_directory_path_is_rejected(tmp_path):
    with pytest.raises(DatasetFormatError, match="不是文件"):
        load_jsonl(str(tmp_path))
