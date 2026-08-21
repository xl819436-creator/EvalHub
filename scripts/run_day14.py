"""
EvalHub - Day 14
演示脚本：20 个评测任务的异步队列流水线
- 17 个正常任务 + 1 个永不返回(触发超时) + 1 个故意失败 + 1 个正常
- 3 个固定 Worker，Semaphore(3) 限制并发

运行方式（必须用 -m，包式导入）：
    python -m scripts.run_day14
    python -m scripts.run_day14 --workers 1
"""
from __future__ import annotations

import argparse
import asyncio
import time

from evalhub_core.worker_pool import EvaluationTask, run_pool


def build_tasks(count: int = 20) -> list[EvaluationTask]:
    """构造 count 个任务：大部分正常，混入 1 个挂起(超时)和 1 个故意失败。"""
    tasks = [
        EvaluationTask(task_id=i, sleep_seconds=0.2 + (i % 6) * 0.1)
        for i in range(count)
    ]
    tasks[7] = EvaluationTask(task_id=7, should_hang=True)
    tasks[13] = EvaluationTask(task_id=13, should_fail=True)
    return tasks


async def main(num_workers: int, max_concurrency: int, timeout: float) -> None:
    tasks = build_tasks()
    started = time.perf_counter()
    results, stats = await run_pool(
        tasks,
        num_workers=num_workers,
        max_concurrency=max_concurrency,
        timeout=timeout,
    )
    elapsed = time.perf_counter() - started

    summary = {"ok": 0, "timeout": 0, "error": 0}
    for r in sorted(results, key=lambda r: r.task_id):
        summary[r.status.value] += 1
        print(f"task={r.task_id:02d} status={r.status.value} duration={r.duration:.2f}s")

    print(
        f"summary ok={summary['ok']} timeout={summary['timeout']} error={summary['error']} "
        f"total={elapsed:.2f}s max_active={stats.max_active_count} "
        f"workers={num_workers} concurrency={max_concurrency} timeout={timeout}s"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EvalHub Day 14 worker pool demo")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    asyncio.run(main(args.workers, args.concurrency, args.timeout))