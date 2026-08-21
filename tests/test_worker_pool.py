"""
EvalHub - Day 14
worker_pool 行为测试：队列清空、Semaphore 上限、超时、错误隔离、worker 数量、task_done 协议。
pytest.ini 已配置 asyncio_mode = auto，async 测试无需装饰器。
"""
from __future__ import annotations

import asyncio
import warnings

import pytest

from evalhub_core.worker_pool import (
    EvaluationTask,
    TaskStatus,
    run_pool,
)


def make_tasks(count: int, sleep: float = 0.02) -> list[EvaluationTask]:
    """生成 count 个正常任务（极短 sleep，保持测试秒级完成）。"""
    return [
        EvaluationTask(task_id=i, sleep_seconds=sleep)
        for i in range(count)
    ]


async def test_all_tasks_processed():
    """验收点1：20 个任务全部处理完，队列清空（run_pool 正常返回即 join() 结束）。"""
    tasks = make_tasks(20)
    results, stats = await run_pool(tasks, num_workers=3, max_concurrency=3, timeout=2.0)

    assert len(results) == 20
    assert all(r.status == TaskStatus.OK for r in results)
    assert stats.max_active_count >= 1


async def test_max_active_never_exceeds_limit():
    """验收点2：max_active_count 不超过并发上限 3，且确实发生过并发。"""
    tasks = make_tasks(10, sleep=0.05)
    results, stats = await run_pool(tasks, num_workers=3, max_concurrency=3, timeout=2.0)

    assert stats.max_active_count <= 3
    assert stats.max_active_count >= 2


async def test_max_active_bounded_by_semaphore():
    """严格验证：handler 用事件卡住临界区，第 4 个任务必须等待，max_active 恒 == 3。"""
    release = asyncio.Event()

    async def blocking_handler(task: EvaluationTask):
        await release.wait()
        return {"task_id": task.task_id}

    tasks = make_tasks(6, sleep=0.0)
    asyncio.get_running_loop().call_later(0.2, release.set)

    results, stats = await run_pool(
        tasks,
        num_workers=3,
        max_concurrency=3,
        timeout=5.0,
        handler=blocking_handler,
    )

    assert stats.max_active_count == 3
    assert len(results) == 6


async def test_timeout_returns_structured_result():
    """验收点3 + 实战1：挂起任务超时返回结构化结果，且其余任务不受影响。"""
    tasks = make_tasks(5, sleep=0.02)
    tasks[2] = EvaluationTask(task_id=2, should_hang=True)

    results, stats = await run_pool(tasks, num_workers=3, max_concurrency=3, timeout=0.2)

    by_id = {r.task_id: r for r in results}
    assert len(results) == 5
    assert by_id[2].status == TaskStatus.TIMEOUT
    assert by_id[2].error_type == "TimeoutError"
    assert by_id[2].duration > 0
    others = [r for r in results if r.task_id != 2]
    assert all(r.status == TaskStatus.OK for r in others)


async def test_error_does_not_break_queue():
    """错误写入 error_type 且不中断队列：失败任务 ERROR，其余全部 OK。"""
    tasks = make_tasks(10, sleep=0.02)
    tasks[4] = EvaluationTask(task_id=4, should_fail=True)

    results, stats = await run_pool(tasks, num_workers=3, max_concurrency=3, timeout=2.0)

    by_id = {r.task_id: r for r in results}
    assert by_id[4].status == TaskStatus.ERROR
    assert by_id[4].error_type == "RuntimeError"
    others = [r for r in results if r.task_id != 4]
    assert all(r.status == TaskStatus.OK for r in others)


@pytest.mark.parametrize("num_workers", [1, 3, 10])
async def test_worker_count_parametrized(num_workers):
    """实战2：worker 数量不影响结果正确性；并发上限始终被 Semaphore 压住。"""
    tasks = make_tasks(20, sleep=0.02)
    results, stats = await run_pool(
        tasks,
        num_workers=num_workers,
        max_concurrency=3,
        timeout=2.0,
    )

    assert len(results) == 20
    assert all(r.status == TaskStatus.OK for r in results)
    assert stats.max_active_count <= 3


async def test_join_hangs_without_task_done():
    """实战3：漏掉 task_done() 时 join() 永不返回；补上后立即返回。"""
    q: asyncio.Queue = asyncio.Queue()
    await q.put("item")

    got = await q.get()
    assert got == "item"

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(q.join(), timeout=0.2)

    q.task_done()
    await asyncio.wait_for(q.join(), timeout=0.2)


async def test_no_pending_task_warning():
    """验收点4：run_pool 结束后不遗留任何任务（无 pending task / never awaited 警告）。"""
    before = set(asyncio.all_tasks())
    tasks = make_tasks(20)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        results, stats = await run_pool(tasks, num_workers=3, max_concurrency=3, timeout=2.0)

    after = set(asyncio.all_tasks()) - before
    assert len(results) == 20
    assert after == set()

    for w in caught:
        message = str(w.message)
        assert "was never awaited" not in message
        assert "Task was destroyed but it is pending" not in message