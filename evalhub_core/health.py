"""EvalHub 最小健康检查。"""

from __future__ import annotations

import json


def get_health() -> dict[str, str]:
    """返回不依赖数据库和外部 API 的健康状态。"""

    return {
        "status": "ok",
        "service": "evalhub",
    }


def main() -> int:
    """将健康状态输出为 JSON。"""

    print(
        json.dumps(
            get_health(),
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())