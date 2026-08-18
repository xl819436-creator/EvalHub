import asyncio

import httpx
import pytest

from scripts import async_runner


def test_serial_returns_ten_successful_results() -> None:
    results = asyncio.run(
        async_runner.run_serial([0.001] * 10)
    )

    assert len(results) == 10
    assert [result["task_id"] for result in results] == list(range(10))
    assert all(result["status"] == "success" for result in results)


@pytest.mark.parametrize(
    "runner",
    [
        async_runner.run_with_gather,
        async_runner.run_with_task_group,
    ],
)
def test_one_failure_keeps_other_nine_results(runner) -> None:
    results = asyncio.run(
        runner(
            [0.001] * 10,
            failed_task_id=4,
        )
    )

    success_results = [
        result
        for result in results
        if result["status"] == "success"
    ]
    error_results = [
        result
        for result in results
        if result["status"] == "error"
    ]

    assert len(results) == 10
    assert len(success_results) == 9
    assert len(error_results) == 1
    assert error_results[0]["task_id"] == 4
    assert error_results[0]["error_type"] == "RuntimeError"


@pytest.mark.parametrize(
    "runner",
    [
        async_runner.run_serial,
        async_runner.run_with_gather,
        async_runner.run_with_task_group,
    ],
)
def test_every_result_has_timing_information(runner) -> None:
    results = asyncio.run(
        runner(
            [0.001, 0.001, 0.001],
            failed_task_id=1,
        )
    )

    assert len(results) == 3

    for result in results:
        assert "started_at" in result
        assert "finished_at" in result
        assert "elapsed" in result
        assert result["finished_at"] >= result["started_at"]
        assert result["elapsed"] >= 0


def test_probe_many_reuses_one_async_client(monkeypatch) -> None:
    seen_clients: list[httpx.AsyncClient] = []

    async def fake_async_probe(
        client: httpx.AsyncClient,
        url: str,
    ) -> dict[str, object]:
        seen_clients.append(client)

        return {
            "url": url,
            "status": "OK",
            "status_code": 200,
        }

    monkeypatch.setattr(
        async_runner,
        "async_probe",
        fake_async_probe,
    )

    results = asyncio.run(
        async_runner.probe_many(
            [
                "https://test.local/1",
                "https://test.local/2",
                "https://test.local/3",
            ]
        )
    )

    assert len(results) == 3
    assert len(seen_clients) == 3
    assert all(client is seen_clients[0] for client in seen_clients)
    assert seen_clients[0].is_closed is True


def test_async_http_errors_are_isolated() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers

        if request.url.path == "/ok":
            return httpx.Response(
                200,
                json={"result": "ok"},
            )

        if request.url.path == "/server-error":
            return httpx.Response(
                500,
                json={"result": "server-error"},
            )

        if request.url.path == "/timeout":
            raise httpx.ReadTimeout(
                "timed out",
                request=request,
            )

        if request.url.path == "/network-error":
            raise httpx.ConnectError(
                "connection failed",
                request=request,
            )

        raise AssertionError(
            f"unexpected path: {request.url.path}"
        )

    transport = httpx.MockTransport(handler)

    results = asyncio.run(
        async_runner.probe_many(
            [
                "https://test.local/ok",
                "https://test.local/server-error",
                "https://test.local/timeout",
                "https://test.local/network-error",
            ],
            transport=transport,
        )
    )

    assert [result["status"] for result in results] == [
        "OK",
        "ServerError",
        "TimeoutError",
        "NetworkError",
    ]

    assert [result["status_code"] for result in results] == [
        200,
        500,
        None,
        None,
    ]