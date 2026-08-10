from typing import Any


def normalize_text(value: Any) -> str:
    """将答案转换为字符串，并删除两侧多余空格。"""

    return str(value).strip()


def exact_match(prediction: Any, expected: Any) -> bool:
    """判断预测答案与标准答案是否完全一致。"""

    normalized_prediction = normalize_text(prediction)
    normalized_expected = normalize_text(expected)

    return normalized_prediction == normalized_expected


def evaluate_record(
    record: dict[str, Any],
    prediction: Any,
) -> dict[str, Any]:
    """评测一条测试数据。"""

    expected = record["expected"]
    matched = exact_match(prediction, expected)

    return {
        "id": record["id"],
        "input": record["input"],
        "category": record["category"],
        "prediction": normalize_text(prediction),
        "expected": normalize_text(expected),
        "matched": matched,
    }


def build_report(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """根据全部单条评测结果生成汇总报告。"""

    total = len(results)
    correct = sum(
        1 for result in results if result["matched"]
    )
    incorrect = total - correct
    accuracy = correct / total if total else 0.0

    return {
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "accuracy": accuracy,
        "results": results,
    }