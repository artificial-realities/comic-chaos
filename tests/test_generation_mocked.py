"""A whole comic, start → submit → finish, through the real Flask routes.

The OpenAI-backed pieces (Narratron's LLM calls and the image generator) are
replaced with fakes, so this costs nothing and needs no key.
"""

import base64
from io import BytesIO

import pytest
from PIL import Image

from comic_chaos.image_gen.image_generator import ImageGenerator
from comic_chaos.narratron.models import NarratronResponse, OpeningSequenceResponse
from comic_chaos.narratron.narratron import Narratron
from comic_chaos.state.comic_state import ComicState
from helpers import BUBBLE_BOX, make_bubble_png, parse_sse

SID = "session_0123456789abcdef0123456789abcdef"


def interactive_panel(placeholder="What now?"):
    return {
        "scene_description": "Hero stands in the street",
        "elements": [{"type": "speech", "character_name": "Hero", "position": "top-left",
                      "user_input": True, "placeholder": placeholder}],
    }


def narrator_turn(panels):
    return {
        "panels": panels,
        "scene_summary": {"scene_setting": "A street", "characters_present": ["Hero"], "current_action": "Talking"},
        "rolling_summary_update": "Hero talks.",
        "short_term_narrative": ["Something happens"],
        "long_term_narrative": ["Hero wins"],
    }


@pytest.fixture
def fake_models(monkeypatch):
    """Replace every model call with deterministic fakes and record what was asked."""
    calls = {"images": 0, "inputs": []}
    png = make_bubble_png()
    x, y, w, h = BUBBLE_BOX

    def fake_opening(self, comic_state):
        response = OpeningSequenceResponse.from_raw({
            "title_card": {"scene_description": "A skyline", "title_treatment": "Title", "atmosphere": "Moody"},
            "first_panel": narrator_turn([interactive_panel()]),
            "initial_narrative": {"short_term": ["Begin"], "long_term": ["End"]},
        })
        self._apply_state_changes(response.first_panel, comic_state)
        return response

    def fake_process_input(self, user_input, comic_state):
        calls["inputs"].append(user_input)
        auto = {"scene_description": "Meanwhile", "elements": [
            {"type": "narration", "position": "top-left", "user_input": False, "text": "Later..."}]}
        response = NarratronResponse(narrator_turn([auto, interactive_panel()]))
        self._apply_state_changes(response, comic_state)
        return response

    def fake_images(self, render_state, visual_style, elements=None, **kwargs):
        calls["images"] += 1
        b64 = base64.b64encode(png).decode("ascii")
        yield {"type": "partial", "image_base64": b64, "partial_index": 0}
        bubbles = [{"x": x, "y": y, "width": w, "height": h, "center_x": x + w // 2, "center_y": y + h // 2}]
        yield {"type": "complete", "image_base64": b64, "image_bytes": png,
               "detected_bubbles": bubbles if elements else []}

    monkeypatch.setattr(Narratron, "generate_opening_sequence", fake_opening)
    monkeypatch.setattr(Narratron, "process_input", fake_process_input)
    monkeypatch.setattr(ImageGenerator, "generate_image_streaming", fake_images)
    return calls


def test_full_comic_flow(client, app_module, api_key, fake_models):
    # --- start: title card + first interactive panel ---
    response = client.post("/api/start-stream", json={"comic_id": "gta", "session_id": SID, "language": "en"})
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    types = [e["type"] for e in parse_sse(response.data)]
    assert types == ["init_title_card", "partial", "complete_title_card", "init", "partial", "complete"]

    # --- submit: an automatic transition panel, then the next interactive panel ---
    response = client.post("/api/submit-stream", json={"session_id": SID, "user_input": "Hello <there>!"})
    events = parse_sse(response.data)
    assert [e["type"] for e in events if e["type"] != "partial"] == ["init_auto", "complete_auto", "init", "complete"]
    assert fake_models["inputs"] == ["Hello <there>!"]
    assert fake_models["images"] == 4  # title card, panel 1, auto panel, panel 3

    # --- finish: the trailing unfilled panel is left out of the strip ---
    response = client.post("/api/finish", json={"session_id": SID})
    result = response.get_json()
    assert response.status_code == 200, result
    assert result["panel_count"] == 3  # title card, filled panel 1, auto panel
    strip = Image.open(BytesIO(base64.b64decode(result["strip_image"])))
    assert strip.format == "PNG" and strip.width > strip.height

    # Finished sessions are cleaned up
    assert SID not in app_module.sessions


def test_image_failure_rolls_back_the_turn(client, app_module, api_key, fake_models, monkeypatch):
    client.post("/api/start-stream", json={"comic_id": "gta", "session_id": SID, "language": "en"}).get_data()
    panels_before = len(app_module.sessions[SID].panels_data)

    def failing_images(self, *args, **kwargs):
        yield {"type": "error", "error": "Your request was rejected by the safety system"}

    monkeypatch.setattr(ImageGenerator, "generate_image_streaming", failing_images)
    events = parse_sse(client.post("/api/submit-stream", json={"session_id": SID, "user_input": "x"}).data)

    assert events[-1]["type"] == "error"
    session = app_module.sessions[SID]
    assert len(session.panels_data) == panels_before
    assert session.panels_data[-1]["user_input_text"] is None  # the user can retry


def test_submit_before_first_panel_is_an_error_event(client, app_module, api_key, fake_models):
    # Start-stream response never consumed: the session exists but has no panels yet,
    # as if the connection dropped while the title card was being generated.
    client.post("/api/start-stream", json={"comic_id": "gta", "session_id": SID, "language": "en"})
    session = app_module.sessions[SID]
    session.state = ComicState.initialize_from_config(session.config)
    assert session.panels_data == []

    events = parse_sse(client.post("/api/submit-stream", json={"session_id": SID, "user_input": "x"}).data)
    assert [e["type"] for e in events] == ["error"]


def test_finish_includes_text_typed_but_not_submitted(client, app_module, api_key, fake_models):
    client.post("/api/start-stream", json={"comic_id": "gta", "session_id": SID, "language": "en"}).get_data()

    response = client.post("/api/finish", json={"session_id": SID, "user_input": "  Last words\x00  "})
    result = response.get_json()

    assert response.status_code == 200, result
    assert result["panel_count"] == 2  # title card and the panel the text was typed into
