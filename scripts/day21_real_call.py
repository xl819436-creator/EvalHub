"""Day 21：执行一次可控的 DeepSeek 真实调用。

默认测试不导入或运行这个脚本；真实调用需要本地 ``.env``、余额和明确的人工操作。
脚本只把脱敏响应样例和成本记录写入被 ``.gitignore`` 忽略的本地文件。
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
COST_LOG_PATH = PROJECT_ROOT / "data" / "cost_log.jsonl"
SAMPLE_PATH = PROJECT_ROOT / "experiments" / "raw_response_sample.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx

from evalhub_core.cost import DEFAULT_PRICING, calculate_cost
from evalhub_core.deepseek import extract_json_object, map_deepseek_response
from evalhub_core.schemas import LLMResponse


def load_dotenv(path: Path) -> None:
    """读取简单的 KEY=VALUE 文件，且不覆盖已有环境变量。"""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def today_cost(path: Path = COST_LOG_PATH, today: date | None = None) -> float:
    """汇总成本日志中指定日期的美元成本。"""
    if not path.exists():
        return 0.0

    target_day = (today or date.today()).isoformat()
    total = 0.0
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            entry = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"成本日志第 {line_number} 行不是合法 JSON") from exc
        if entry.get("date") == target_day:
            total += float(entry.get("cost_usd", 0.0))
    return total


def append_cost(entry: dict[str, Any], path: Path = COST_LOG_PATH) -> None:
    """追加一条成本记录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_payload(model: str, prompt: str, max_tokens: int, temperature: float = 0.0) -> dict[str, Any]:
    """构造要求模型返回 JSON 对象的请求体。"""
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是评测数据生成助手，只输出 JSON 对象。"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }


def _error_response(latency_ms: float) -> LLMResponse:
    return LLMResponse(
        content=None,
        latency_ms=latency_ms,
        error_type="provider_error",
        token_usage=None,
    )


def request_once(
    client: httpx.Client,
    api_key: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], LLMResponse, float]:
    """发送一次请求并返回原始 JSON、统一响应和耗时。"""
    started = time.perf_counter()
    response = client.post(
        "/chat/completions",
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    latency_ms = (time.perf_counter() - started) * 1000

    try:
        raw = response.json()
    except ValueError:
        raw = {"error": {"message": "服务端返回的内容不是 JSON"}}
    if not isinstance(raw, dict):
        raw = {"error": {"message": "服务端返回的 JSON 不是对象"}}
    if response.status_code >= 400 and "error" not in raw:
        raw = {"error": {"message": f"HTTP {response.status_code}"}}

    try:
        mapped = map_deepseek_response(raw, latency_ms=latency_ms)
    except (KeyError, IndexError, TypeError, ValueError):
        mapped = _error_response(latency_ms)
    mapped.status_code = response.status_code
    return raw, mapped, latency_ms


def redacted_sample(payload: dict[str, Any], latency_ms: float) -> dict[str, Any]:
    """只保留响应样例字段，避免保存请求头或其他敏感信息。"""
    choices = payload.get("choices") or [{}]
    first_choice = choices[0] if isinstance(choices[0], dict) else {}
    message = first_choice.get("message") or {}
    return {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "latency_ms": round(latency_ms, 1),
        "finish_reason": first_choice.get("finish_reason"),
        "model": payload.get("model"),
        "usage": payload.get("usage"),
        "content": message.get("content"),
    }


def save_sample(payload: dict[str, Any], latency_ms: float, path: Path = SAMPLE_PATH) -> None:
    """保存脱敏后的原始响应样例。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redacted_sample(payload, latency_ms), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"环境变量 {name} 必须是数字") from exc


def main() -> int:
    load_dotenv(ENV_PATH)

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("错误：.env 中没有 DEEPSEEK_API_KEY，请先配置。")
        return 1

    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    max_tokens = int(os.environ.get("EVALHUB_MAX_TOKENS", "512"))
    budget = _float_env("EVALHUB_DAILY_BUDGET_USD", 1.0)
    spent = today_cost()
    if spent >= budget:
        print(f"错误：今日预算已用完（已花 {spent:.6f} 美元 >= {budget:.6f} 美元）。")
        return 1

    prompt = (
        '请生成一条评测样本，只输出 JSON：'
        '{"id":"case-099","input":"中国的首都是哪里？",'
        '"expected":"北京","category":"knowledge"}'
    )
    payload = build_payload(model, prompt, max_tokens=max_tokens)

    try:
        with httpx.Client(base_url=base_url, timeout=60.0) as client:
            raw, response, latency_ms = request_once(client, api_key, payload)
    except httpx.RequestError as exc:
        print(f"网络请求失败：{exc.__class__.__name__}")
        return 1

    save_sample(raw, latency_ms)
    if not response.success:
        print(f"调用失败：error_type={response.error_type}, status_code={response.status_code}")
        return 1

    try:
        parsed = extract_json_object(response.content or "")
    except Exception as exc:
        print(f"解析失败：{exc}")
        return 1

    usage = response.token_usage
    if usage is None:
        print("调用成功，但响应没有 usage，无法安全记录成本。")
        return 1

    default_pricing = DEFAULT_PRICING.get(model, DEFAULT_PRICING["deepseek-chat"])
    pricing = {
        "input": _float_env("EVALHUB_INPUT_PRICE_PER_MILLION", default_pricing["input"]),
        "output": _float_env("EVALHUB_OUTPUT_PRICE_PER_MILLION", default_pricing["output"]),
    }
    cost = calculate_cost(usage.prompt_tokens, usage.completion_tokens, pricing)
    append_cost(
        {
            "date": date.today().isoformat(),
            "time": datetime.now().isoformat(timespec="seconds"),
            "model": model,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": cost,
            "latency_ms": round(latency_ms, 1),
        }
    )

    print("=== 调用结果 ===")
    print(f"content: {response.content}")
    print(f"解析出的 JSON: {json.dumps(parsed, ensure_ascii=False)}")
    print(f"prompt_tokens: {usage.prompt_tokens}")
    print(f"completion_tokens: {usage.completion_tokens}")
    print(f"total_tokens: {usage.total_tokens}")
    print(f"latency_ms: {latency_ms:.1f}")
    print(f"finish_reason: {(raw.get('choices') or [{}])[0].get('finish_reason')}")
    print(f"cost_usd: {cost:.6f}")
    print(f"脱敏样例已保存到: {SAMPLE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
