"""HTTP routes that never reach a model: page, comic list, status, input validation."""

import pytest

SID = "session_0123456789abcdef0123456789abcdef"


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Comic Chaos" in response.data


def test_static_assets_are_served(client):
    assert client.get("/static/images/logo.webp").status_code == 200
    assert client.get("/static/fonts/ComicNeue-Regular.ttf").status_code == 200


def test_comic_list(client):
    comics = client.get("/api/comics").get_json()
    assert comics, "expected bundled comics"
    for comic in comics:
        assert {"id", "name", "name_no", "description", "description_no", "style", "panel_font"} <= comic.keys()


def test_status_without_key(client):
    assert client.get("/api/status").get_json() == {"api_available": False, "reason": "missing_api_key"}


def test_status_with_key(client, api_key):
    assert client.get("/api/status").get_json() == {"api_available": True}


def test_status_disabled(client, api_key, monkeypatch):
    monkeypatch.setenv("API_ENABLED", "false")
    assert client.get("/api/status").get_json() == {"api_available": False, "reason": "disabled"}


@pytest.mark.parametrize("route", ["/api/start-stream", "/api/submit-stream"])
def test_generation_requires_key(client, route):
    response = client.post(route, json={"comic_id": "gta", "session_id": SID, "user_input": "hi"})
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.get_json()["error"]


@pytest.mark.parametrize("body, status", [
    ({"comic_id": "gta"}, 400),
    ({"session_id": SID}, 400),
    ({"comic_id": "gta", "session_id": "../../tmp/evil"}, 400),
    ({"comic_id": ["gta"], "session_id": SID}, 400),
    ({"comic_id": "../comics/gta", "session_id": SID}, 404),
    ({"comic_id": "archive", "session_id": SID}, 404),
    ({"comic_id": "does_not_exist", "session_id": SID}, 404),
])
def test_start_stream_validation(client, api_key, body, status):
    assert client.post("/api/start-stream", json=body).status_code == status


def test_non_json_bodies_are_rejected(client, api_key):
    for route in ("/api/start-stream", "/api/submit-stream", "/api/finish"):
        assert client.post(route, data="not json", content_type="text/plain").status_code == 400


@pytest.mark.parametrize("route", ["/api/submit-stream", "/api/finish"])
def test_unknown_and_invalid_sessions(client, api_key, route):
    assert client.post(route, json={"session_id": SID, "user_input": "x"}).status_code == 404
    assert client.post(route, json={"session_id": "../x/../y", "user_input": "x"}).status_code == 400


def test_submit_rejects_non_string_input(client, api_key):
    response = client.post("/api/submit-stream", json={"session_id": SID, "user_input": {"a": 1}})
    assert response.status_code == 400
