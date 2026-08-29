"""Day 21 真实调用脚本的离线辅助函数测试。"""

from datetime import date
import os

from scripts.day21_real_call import build_payload, load_dotenv, redacted_sample, today_cost


def test_load_dotenv_does_not_override_existing_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('MODEL_NAME="from-file"\nNEW_VALUE=created\n', encoding="utf-8")
    monkeypatch.setenv("MODEL_NAME", "from-environment")

    load_dotenv(env_file)

    assert os.environ["MODEL_NAME"] == "from-environment"
    assert os.environ["NEW_VALUE"] == "created"


def test_today_cost_only_sums_target_date(tmp_path):
    log = tmp_path / "cost_log.jsonl"
    log.write_text(
        '{"date":"2026-08-28","cost_usd":0.12}\n'
        '{"date":"2026-08-27","cost_usd":9.99}\n'
        '{"date":"2026-08-28","cost_usd":0.03}\n',
        encoding="utf-8",
    )

    assert today_cost(log, today=date(2026, 8, 28)) == 0.15


def test_redacted_sample_keeps_response_fields_only():
    sample = redacted_sample(
        {
            "model": "deepseek-chat",
            "usage": {"prompt_tokens": 1},
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": "{\"ok\":true}"},
            }],
        },
        latency_ms=12.34,
    )

    assert sample["content"] == '{"ok":true}'
    assert sample["latency_ms"] == 12.3
    assert "Authorization" not in sample
    assert "api_key" not in sample


def test_build_payload_requests_json_object():
    payload = build_payload("deepseek-chat", "hello", max_tokens=32)

    assert payload["model"] == "deepseek-chat"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["max_tokens"] == 32
