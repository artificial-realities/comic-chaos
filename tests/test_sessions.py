"""Session IDs and on-disk checkpoints."""

import json
import os
import time

import pytest

from src.comic_session import ComicSession
from src.state.comic_state import ComicState
from helpers import make_bubble_png


@pytest.mark.parametrize("session_id", [
    "session_1760000000000_k3j9x0abc",          # format used before this release
    "session_0123456789abcdef0123456789abcdef",  # current frontend format
    "A-Za-z0-9_-A-Za-z0-9",
])
def test_valid_session_ids(app_module, session_id):
    assert app_module.is_valid_session_id(session_id)


@pytest.mark.parametrize("session_id", [
    None, 123, "", "short", "../../etc/passwd", "session/../../x", "session_..\\..\\x",
    "session_abc.json", "session_ abcdefghijkl", "x" * 129,
])
def test_invalid_session_ids(app_module, session_id):
    assert not app_module.is_valid_session_id(session_id)
    with pytest.raises(ValueError):
        app_module.session_path(session_id)


def make_session(language="en"):
    """A real ComicSession for a bundled comic, with no API key (no clients)."""
    session = ComicSession("gta", language=language)
    session.state = ComicState.initialize_from_config(session.config)
    session.state.add_panel('Hero: "Hello"')
    session.panels_data = [
        {"panel_number": 0, "image_bytes": make_bubble_png(), "elements": [], "user_input_text": None,
         "detected_bubbles": [], "is_title_card": True, "is_auto": False},
        {"panel_number": 1, "image_bytes": make_bubble_png(),
         "elements": [{"type": "speech", "character_name": "Hero", "position": "top-left",
                       "user_input": True, "placeholder": "Say something"}],
         "user_input_text": "Æøå & <b>hei</b>",
         "detected_bubbles": [{"x": 1, "y": 2, "width": 3, "height": 4, "center_x": 2, "center_y": 4}],
         "is_auto": False},
    ]
    return session


SID = "session_0123456789abcdef0123456789abcdef"


def test_checkpoint_round_trip_is_json(app_module):
    session = make_session()
    app_module.save_session(SID, session)

    path = app_module.SESSIONS_DIR / f"{SID}.json"
    on_disk = json.loads(path.read_text(encoding="utf-8"))  # plain JSON, not pickle
    assert on_disk["comic_id"] == "gta"

    loaded = app_module.load_session_data(SID)
    assert loaded["panels_data"] == session.panels_data  # image bytes restored exactly
    assert loaded["state"] == session.state
    assert loaded["language"] == "en"


def test_recover_session_from_checkpoint(app_module):
    session = make_session(language="no")
    app_module.save_session(SID, session)

    recovered = app_module.get_session(SID)  # not in memory → recovered from disk
    assert recovered is not None and recovered is not session
    assert recovered.comic_id == "gta" and recovered.language == "no"
    assert recovered.panels_data == session.panels_data
    assert app_module.sessions[SID] is recovered


@pytest.mark.parametrize("content", ["not json", '{"version": 999}', "[]", '{"version": 1}'])
def test_unreadable_checkpoints_are_ignored(app_module, content):
    app_module.SESSIONS_DIR.mkdir(parents=True)
    (app_module.SESSIONS_DIR / f"{SID}.json").write_text(content, encoding="utf-8")
    assert app_module.load_session_data(SID) is None
    assert app_module.get_session(SID) is None


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions")
def test_checkpoints_are_private(app_module):
    app_module.save_session(SID, make_session())
    assert app_module.SESSIONS_DIR.stat().st_mode & 0o077 == 0
    assert (app_module.SESSIONS_DIR / f"{SID}.json").stat().st_mode & 0o077 == 0
    assert [p.name for p in app_module.SESSIONS_DIR.iterdir()] == [f"{SID}.json"]  # no temp files left


def test_stale_sessions_are_evicted(app_module):
    session = make_session()
    app_module.sessions[SID] = session
    app_module.save_session(SID, session)
    app_module.session_timestamps[SID] = time.monotonic() - app_module.SESSION_TTL_SECONDS - 1

    app_module.cleanup_stale_sessions()

    assert SID not in app_module.sessions
    assert not (app_module.SESSIONS_DIR / f"{SID}.json").exists()
