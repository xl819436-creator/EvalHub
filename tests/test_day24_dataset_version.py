"""Day 24：数据集版本、校验与可复现性测试。"""

import json

from evalhub_core.dataset_version import (
    SCHEMA_VERSION,
    build_run_manifest,
    dataset_hash,
    normalize_record,
    validate_dataset,
)


def make_records():
    return [
        {
            "id": "case-001",
            "category": "knowledge",
            "input": "中国的首都是哪里？",
            "expected": "北京",
            "evaluator_names": ["exact_match"],
            "metadata": {"source": "sample"},
        },
        {
            "id": "case-002",
            "category": "math",
            "input": "1+1等于多少？",
            "expected": "2",
            "evaluator_names": ["exact_match"],
            "metadata": {},
        },
    ]


def test_normalize_ignores_key_order():
    # 实战题 1：仅调整 JSON 键顺序，规范化结果一致
    a = {"id": "x", "input": "hi", "expected": "ok", "category": "t"}
    b = {"expected": "ok", "category": "t", "id": "x", "input": "hi"}
    assert normalize_record(a) == normalize_record(b)


def test_dataset_hash_ignores_key_order():
    # 实战题 1：键顺序变化，数据集哈希保持一致
    records_a = make_records()
    records_b = [
        {k: v for k, v in sorted(record.items(), key=lambda item: item[0])}
        for record in records_a
    ]
    assert dataset_hash(records_a) == dataset_hash(records_b)


def test_dataset_hash_changes_when_expected_changes():
    # 实战题 2：修改 expected，哈希必须变化
    records = make_records()
    original = dataset_hash(records)
    records[1]["expected"] = "2.0"
    assert dataset_hash(records) != original


def test_same_content_same_hash():
    records = make_records()
    assert dataset_hash(records) == dataset_hash(json.loads(json.dumps(records)))


def test_validate_reports_id_and_field_path():
    bad = [
        {"id": "case-001", "category": "knowledge", "input": "q", "expected": "a"},
        {"id": "case-002", "category": "math", "input": "", "expected": "2"},
        {"id": "case-003", "category": "math", "input": "q"},
    ]
    errors = validate_dataset(bad)

    assert len(errors) == 2
    assert any("case-002" in error and "[input]" in error for error in errors)
    assert any("case-003" in error and "[expected]" in error for error in errors)


def test_run_manifest_snapshots_parameters():
    records = make_records()

    manifest = build_run_manifest(
        records,
        provider="deepseek",
        model="deepseek-chat",
        seed=42,
        start_time="2026-08-24T10:00:00",
    )

    assert manifest["dataset_hash"] == dataset_hash(records)
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["provider"] == "deepseek"
    assert manifest["model"] == "deepseek-chat"
    assert manifest["seed"] == 42
    assert manifest["start_time"] == "2026-08-24T10:00:00"
    assert isinstance(manifest["git_commit"], str) and manifest["git_commit"]


def test_fixed_seed_reproducible():
    # 实战题 3：同数据同配置（固定 seed），随机序列可复现
    import random

    random.seed(42)
    first = [random.random() for _ in range(5)]

    random.seed(42)
    second = [random.random() for _ in range(5)]

    assert first == second
