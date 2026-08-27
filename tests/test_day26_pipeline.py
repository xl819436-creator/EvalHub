"""Day 26：完整链路测试（状态机、局部失败、取消、幂等、非法迁移）。"""

from evalhub_core.eval_runner import EvalJob, run_job
from evalhub_core.job_state_machine import TERMINAL_STATES, can_transition, transition

def test_20_with_3_failures_is_completed_with_errors():
    # 实战题 1：3/20 失败 → completed_with_errors，不是 failed
    job = EvalJob(job_id="job-a")
    job = run_job(job, total=20, execute_one=lambda i: None, fail_indexes={2, 7, 13})
    assert job.status == "completed_with_errors"
    assert sum(1 for r in job.runs if r.status == "failed") == 3


def test_cancel_half_keeps_count_conserved():
    # 实战题 2：执行到一半取消 → completed+failed+cancelled = total
    job = EvalJob(job_id="job-b")
    cancel_flag = [False]

    def execute_with_cancel(i):
        if i == 10:
            cancel_flag[0] = True

    job = run_job(job, total=20, execute_one=execute_with_cancel, cancel_flag=cancel_flag)
    counts = {}
    for run in job.runs:
        counts[run.status] = counts.get(run.status, 0) + 1
    assert counts.get("completed", 0) + counts.get("failed", 0) + counts.get("cancelled", 0) == 20
    assert job.status == "cancelled"


def test_illegal_transition_raises():
    # 验收：为非法迁移写测试
    assert can_transition("completed", "running") is False
    try:
        transition("completed", "running")
        raise AssertionError("应当抛 ValueError")
    except ValueError:
        pass