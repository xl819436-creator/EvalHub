"""Day 26：任务状态机（pending/running/completed/completed_with_errors/failed/cancelled）。"""

from typing import Dict, Set

# 合法迁移表：当前状态 -> 允许的下一状态集合
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "pending": {"running", "cancelled"},
    "running": {"completed", "completed_with_errors", "failed", "cancelled"},
    "completed": set(),
    "completed_with_errors": set(),
    "failed": set(),
    "cancelled": set(),
}

TERMINAL_STATES = {"completed", "completed_with_errors", "failed", "cancelled"}


def can_transition(current: str, next_state: str) -> bool:
    return next_state in ALLOWED_TRANSITIONS.get(current, set())


def transition(current: str, next_state: str) -> str:
    """执行迁移；非法迁移抛 ValueError。"""
    if not can_transition(current, next_state):
        raise ValueError(
            f"非法状态迁移：{current} -> {next_state}；"
            f"允许：{sorted(ALLOWED_TRANSITIONS.get(current, set())) or '无（终态）'}"
        )
    return next_state