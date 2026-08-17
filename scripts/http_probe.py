import sys

import httpx


def classify_status(status: int) -> str:
    if status == 401:
        return "AuthError"
    if status == 429:
        return "RateLimitError"
    if 500 <= status < 600:
        return "ServerError"
    if 400 <= status < 500:
        return "ClientError"
    if 200 <= status < 300:
        return "OK"
    return "HTTPError"


def probe(url: str, timeout: float) -> int:
    try:
        response = httpx.get(url, timeout=timeout)
        print(f"method={response.request.method}")
        print(f"url={response.url}")
        print(f"status={response.status_code}")
        print(f"elapsed={response.elapsed.total_seconds():.3f}s")

        response.raise_for_status()

    except httpx.TimeoutException as exc:
        print("result=TimeoutError")
        print(f"url={exc.request.url}")
        return 2

    except httpx.RequestError as exc:
        print("result=NetworkError")
        print(f"url={exc.request.url}")
        return 3

    except httpx.HTTPStatusError as exc:
        result = classify_status(exc.response.status_code)
        print(f"result={result}")
        return 1

    print("result=OK")

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        print("json=", response.json())

    return 0


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else "https://httpbin.org/get"
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    return probe(url, timeout)


if __name__ == "__main__":
    raise SystemExit(main())