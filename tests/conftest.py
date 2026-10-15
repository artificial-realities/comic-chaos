"""Shared test setup.

The suite is fully offline: it never reads the developer's .env, never sees a
real API key, and any attempt to open a network connection fails the test.
Generation is exercised with fakes, so running the tests costs nothing.
"""

import os
import socket

import dotenv
import pytest

# Neutralise .env loading before any project module is imported, so a
# developer's real OPENAI_API_KEY never enters the test process.
dotenv.load_dotenv = lambda *args, **kwargs: False

_ENV_VARS = (
    "OPENAI_API_KEY",
    "API_ENABLED",
    "HOST",
    "PORT",
    "DEBUG",
    "COMIC_CHAOS_LLM_MODEL",
    "COMIC_CHAOS_IMAGE_MODEL",
)
for _var in _ENV_VARS:
    os.environ.pop(_var, None)

FAKE_API_KEY = "sk-test-not-a-real-key"


class NetworkBlockedError(RuntimeError):
    pass


def _blocked(*args, **kwargs):
    raise NetworkBlockedError("Tests must not use the network (and must never call the OpenAI API)")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Fail loudly if anything tries to reach the network."""
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Each test starts with no API key and default settings."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def api_key(monkeypatch):
    """Configure a fake (syntactically plausible, unusable) API key."""
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_API_KEY)
    return FAKE_API_KEY


@pytest.fixture
def app_module(monkeypatch, tmp_path):
    """The Flask app module with session checkpoints isolated in tmp_path."""
    from comic_chaos import app as app_module

    monkeypatch.setattr(app_module, "SESSIONS_DIR", tmp_path / "sessions")
    app_module.sessions.clear()
    app_module.session_timestamps.clear()
    app_module.app.config["TESTING"] = True
    app_module.limiter.reset()
    yield app_module
    app_module.sessions.clear()
    app_module.session_timestamps.clear()


@pytest.fixture
def client(app_module):
    return app_module.app.test_client()
