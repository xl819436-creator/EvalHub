from evalhub_core.evaluator import (
    build_report,
    evaluate_record,
    exact_match,
    normalize_text,
)


def test_normalize_text_strips_edges() -> None:
    assert normalize_text("  北京  ") == "北京"


def test_exact_match_accepts_equal_values() -> None:
    assert exact_match(" 2 ", 2) is True


def test_exact_match_rejects_different_values() -> None:
    assert exact_match("北京", "上海") is False


def test_evaluate_record_preserves_identity() -> None:
    record = {
        "id": "case-001",
        "input": "1 + 1 等于多少？",
        "expected": "2",
        "category": "math",
    }

    result = evaluate_record(record, prediction="2")

    assert result["id"] == "case-001"
    assert result["matched"] is True


def test_build_report_handles_empty_results() -> None:
    report = build_report([])

    assert report["total"] == 0
    assert report["accuracy"] == 0.0


def test_build_report_counts_matches() -> None:
    report = build_report(
        [
            {"matched": True},
            {"matched": False},
            {"matched": True},
        ]
    )

    assert report["total"] == 3
    assert report["correct"] == 2
    assert report["incorrect"] == 1
    assert report["accuracy"] == 2 / 3
