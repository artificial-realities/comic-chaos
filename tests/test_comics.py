"""Comic discovery and blueprint validation."""

import json

import pytest

from comics.comic_registry import ComicRegistry
from src.config import COMICS_DIR
from src.state.comic_state import ComicState
from src.state.static_config import StaticConfig, validate_comic_dir

BUNDLED = sorted(p.parent.name for p in COMICS_DIR.glob("*/blueprint.json") if p.parent.name != "archive")

MINIMAL_BLUEPRINT = {
    "title": "Test Comic",
    "synopsis": "A test.",
    "locations": [{"name": "Lab", "description": "A bright laboratory"}],
    "characters": [{"name": "Testy", "description": "A round robot with big eyes"}],
}


def write_comic(root, comic_id, blueprint, config=None):
    comic_dir = root / comic_id
    comic_dir.mkdir(parents=True)
    text = blueprint if isinstance(blueprint, str) else json.dumps(blueprint)
    (comic_dir / "blueprint.json").write_text(text, encoding="utf-8")
    if config is not None:
        (comic_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    return comic_dir


def test_bundled_comics_are_discovered():
    registry = ComicRegistry(comics_dir=COMICS_DIR)
    assert BUNDLED, "expected at least one bundled comic"
    assert sorted(c.id for c in registry.get_available_comics()) == BUNDLED
    assert registry.load_errors == []


@pytest.mark.parametrize("comic_id", BUNDLED)
def test_bundled_comic_is_valid(comic_id):
    comic_dir = COMICS_DIR / comic_id
    assert validate_comic_dir(comic_dir) == []

    config = StaticConfig.load_from_directory(comic_dir)
    # Both languages are offered in the UI
    assert config.blueprint.title and config.blueprint.title_no
    assert config.blueprint.synopsis and config.blueprint.synopsis_no
    # The opening state can be built without any API call
    state = ComicState.initialize_from_config(config)
    assert state.main_character_name == config.blueprint.characters[0].name


def test_registry_reads_metadata_and_font(tmp_path):
    write_comic(tmp_path, "good", {**MINIMAL_BLUEPRINT, "title_no": "Testserie"}, {"panel_font": "'Comic Neue'"})
    info = ComicRegistry(comics_dir=tmp_path).get_available_comics()[0]
    assert (info.id, info.name, info.name_no, info.panel_font) == ("good", "Test Comic", "Testserie", "'Comic Neue'")


def test_registry_skips_archive_and_broken_comics(tmp_path):
    write_comic(tmp_path, "good", MINIMAL_BLUEPRINT)
    write_comic(tmp_path, "broken", "{ not json")
    write_comic(tmp_path / "archive", "old", MINIMAL_BLUEPRINT)

    registry = ComicRegistry(comics_dir=tmp_path)
    assert [c.id for c in registry.get_available_comics()] == ["good"]
    assert len(registry.load_errors) == 1 and registry.load_errors[0].startswith("broken")


@pytest.mark.parametrize("comic_id", ["../comics/good", "archive", "archive/old", "missing", "", "/etc"])
def test_only_discovered_comics_can_be_loaded(tmp_path, comic_id):
    write_comic(tmp_path, "good", MINIMAL_BLUEPRINT)
    write_comic(tmp_path / "archive", "old", MINIMAL_BLUEPRINT)
    registry = ComicRegistry(comics_dir=tmp_path)
    assert registry.get_comic_config_dir("good") == tmp_path / "good"
    assert registry.get_comic_config_dir(comic_id) is None


def test_validation_reports_missing_characters_and_bad_fields(tmp_path):
    no_characters = {**MINIMAL_BLUEPRINT, "characters": []}
    assert "character" in validate_comic_dir(write_comic(tmp_path, "a", no_characters))[0]

    missing_title = {k: v for k, v in MINIMAL_BLUEPRINT.items() if k != "title"}
    assert "ValidationError" in validate_comic_dir(write_comic(tmp_path, "b", missing_title))[0]

    bad_config = write_comic(tmp_path, "c", MINIMAL_BLUEPRINT, {"llm_temperature": "hot"})
    assert "ValidationError" in validate_comic_dir(bad_config)[0]
