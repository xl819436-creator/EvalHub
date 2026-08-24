"""EvalHub - Day 16/17/18：API 校验与统一错误测试（不调用外部 API）。"""
from __future__ import annotations

from tests.conftest import client


def _valid_dataset() -> dict:
    return {
        "name": "demo",
        "samples": [{"input": "你好", "expected_output": "你好呀"}],
    }


def _valid_evaluation(dataset_id: str = "ds-1") -> dict:
    return {
        "dataset_id": dataset_id,
        "providers": ["mock"],
        "evaluators": ["exact_match"],
        "concurrency": 3,
        "temperature": 0.7,
    }


def test_root_ok():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "evalhub"


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "evalhub"}


def test_unknown_route_returns_unified_404():
    resp = client.get("/no-such-path")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "HTTP_ERROR"
    assert "message" in body
    assert "request_id" in body


def test_create_dataset_valid():
    resp = client.post("/datasets", json=_valid_dataset())
    assert resp.status_code == 201
    body = resp.json()
    assert body["dataset_id"] == "ds-1"
    assert body["sample_count"] == 1


def test_create_dataset_blank_name_rejected():
    payload = _valid_dataset()
    payload["name"] = "   "
    resp = client.post("/datasets", json=payload)
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"


def test_create_dataset_empty_samples_rejected():
    payload = {"name": "demo", "samples": []}
    resp = client.post("/datasets", json=payload)
    assert resp.status_code == 422


def test_duplicate_dataset_name_conflict():
    assert client.post("/datasets", json=_valid_dataset()).status_code == 201
    resp = client.post("/datasets", json=_valid_dataset())
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "CONFLICT"
    assert "request_id" in body


def test_create_evaluation_valid():
    client.post("/datasets", json=_valid_dataset())
    resp = client.post("/evaluations", json=_valid_evaluation("ds-1"))
    assert resp.status_code == 202
    assert resp.json()["status"] == "pending"


def test_evaluation_unknown_dataset_404():
    resp = client.post("/evaluations", json=_valid_evaluation("ds-99"))
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "NOT_FOUND"
    assert "request_id" in body


def test_evaluation_empty_providers_rejected():
    payload = _valid_evaluation("ds-1")
    payload["providers"] = []
    resp = client.post("/evaluations", json=payload)
    assert resp.status_code == 422


def test_evaluation_empty_evaluators_rejected():
    payload = _valid_evaluation("ds-1")
    payload["evaluators"] = []
    resp = client.post("/evaluations", json=payload)
    assert resp.status_code == 422


def test_evaluation_concurrency_out_of_range():
    for bad in (0, 21):
        payload = _valid_evaluation("ds-1")
        payload["concurrency"] = bad
        assert client.post("/evaluations", json=payload).status_code == 422


def test_evaluation_temperature_out_of_range():
    for bad in (-0.1, 2.5):
        payload = _valid_evaluation("ds-1")
        payload["temperature"] = bad
        assert client.post("/evaluations", json=payload).status_code == 422


def test_error_response_has_three_required_fields():
    resp = client.post("/evaluations", json=_valid_evaluation("ds-9"))
    body = resp.json()
    assert {"code", "message", "request_id"}.issubset(body.keys())
