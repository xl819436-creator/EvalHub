"""Day 18：SQLAlchemy 持久化、回滚、分页、状态机测试。"""
from __future__ import annotations

import pytest

from tests.conftest import TestingSession, client


def _create_dataset(name: str = "demo") -> str:
    resp = client.post("/datasets", json={"name": name, "samples": [{"input": "hi", "expected_output": "hi"}]})
    assert resp.status_code == 201
    return resp.json()["dataset_id"]


def test_rollback_on_error():
    """实战 1：事务中途抛错（外键不存在），部分写入必须回滚。"""
    from sqlalchemy.exc import IntegrityError
    from app.models.evaluation import EvaluationJob
    db = TestingSession()
    db.add(EvaluationJob(
        id="job-x", dataset_id="ds-x", status="pending",
        providers=[], evaluators=[], concurrency=3,
    ))
    try:
        db.flush()  # ds-x 不存在 -> 外键约束抛错
        raise AssertionError("should have raised")
    except IntegrityError:
        db.rollback()
    assert db.query(EvaluationJob).count() == 0  # 已回滚，无残留


def test_job_created_and_persisted():
    ds = _create_dataset()
    resp = client.post("/evaluations", json={
        "dataset_id": ds, "providers": ["mock"], "evaluators": ["exact_match"],
        "concurrency": 3, "temperature": 0.7,
    })
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    from app.models.evaluation import EvaluationJob
    db = TestingSession()
    assert db.get(EvaluationJob, job_id) is not None  # 已写入数据库


def test_pagination_10_per_page():
    """实战 2：25 条 run，每页 10 条。"""
    from app.models.dataset import Dataset
    from app.models.evaluation import EvaluationJob, EvaluationRun
    from app.repositories.job_repository import JobRepository
    db = TestingSession()
    db.add(Dataset(id="ds-p", name="page-set"))
    db.add(EvaluationJob(
        id="job-p", dataset_id="ds-p", status="running",
        providers=[], evaluators=[], concurrency=1,
    ))
    for i in range(25):
        db.add(EvaluationRun(id=f"run-{i}", job_id="job-p", sample_index=i, status="ok"))
    db.commit()
    repo = JobRepository(db)
    assert len(repo.list_runs("job-p", offset=0, limit=10)) == 10
    assert len(repo.list_runs("job-p", offset=20, limit=10)) == 5


def test_invalid_transition_rejected():
    """实战 3：running 不能直接跳 pending。"""
    from app.models.dataset import Dataset
    from app.models.evaluation import EvaluationJob
    from app.services.evaluation_service import EvaluationService
    db = TestingSession()
    db.add(Dataset(id="ds-t", name="trans-set"))
    db.add(EvaluationJob(
        id="job-t", dataset_id="ds-t", status="running",
        providers=[], evaluators=[], concurrency=1,
    ))
    db.commit()
    with pytest.raises(ValueError):
        EvaluationService(db).transition("job-t", "pending")
