from datetime import timedelta

import httpx
import pytest

from scripts.http_probe import probe


def make_response(status: int, url: str) -> httpx.Response:
    response = httpx.Response(
        status,
        json={"status": status},
        request=httpx.Request("GET", url),
    )
    response.elapsed = timedelta(milliseconds=1)
    return response


@pytest.mark.parametrize(
    ("status", "expected", "exit_code"),
    [
        (200, "OK", 0),
        (400, "ClientError", 1),
        (401, "AuthError", 1),
        (404, "ClientError", 1),
        (429, "RateLimitError", 1),
        (500, "ServerError", 1),
    ],
)
def test_probe_http_status(
    monkeypatch,
    capsys,
    status: int,
    expected: str,
    exit_code: int,
) -> None:
    url = f"https://test.local/status/{status}"

    def fake_get(request_url: str, timeout: float) -> httpx.Response:
        assert timeout == 10.0
        return make_response(status, request_url)

    monkeypatch.setattr(httpx, "get", fake_get)

    assert probe(url, 10.0) == exit_code

    output = capsys.readouterr().out
    assert f"status={status}" in output
    assert f"result={expected}" in output
    assert "Authorization" not in output


def test_probe_timeout(monkeypatch, capsys) -> None:
    url = "https://test.local/timeout"

    def fake_get(request_url: str, timeout: float) -> httpx.Response:
        request = httpx.Request("GET", request_url)
        raise httpx.ReadTimeout("timed out", request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    assert probe(url, 0.001) == 2
    assert "result=TimeoutError" in capsys.readouterr().out


def test_probe_network_error(monkeypatch, capsys) -> None:
    url = "https://test.local/network-error"

    def fake_get(request_url: str, timeout: float) -> httpx.Response:
        request = httpx.Request("GET", request_url)
        raise httpx.ConnectError("connection failed", request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    assert probe(url, 10.0) == 3
    assert "result=NetworkError" in capsys.readouterr().out