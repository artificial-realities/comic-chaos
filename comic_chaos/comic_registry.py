"""Comic registry for managing multiple comics."""

import json
from pathlib import Path
from pydantic import BaseModel, Field

from .state.static_config import ComicConfig

ARCHIVE_DIR_NAME = "archive"


class ComicInfo(BaseModel):
    """Metadata about a registered comic."""

    id: str = Field(description="Unique comic identifier (directory name)")
    name: str = Field(description="Display name")
    name_no: str = Field(default="", description="Display name in Norwegian")
    description: str = Field(description="Brief description")
    description_no: str = Field(default="", description="Brief description in Norwegian")
    style: str = Field(description="Visual style description")
    panel_font: str = Field(description="CSS font-family for in-panel text")


class ComicRegistry:
    """Registry for discovering and managing multiple comics."""

    def __init__(self, comics_dir: str | Path = "comics"):
        self.comics_dir = Path(comics_dir)
        self._comics: dict[str, ComicInfo] = {}
        self.load_errors: list[str] = []
        self._discover_comics()

    def _discover_comics(self) -> None:
        """Discover all available comics."""
        if not self.comics_dir.exists():
            return

        for comic_path in self.comics_dir.iterdir():
            if comic_path.is_dir() and comic_path.name != ARCHIVE_DIR_NAME:
                blueprint_file = comic_path / "blueprint.json"
                if blueprint_file.exists():
                    try:
                        self._register_comic(comic_path, blueprint_file)
                    except (OSError, ValueError) as e:
                        # One broken comic should not hide the others
                        self.load_errors.append(f"{comic_path.name}: {type(e).__name__}: {e}")
                        print(f"[COMICS] Skipping '{comic_path.name}': {e}")

    def _register_comic(self, comic_path: Path, blueprint_file: Path) -> None:
        # Load info from blueprint
        with open(blueprint_file, encoding="utf-8") as f:
            bp_data = json.load(f)
        if not isinstance(bp_data, dict):
            raise ValueError("blueprint.json must contain a JSON object")

        name_no = bp_data.get("title_no", "")
        description_no = bp_data.get("synopsis_no", "")

        # Load panel font from config.json if present
        panel_font = ComicConfig().panel_font
        config_file = comic_path / "config.json"
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                cfg_data = json.load(f)
            panel_font = cfg_data.get("panel_font", panel_font)

        self._comics[comic_path.name] = ComicInfo(
            id=comic_path.name,
            name=bp_data.get("title", comic_path.name),
            name_no=name_no,
            description=bp_data.get("synopsis", "No description"),
            description_no=description_no,
            style=bp_data.get("visual_style", "comic book style"),
            panel_font=panel_font,
        )

    def get_available_comics(self) -> list[ComicInfo]:
        """Get list of all available comics."""
        return list(self._comics.values())

    def get_comic_config_dir(self, comic_id: str) -> Path | None:
        """Get the config directory for a discovered comic (None for unknown IDs)."""
        if comic_id not in self._comics:
            return None
        return self.comics_dir / comic_id
