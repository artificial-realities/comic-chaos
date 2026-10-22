"""Narratron response handling (no LLM calls)."""

from types import SimpleNamespace

import pytest

from comic_chaos.config import COMICS_DIR
from comic_chaos.narratron.models import FALLBACK_RESPONSE, NarratronResponse, NarratronResponseSchema
from comic_chaos.narratron.narratron import Narratron
from comic_chaos.state.comic_state import ComicState
from comic_chaos.state.static_config import StaticConfig
from comic_chaos.text_sanitizer import sanitize_text


def panel(user_input):
    return {"scene_description": "s", "elements": [
        {"type": "speech", "position": "top-left", "user_input": user_input, "text": "Hi"}]}


def test_last_panel_is_forced_interactive():
    response = NarratronResponse({"panels": [panel(False)]})
    assert response.panels[-1].is_auto is False
    assert response.panels[-1].elements[-1]["user_input"] is True
    assert "text" not in response.panels[-1].elements[-1]


def test_at_most_two_panels():
    response = NarratronResponse({"panels": [panel(False), panel(False), panel(True), panel(True)]})
    assert len(response.panels) == 2
    assert [p.is_auto for p in response.panels] == [True, False]


def test_sanitize_text_keeps_norwegian_and_strips_invisibles():
    assert sanitize_text("Blåbærøl​\x00!") == "Blåbærøl!"


@pytest.fixture
def narratron(api_key):
    config = StaticConfig.load_from_directory(COMICS_DIR / "gta")
    return Narratron(config=config, api_key=api_key, language="no")


def fake_parse(parsed, refusal=None):
    """Stand-in for client.chat.completions.parse that returns one message."""
    message = SimpleNamespace(parsed=parsed, refusal=refusal)
    return lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=message)])


def turn(text):
    return NarratronResponseSchema.model_validate({
        "panels": [panel(True) | {"scene_description": text}],
        "scene_summary": {"scene_setting": "A street", "characters_present": ["Hero"], "current_action": "Talking"},
        "rolling_summary_update": text,
        "short_term_narrative": ["Next"],
        "long_term_narrative": ["Later"],
    })


def test_structured_response_is_used_and_sanitized(narratron, monkeypatch):
    monkeypatch.setattr(narratron.client.chat.completions, "parse", fake_parse(turn("Hei\x00 på deg")))
    state = ComicState.initialize_from_config(narratron.config)

    response = narratron.process_input("hi", state)

    assert response.raw is not FALLBACK_RESPONSE
    assert response.panels[0].scene_description == "Hei på deg"
    assert state.narrative.rolling_summary == "Hei på deg"


def test_refusal_falls_back(narratron, monkeypatch, capsys):
    monkeypatch.setattr(narratron.client.chat.completions, "parse", fake_parse(None, refusal="no"))
    response = narratron.process_input("hi", ComicState.initialize_from_config(narratron.config))

    assert response.raw is FALLBACK_RESPONSE
    assert "refusal" in capsys.readouterr().out


def test_llm_errors_are_logged_and_fall_back(narratron, monkeypatch, capsys):
    def broken_llm(*args, **kwargs):
        raise RuntimeError("model_not_found")

    monkeypatch.setattr(narratron, "_call_llm", broken_llm)
    response = narratron.process_input("hi", ComicState.initialize_from_config(narratron.config))

    assert response.raw is FALLBACK_RESPONSE
    assert response.panels[0].elements[0]["placeholder"] == "Hva skjer videre?"  # localized
    assert "model_not_found" in capsys.readouterr().out
