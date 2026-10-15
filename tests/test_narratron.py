"""Narratron response handling and JSON repair (no LLM calls)."""

import json

import pytest

from comic_chaos.json_sanitizer import repair_json, sanitize_text
from comic_chaos.narratron.models import FALLBACK_RESPONSE, NarratronResponse
from comic_chaos.narratron.narratron import Narratron
from comic_chaos.state.static_config import StaticConfig
from comic_chaos.config import COMICS_DIR


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


def test_repair_truncated_llm_json():
    good = {"panels": [panel(True)], "long_term_narrative": ["a", "b"]}
    corrupted = json.dumps(good)[:-1] + ', "rolling_summary_update": "unterminated garbage garbage'
    assert json.loads(repair_json(corrupted)) == good


def test_sanitize_text_keeps_norwegian_and_strips_invisibles():
    assert sanitize_text("Blåbærøl​\x00!") == "Blåbærøl!"


@pytest.fixture
def narratron(api_key):
    config = StaticConfig.load_from_directory(COMICS_DIR / "gta")
    return Narratron(config=config, api_key=api_key, language="no")


def test_unparseable_output_falls_back(narratron):
    assert narratron._parse_response("definitely not json").raw is FALLBACK_RESPONSE


def test_llm_errors_are_logged_and_fall_back(narratron, monkeypatch, capsys):
    from comic_chaos.state.comic_state import ComicState

    def broken_llm(*args, **kwargs):
        raise RuntimeError("model_not_found")

    monkeypatch.setattr(narratron, "_call_llm", broken_llm)
    response = narratron.process_input("hi", ComicState.initialize_from_config(narratron.config))

    assert response.raw is FALLBACK_RESPONSE
    assert response.panels[0].elements[0]["placeholder"] == "Hva skjer videre?"  # localized
    assert "model_not_found" in capsys.readouterr().out
