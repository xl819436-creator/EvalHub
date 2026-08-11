from evalhub_core.health import get_health, main


def test_get_health_returns_ok() -> None:
    health = get_health()

    assert health == {
        "status": "ok",
        "service": "evalhub",
    }


def test_main_prints_health(capsys) -> None:
    exit_code = main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"status": "ok"' in output
    assert '"service": "evalhub"' in output