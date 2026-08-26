"""Day 19：评分器的参数化测试（同一函数多组输入，边界+正常+异常）。"""

import pytest

from evalhub_core.evaluator import (
    build_report,
    evaluate_record,
    exact_match,
    normalize_text,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("北京", "北京"),
        ("  北京  ", "北京"),
        ("\t上海\n", "上海"),
        ("", ""),
        ("   ", ""),
        (123, "123"),
        (None, "None"),
        (3.14, "3.14"),
    ],
)
def test_normalize_text(value, expected):
    assert normalize_text(value) == expected


@pytest.mark.parametrize(
    ("prediction", "expected", "matched"),
    [
        # 12 组 exact_match 输入（对应实战题 2：同一评分器 12 组参数化）
        ("北京", "北京", True),
        (" 北京 ", "北京", True),
        ("北京", "上海", False),
        ("2", 2, True),
        ("2.0", "2", False),
        ("", "", True),
        (" ", "", True),
        (None, "None", True),
        ("None", "none", False),
        ("你好世界", "你好 世界", False),
        ("A", "a", False),
        ("  A  ", "A", True),
    ],
)
def test_exact_match_parametrized(prediction, expected, matched):
    assert exact_match(prediction, expected) is matched


@pytest.mark.parametrize(
    ("prediction", "matched"),
    [
        ("2", True),
        ("3", False),
        (" 2 ", True),
    ],
)
def test_evaluate_record_matches(prediction, matched):
    record = {
        "id": "case-001",
        "input": "1 + 1 等于多少？",
        "expected": "2",
        "category": "math",
    }

    result = evaluate_record(record, prediction)

    assert result["matched"] is matched
    assert result["category"] == "math"


@pytest.mark.parametrize(
    ("matches", "expected_correct"),
    [
        ([], 0),
        ([True], 1),
        ([True, False], 1),
        ([True, False, True, True], 3),
    ],
)
def test_build_report_counts(matches, expected_correct):
    results = [{"matched": matched} for matched in matches]

    report = build_report(results)

    assert report["correct"] == expected_correct
    assert report["total"] == len(matches)
