"""
EvalHub - Day 14
Bounded async worker pool: Queue + Semaphore + Timeout
- 生产者把 20 个 EvaluationTask 放入 asyncio.Queue
- 3 个固定 Worker，Semaphore(3) 限制并发
- 每项任务有超时；错误写入 error_type，不中断队列
- sentinel 优雅停止 Worker，无 pending task warning
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable


# ---------- 数据结构 ----------

class TaskStatus(str, Enum):
    OK = "ok"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class EvaluationTask:
    """评测任务"""
    task_id: int
    payload: Any = None
    sleep_seconds: float = 0.5
    should_fail: bool = False
    should_hang: bool = False  # 永不返回，用于测试超时


@dataclass
class TaskResult:
    """结构化结果"""
    task_id: int
    status: TaskStatus
    error_type: str | None = None
    duration: float = 0.0
    output: Any = None


@dataclass
class PoolStats:
    """并发统计"""
    active_count: int = 0
    max_active_count: int = 0


# Worker 收到 SENTINEL 即退出循环
SENTINEL: Any = object()


# ---------- 默认任务处理器 ----------

async def default_task_handler(task: EvaluationTask) -> Any:
    """模拟一次评测：sleep 一会儿，可选失败或挂起"""
    if task.should_hang:
        await asyncio.sleep(3600)  # 永不返回，触发超时
    await asyncio.sleep(task.sleep_seconds)
    if task.should_fail:
        raise RuntimeError(f"task {task.task_id} failed on purpose")
    return {"task_id": task.task_id, "eval_score": 0.87}


# ---------- Worker ----------

async def worker(
    worker_id: int,
    queue: asyncio.Queue,
    semaphore: asyncio.Semaphore,
    stats: PoolStats,
    results: list[TaskResult],
    handler: Callable[[EvaluationTask], Awaitable[Any]] = default_task_handler,
    timeout: float = 3.0,
) -> None:
    while True:
        task = await queue.get()
        # 收到哨兵：优雅退出
        if task is SENTINEL:
            queue.task_done()
            return

        start = time.perf_counter()
        try:
            # 进入临界区：受 semaphore 限制
            async with semaphore:
                stats.active_count += 1
                stats.max_active_count = max(
                    stats.max_active_count, stats.active_count
                )
                try:
                    output = await asyncio.wait_for(
                        handler(task), timeout=timeout
                    )
                    result = TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.OK,
                        duration=time.perf_counter() - start,
                        output=output,
                    )
                finally:
                    stats.active_count -= 1
        except asyncio.TimeoutError:
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.TIMEOUT,
                error_type="TimeoutError",
                duration=time.perf_counter() - start,
            )
        except Exception as e:
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.ERROR,
                error_type=type(e).__name__,
                duration=time.perf_counter() - start,
            )

        results.append(result)
        print(
            f"[worker {worker_id}] task {task.task_id} "
            f"-> {result.status.value} ({result.duration:.2f}s)"
        )
        # 关键：无论成功失败都要调用 task_done()
        queue.task_done()


# ---------- 生产者 ----------

async def producer(
    queue: asyncio.Queue,
    tasks: list[EvaluationTask],
    num_workers: int,
) -> None:
    for task in tasks:
        await queue.put(task)
    # 每个 worker 放一个 sentinel，让它退出
    for _ in range(num_workers):
        await queue.put(SENTINEL)


# ---------- 池入口 ----------

async def run_pool(
    tasks: list[EvaluationTask],
    num_workers: int = 3,
    max_concurrency: int = 3,
    timeout: float = 3.0,
    handler: Callable[[EvaluationTask], Awaitable[Any]] = default_task_handler,
) -> tuple[list[TaskResult], PoolStats]:
    queue: asyncio.Queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(max_concurrency)
    stats = PoolStats()
    results: list[TaskResult] = []

    # 启动 num_workers 个固定 worker
    workers = [
        asyncio.create_task(
            worker(i, queue, semaphore, stats, results, handler, timeout),
            name=f"worker-{i}",
        )
        for i in range(num_workers)
    ]

    # 生产者放任务 + sentinel
    await producer(queue, tasks, num_workers)

    # 等待队列清空
    await queue.join()

    # 等待所有 worker 退出（收到 sentinel 后会 return）
    await asyncio.gather(*workers)
    return results, stats
