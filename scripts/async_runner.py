from __future__ import annotations

import asyncio
import sys
import time
from collections.abc import Awaitable

import httpx

from scripts.http_probe import classify_status


TaskResult = dict[str, object]

DELAYS = [
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    1.0,
    0.2,
]


async def simulated_request(
    task_id: int,
    delay: float,
    should_fail: bool = False,
) -> TaskResult:
    """模拟一个主要耗时来自等待的模型请求。"""
    started_at = time.perf_counter()

    print(
        f"task={task_id:02d} "
        f"event=start "
        f"delay={delay:.1f}s"
    )

    await asyncio.sleep(delay)

    if should_fail:
        raise RuntimeError(
            f"task {task_id} failed intentionally"
        )

    finished_at = time.perf_counter()
    elapsed = finished_at - started_at

    print(
        f"task={task_id:02d} "
        f"event=finish "
        f"elapsed={elapsed:.3f}s"
    )

    return {
        "task_id": task_id,
        "status": "success",
        "started_at": started_at,
        "finished_at": finished_at,
        "elapsed": elapsed,
        "error_type": None,
        "error": None,
    }


async def run_safely(
    task_id: int,
    delay: float,
    should_fail: bool = False,
) -> TaskResult:
    """捕获一个任务的异常，避免影响其他任务。"""
    started_at = time.perf_counter()

    try:
        return await simulated_request(
            task_id=task_id,
            delay=delay,
            should_fail=should_fail,
        )
    except Exception as exc:
        finished_at = time.perf_counter()
        elapsed = finished_at - started_at

        print(
            f"task={task_id:02d} "
            f"event=error "
            f"error_type={type(exc).__name__} "
            f"elapsed={elapsed:.3f}s"
        )

        return {
            "task_id": task_id,
            "status": "error",
            "started_at": started_at,
            "finished_at": finished_at,
            "elapsed": elapsed,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


async def run_serial(
    delays: list[float],
    failed_task_id: int | None = None,
) -> list[TaskResult]:
    """一个任务结束后再开始下一个任务。"""
    results: list[TaskResult] = []

    for task_id, delay in enumerate(delays):
        result = await run_safely(
            task_id=task_id,
            delay=delay,
            should_fail=task_id == failed_task_id,
        )
        results.append(result)

    return results


async def run_with_gather(
    delays: list[float],
    failed_task_id: int | None = None,
) -> list[TaskResult]:
    """使用create_task和gather并发执行任务。"""
    tasks = [
        asyncio.create_task(
            run_safely(
                task_id=task_id,
                delay=delay,
                should_fail=task_id == failed_task_id,
            ),
            name=f"simulated-request-{task_id}",
        )
        for task_id, delay in enumerate(delays)
    ]

    gathered_results = await asyncio.gather(
        *tasks,
        return_exceptions=True,
    )

    results: list[TaskResult] = []

    for task_id, item in enumerate(gathered_results):
        if isinstance(item, BaseException):
            results.append(
                {
                    "task_id": task_id,
                    "status": "error",
                    "started_at": 0.0,
                    "finished_at": 0.0,
                    "elapsed": 0.0,
                    "error_type": type(item).__name__,
                    "error": str(item),
                }
            )
        else:
            results.append(item)

    return results


async def run_with_task_group(
    delays: list[float],
    failed_task_id: int | None = None,
) -> list[TaskResult]:
    """使用Python 3.11 TaskGroup并发执行任务。"""
    tasks: list[asyncio.Task[TaskResult]] = []

    async with asyncio.TaskGroup() as group:
        for task_id, delay in enumerate(delays):
            task = group.create_task(
                run_safely(
                    task_id=task_id,
                    delay=delay,
                    should_fail=task_id == failed_task_id,
                ),
                name=f"simulated-request-{task_id}",
            )
            tasks.append(task)

    return [task.result() for task in tasks]


async def async_probe(
    client: httpx.AsyncClient,
    url: str,
) -> TaskResult:
    """使用调用方提供的AsyncClient执行一次请求。"""
    started_at = time.perf_counter()
    status_code: int | None = None
    error: str | None = None

    try:
        response = await client.get(url)
        status_code = response.status_code
        response.raise_for_status()
        result = classify_status(status_code)

    except httpx.TimeoutException as exc:
        result = "TimeoutError"
        error = str(exc)

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        result = classify_status(status_code)
        error = str(exc)

    except httpx.RequestError as exc:
        result = "NetworkError"
        error = str(exc)

    finished_at = time.perf_counter()

    return {
        "url": url,
        "status": result,
        "status_code": status_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "elapsed": finished_at - started_at,
        "error": error,
    }


async def probe_many(
    urls: list[str],
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[TaskResult]:
    """创建一次AsyncClient，并让整批请求复用它。"""
    async with httpx.AsyncClient(
        timeout=10.0,
        transport=transport,
    ) as client:
        tasks = [
            asyncio.create_task(
                async_probe(client, url),
                name=f"http-probe-{index}",
            )
            for index, url in enumerate(urls)
        ]

        return list(
            await asyncio.gather(
                *tasks,
                return_exceptions=False,
            )
        )


async def measure(
    label: str,
    operation: Awaitable[list[TaskResult]],
) -> tuple[list[TaskResult], float]:
    """测量一组任务的总耗时。"""
    started_at = time.perf_counter()
    results = await operation
    elapsed = time.perf_counter() - started_at

    success_count = sum(
        result["status"] == "success"
        for result in results
    )
    error_count = sum(
        result["status"] == "error"
        for result in results
    )

    print(
        f"{label}: "
        f"total={elapsed:.3f}s "
        f"success={success_count} "
        f"error={error_count}"
    )
    print()

    return results, elapsed


def demonstrate_missing_await() -> None:
    """故意创建协程但不await，仅用于观察警告。"""
    simulated_request(
        task_id=99,
        delay=0.1,
    )


async def main() -> None:
    print("=== 1. 串行实验 ===")
    await measure(
        "serial",
        run_serial(DELAYS),
    )

    print("=== 2. gather并发实验 ===")
    await measure(
        "gather",
        run_with_gather(DELAYS),
    )

    print("=== 3. TaskGroup并发实验 ===")
    await measure(
        "task_group",
        run_with_task_group(DELAYS),
    )

    print("=== 4. gather异常隔离 ===")
    await measure(
        "gather_with_error",
        run_with_gather(
            DELAYS,
            failed_task_id=4,
        ),
    )

    print("=== 5. TaskGroup异常隔离 ===")
    await measure(
        "task_group_with_error",
        run_with_task_group(
            DELAYS,
            failed_task_id=4,
        ),
    )


if __name__ == "__main__":
    if "--forget-await" in sys.argv:
        demonstrate_missing_await()
    else:
        asyncio.run(main())