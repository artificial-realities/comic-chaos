"""Configuration checks and startup behaviour (no server is started)."""

import pytest

from comic_chaos import __main__ as main
from comic_chaos import config


def test_paths_are_anchored_to_project_root():
    assert config.COMICS_DIR.is_absolute()
    assert config.COMICS_DIR == config.PROJECT_ROOT / "comics"


def test_missing_key_is_an_error():
    assert config.get_openai_api_key() is None
    assert any("OPENAI_API_KEY" in e for e in config.check_config())


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_key_counts_as_missing(monkeypatch, value):
    monkeypatch.setenv("OPENAI_API_KEY", value)
    assert config.get_openai_api_key() is None


def test_configured_key_and_bundled_comics_pass(api_key):
    assert config.get_openai_api_key() == api_key
    assert config.check_config() == []


def test_check_command_exit_codes(capsys, monkeypatch):
    assert main.main(["--check"]) == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().out

    secret = "sk-test-SECRET-VALUE-123"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    assert main.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "Configuration OK" in out
    assert secret not in out


def test_listens_on_loopback_only():
    assert config.HOST == "127.0.0.1"


def test_invalid_port_is_reported(monkeypatch, capsys):
    monkeypatch.setenv("PORT", "not-a-port")
    assert main.main([]) == 1
    assert "PORT" in capsys.readouterr().out
