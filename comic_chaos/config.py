"""Central configuration: paths, the API key, and startup checks.

Model settings (LLM/image model, reasoning effort, quality, font) are the
``ComicConfig`` defaults in ``comic_chaos/state/static_config.py``; a comic can
override them in its own ``config.json``.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Anchored to the project root, so the app works from any directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMICS_DIR = PROJECT_ROOT / "comics"

# Values from a project-root .env file. Variables already set in the real
# environment take precedence over the file.
load_dotenv(PROJECT_ROOT / ".env")

HOST = "127.0.0.1"  # Loopback only: the app has no login, and every comic is billed to the key
DEFAULT_PORT = 5000  # Overridable with the PORT environment variable


def get_openai_api_key() -> str | None:
    """Return the configured OpenAI API key, or None if it is missing."""
    return os.getenv("OPENAI_API_KEY", "").strip() or None


def check_config() -> list[str]:
    """Run offline configuration checks. Never contacts the OpenAI API.

    Returns:
        Problems that prevent comic generation (empty = OK).
    """
    errors: list[str] = []

    if get_openai_api_key() is None:
        errors.append(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and put your own key on the "
            "OPENAI_API_KEY line (https://platform.openai.com/api-keys). "
            "The UI still starts, but comics cannot be generated without a key."
        )

    from .comic_registry import ComicRegistry
    from .state.static_config import validate_comic_dir

    registry = ComicRegistry(comics_dir=COMICS_DIR)
    if not registry.get_available_comics():
        errors.append(f"No comics found: expected {COMICS_DIR}/<comic_id>/blueprint.json.")
    for comic in registry.get_available_comics():
        errors.extend(validate_comic_dir(registry.get_comic_config_dir(comic.id)))
    errors.extend(registry.load_errors)

    return errors
