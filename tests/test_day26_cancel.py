"""Day 26：取消幂等测试（实战题 3）。"""

import pytest

from app.services.evaluation_service import EvaluationManager


def test_repeat_cancel_is_idempotent():
    manager = EvaluationManager()
    manager.create("job-1", total=5)

    first = manager.cancel("job-1")
    second = manager.cancel("job-1")  # 第二次取消

    assert first.status == "pending"  # 还没执行，标记取消
    assert second.status == "pending"  # 幂等：状态不变，不重复修改
    assert manager._cancel_flags["job-1"] == [True]  # 标记只置一次


def test_cancel_unknown_job_raises():
    manager = EvaluationManager()
    with pytest.raises(KeyError, match="任务不存在"):
        manager.cancel("no-such-job")