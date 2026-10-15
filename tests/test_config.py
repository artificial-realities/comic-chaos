"""Configuration checks and startup behaviour (no server is started)."""

import pytest

from comic_chaos import __main__ as main
from comic_chaos import config
from comic_chaos.state.static_config import StaticConfig


def test_paths_are_anchored_to_project_root():
    assert config.COMICS_DIR.is_absolute()
    assert config.COMICS_DIR == config.PROJECT_ROOT / "comics"
    assert config.SESSIONS_DIR.is_relative_to(config.PROJECT_ROOT / "output")


def test_missing_key_is_an_error():
    assert config.get_openai_api_key() is None
    errors, _ = config.check_config()
    assert any("OPENAI_API_KEY" in e for e in errors)


@pytest.mark.parametrize("value", ["", "   ", "your_openai_api_key_here"])
def test_placeholder_key_counts_as_missing(monkeypatch, value):
    monkeypatch.setenv("OPENAI_API_KEY", value)
    assert config.get_openai_api_key() is None


def test_configured_key_and_bundled_comics_pass(api_key):
    assert config.get_openai_api_key() == api_key
    errors, warnings = config.check_config()
    assert errors == []
    assert warnings == []


def test_api_disabled_is_a_warning(api_key, monkeypatch):
    monkeypatch.setenv("API_ENABLED", "false")
    assert config.is_api_enabled() is False
    errors, warnings = config.check_config()
    assert errors == []
    assert any("API_ENABLED" in w for w in warnings)


def test_check_command_exit_codes(capsys, monkeypatch):
    assert main.main(["--check"]) == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().out

    secret = "sk-test-SECRET-VALUE-123"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    assert main.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "Configuration OK" in out
    assert secret not in out


def test_default_host_is_loopback():
    assert config.DEFAULT_HOST == "127.0.0.1"


def test_debug_refused_on_public_interface(monkeypatch, capsys):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("HOST", "0.0.0.0")
    assert main.main([]) == 1  # returns before the server starts
    assert "DEBUG" in capsys.readouterr().out


def test_invalid_port_is_reported(monkeypatch, capsys):
    monkeypatch.setenv("PORT", "not-a-port")
    assert main.main([]) == 1
    assert "PORT" in capsys.readouterr().out


def test_model_env_overrides(monkeypatch):
    gta_dir = config.COMICS_DIR / "gta"
    default = StaticConfig.load_from_directory(gta_dir).comic_config

    monkeypatch.setenv("COMIC_CHAOS_IMAGE_MODEL", "image-model-override")
    monkeypatch.setenv("COMIC_CHAOS_LLM_MODEL", "llm-model-override")
    overridden = StaticConfig.load_from_directory(gta_dir).comic_config

    assert overridden.image_model == "image-model-override"
    assert overridden.llm_model == "llm-model-override"
    assert overridden.image_quality == default.image_quality  # everything else unchanged
