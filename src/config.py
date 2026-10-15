"""Central configuration: paths, runtime settings, and startup checks.

Per-comic model settings (LLM/image model, quality, temperature, font) live in
each comic's ``config.json``; their defaults are defined by ``ComicConfig`` in
``src/state/static_config.py``.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# =============================================================================
# Paths (anchored to the project root, so the app works from any directory)
# =============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

COMICS_DIR = PROJECT_ROOT / "comics"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = OUTPUT_DIR / "logs"
SESSIONS_DIR = OUTPUT_DIR / "sessions"  # JSON session checkpoints

# Values from a project-root .env file. Variables already set in the real
# environment take precedence over the file.
load_dotenv(PROJECT_ROOT / ".env")

# =============================================================================
# Logging
# =============================================================================
ENABLE_LOGGING = False  # Set to True to log all LLM interactions to JSON files in LOGS_DIR

# =============================================================================
# Server defaults (overridable with the HOST / PORT environment variables)
# =============================================================================
DEFAULT_HOST = "127.0.0.1"  # Loopback only: the app has no authentication
DEFAULT_PORT = 5000

# =============================================================================
# Optional environment overrides for the per-comic model settings
# =============================================================================
MODEL_ENV_OVERRIDES = {
    "llm_model": "COMIC_CHAOS_LLM_MODEL",
    "image_model": "COMIC_CHAOS_IMAGE_MODEL",
}

# Values that mean "not configured" (e.g. the untouched .env.example template)
_PLACEHOLDER_API_KEYS = {"your_openai_api_key_here", "your-api-key-here", "sk-..."}


def get_openai_api_key() -> str | None:
    """Return the configured OpenAI API key, or None if missing or a placeholder."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key in _PLACEHOLDER_API_KEYS:
        return None
    return key


def is_api_enabled() -> bool:
    """Return False when generation is switched off with API_ENABLED=false."""
    return os.getenv("API_ENABLED", "true").strip().lower() == "true"


def check_config() -> tuple[list[str], list[str]]:
    """Run offline configuration checks. Never contacts the OpenAI API.

    Returns:
        (errors, warnings) — errors prevent comic generation entirely.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if get_openai_api_key() is None:
        errors.append(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and put your own key "
            "on the OPENAI_API_KEY line (https://platform.openai.com/api-keys). "
            "The UI still starts, but comics cannot be generated without a key."
        )

    if not is_api_enabled():
        warnings.append("API_ENABLED=false — comic generation is switched off.")

    from comics.comic_registry import ComicRegistry
    from src.state.static_config import validate_comic_dir

    registry = ComicRegistry(comics_dir=COMICS_DIR)
    if not registry.get_available_comics():
        errors.append(f"No comics found: expected {COMICS_DIR}/<comic_id>/blueprint.json.")
    for comic in registry.get_available_comics():
        errors.extend(validate_comic_dir(registry.get_comic_config_dir(comic.id)))
    errors.extend(registry.load_errors)

    for field, env_var in MODEL_ENV_OVERRIDES.items():
        if os.getenv(env_var):
            warnings.append(f"{env_var} is set: every comic uses {field}={os.getenv(env_var)}.")

    return errors, warnings
