"""Day 24：validate_dataset CLI——校验 JSONL 数据集并输出可定位错误。

用法（在项目根目录）：
    D:\Annaconda\envs\evalhub-py311\python.exe scripts\validate_dataset.py examples\sample_dataset.jsonl
"""

import argparse
import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径（直接运行 scripts\*.py 时必需）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evalhub_core.dataset_version import SCHEMA_VERSION, dataset_hash, load_dataset, validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 EvalHub JSONL 评测数据集")
    parser.add_argument("dataset", help="JSONL 数据集路径")
    args = parser.parse_args()

    try:
        records = load_dataset(args.dataset)
    except Exception as exc:
        print(f"读取失败：{exc}")
        return 1

    errors = validate_dataset(records)
    if errors:
        print(f"发现 {len(errors)} 个校验错误：")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"校验通过：{len(records)} 条记录，"
        f"Schema 版本 {SCHEMA_VERSION}，数据集哈希 {dataset_hash(records)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
