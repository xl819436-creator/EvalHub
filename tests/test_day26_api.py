"""Day 26：FastAPI 任务查询、取消和 Markdown 报告。"""

from app.models.evaluation import EvaluationJob, EvaluationRun
from tests.conftest import TestingSession, client


def _create_job() -> str:
    dataset = client.post(
        "/datasets",
        json={"name": "demo", "samples": [{"input": "hi", "expected_output": "hi"}]},
    )
    assert dataset.status_code == 201
    response = client.post(
        "/evaluations",
        json={
            "dataset_id": dataset.json()["dataset_id"],
            "providers": ["mock"],
            "evaluators": ["exact_match"],
            "concurrency": 3,
        },
    )
    assert response.status_code == 202
    return response.json()["job_id"]


def _add_runs(job_id: str) -> None:
    db = TestingSession()
    db.add_all(
        [
            EvaluationRun(id="run-0", job_id=job_id, sample_index=0, status="completed", score=1.0),
            EvaluationRun(id="run-1", job_id=job_id, sample_index=1, status="failed", score=0.0),
            EvaluationRun(id="run-2", job_id=job_id, sample_index=2, status="cancelled", score=None),
        ]
    )
    db.commit()
    db.close()


def test_get_evaluation_returns_persisted_run_summary():
    job_id = _create_job()
    _add_runs(job_id)

    response = client.get(f"/evaluations/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["total_runs"] == 3
    assert body["completed_runs"] == 1
    assert body["failed_runs"] == 1
    assert body["cancelled_runs"] == 1
    assert [run["run_id"] for run in body["runs"]] == ["run-0", "run-1", "run-2"]


def test_get_unknown_evaluation_uses_unified_404():
    response = client.get("/evaluations/job-missing")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_cancel_is_persisted_and_idempotent():
    job_id = _create_job()

    first = client.post(f"/evaluations/{job_id}/cancel")
    second = client.post(f"/evaluations/{job_id}/cancel")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "cancelled"
    assert second.json()["status"] == "cancelled"
    assert client.get(f"/evaluations/{job_id}").json()["status"] == "cancelled"


def test_cancel_terminal_job_keeps_terminal_status():
    job_id = _create_job()
    db = TestingSession()
    job = db.get(EvaluationJob, job_id)
    assert job is not None
    job.status = "completed"
    db.commit()

    response = client.post(f"/evaluations/{job_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_report_contains_counts_and_failure_records():
    job_id = _create_job()
    _add_runs(job_id)

    response = client.get(f"/evaluations/{job_id}/report")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "# EvalHub 评测报告" in response.text
    assert "| all | 3 | 33.33% | 0.50 |" in response.text
    assert "run-1" in response.text
    assert "run-2" in response.text


def test_get_dataset_returns_persisted_sample_count():
    created = client.post(
        "/datasets",
        json={"name": "lookup", "samples": [{"input": "hi", "expected_output": "hi"}]},
    )
    dataset_id = created.json()["dataset_id"]

    response = client.get(f"/datasets/{dataset_id}")

    assert response.status_code == 200
    assert response.json() == {
        "dataset_id": dataset_id,
        "name": "lookup",
        "sample_count": 1,
    }


def test_run_mock_persists_results_and_is_idempotent():
    dataset = client.post(
        "/datasets",
        json={
            "name": "mock-run",
            "samples": [
                {"input": "hi", "expected_output": "Mock response: hi"},
                {"input": "bye", "expected_output": "wrong"},
            ],
        },
    )
    job = client.post(
        "/evaluations",
        json={
            "dataset_id": dataset.json()["dataset_id"],
            "providers": ["mock"],
            "evaluators": ["exact_match"],
        },
    )
    job_id = job.json()["job_id"]

    first = client.post(f"/evaluations/{job_id}/run")
    second = client.post(f"/evaluations/{job_id}/run")

    assert first.status_code == 200
    assert first.json()["status"] == "completed_with_errors"
    assert second.json() == first.json()
    status = client.get(f"/evaluations/{job_id}").json()
    assert status["total_runs"] == 2
    assert status["completed_runs"] == 1
    assert status["failed_runs"] == 1
    db = TestingSession()
    runs = sorted(db.query(EvaluationRun).filter(EvaluationRun.job_id == job_id).all(), key=lambda run: run.sample_index)
    assert runs[0].input == "hi"
    assert runs[0].actual == "Mock response: hi"
    assert runs[1].expected == "wrong"
    assert "exact_match" in runs[1].reason
    db.close()


def test_run_dummy_records_failed_exact_match_without_network():
    dataset = client.post(
        "/datasets",
        json={"name": "dummy-run", "samples": [{"input": "hi", "expected_output": "hi"}]},
    )
    job = client.post(
        "/evaluations",
        json={
            "dataset_id": dataset.json()["dataset_id"],
            "providers": ["dummy"],
            "evaluators": ["exact_match"],
        },
    )

    response = client.post(f"/evaluations/{job.json()['job_id']}/run")

    assert response.status_code == 200
    assert response.json()["status"] == "completed_with_errors"
    assert client.get(f"/evaluations/{job.json()['job_id']}").json()["failed_runs"] == 1


def test_run_deepseek_is_rejected_before_any_paid_call():
    job_id = _create_job()
    db = TestingSession()
    job = db.get(EvaluationJob, job_id)
    assert job is not None
    job.providers = ["deepseek"]
    db.commit()
    db.close()

    response = client.post(f"/evaluations/{job_id}/run")

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
