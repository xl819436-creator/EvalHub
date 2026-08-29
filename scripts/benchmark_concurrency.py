"""Day 27：1/5/10 并发基准实验（Mock，不花钱）。"""

import asyncio
import statistics
import time

from evalhub_core.evaluators import EvaluationItem, ExactMatchEvaluator
from evalhub_core.metrics import percentile


def make_items(total: int = 50) -> list[EvaluationItem]:
    return [
        EvaluationItem(id=f"case-{i}", category="math", input="q",
                       expected="2", actual="2" if i % 10 != 0 else "3")
        for i in range(total)
    ]


async def run_batch(concurrency: int, total: int = 50) -> dict:
    items = make_items(total)
    evaluator = ExactMatchEvaluator()
    sem = asyncio.Semaphore(concurrency)
    latencies = []
    started = time.perf_counter()

    async def one(item: EvaluationItem) -> None:
        async with sem:
            t0 = time.perf_counter()
            await asyncio.sleep(0.01)  # 模拟一次调用
            evaluator.evaluate(item)
            latencies.append((time.perf_counter() - t0) * 1000)

    await asyncio.gather(*[one(item) for item in items])
    elapsed = time.perf_counter() - started
    return {
        "concurrency": concurrency,
        "total": total,
        "throughput": total / elapsed,
        "mean_ms": statistics.mean(latencies),
        "p95_ms": percentile(latencies, 95),
        "fail_rate": sum(1 for i in items if not i.passed) / total,
    }


if __name__ == "__main__":
    for c in (1, 5, 10):
        result = asyncio.run(run_batch(c))
        print(result)