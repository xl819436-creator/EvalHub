import argparse
import sys

from evalhub_core.evaluator import build_report, evaluate_record
from evalhub_core.loader import DatasetFormatError, load_jsonl


DEFAULT_DATASET_PATH = "data/eval_dataset.jsonl"


def build_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        description="EvalHub Exact Match 命令行评测工具"
    )

    parser.add_argument(
        "dataset",
        nargs="?",
        default=DEFAULT_DATASET_PATH,
        help=(
            "JSONL 数据集路径，"
            "默认使用 data/eval_dataset.jsonl"
        ),
    )

    return parser


def collect_predictions(
    records: list[dict],
) -> list[dict]:
    """逐题显示问题，并接收预测答案。"""

    results: list[dict] = []

    print()
    print("开始 Exact Match 评测")
    print("请根据题目输入预测答案。")
    print("-" * 50)

    for index, record in enumerate(records, start=1):
        print()
        print(f"题目 {index}/{len(records)}")
        print(f"编号：{record['id']}")
        print(f"类别：{record['category']}")
        print(f"问题：{record['input']}")

        prediction = input("预测答案：")

        result = evaluate_record(
            record=record,
            prediction=prediction,
        )

        results.append(result)

        if result["matched"]:
            print("本题结果：正确")
        else:
            print("本题结果：错误")
            print(f"标准答案：{result['expected']}")

    return results


def print_report(report: dict) -> None:
    """在终端中显示评测汇总结果。"""

    print()
    print("=" * 50)
    print("EvalHub 评测完成")
    print(f"样本总数：{report['total']}")
    print(f"正确数量：{report['correct']}")
    print(f"错误数量：{report['incorrect']}")
    print(f"准确率：{report['accuracy']:.2%}")
    print("=" * 50)


def main() -> int:
    """运行命令行评测程序。"""

    parser = build_parser()
    args = parser.parse_args()

    try:
        records = load_jsonl(args.dataset)
    except (FileNotFoundError, DatasetFormatError) as exc:
        print(
            f"评测执行失败：\n{exc}",
            file=sys.stderr,
        )
        return 1

    print(f"成功读取数据集：{args.dataset}")
    print(f"共读取 {len(records)} 条测试数据。")

    results = collect_predictions(records)
    report = build_report(results)
    print_report(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())