# AGENTS.md: working on Comic Chaos

Project facts and rules for coding agents (and humans). Read this before changing
anything. How it works is in [docs/architecture.md](docs/architecture.md).

## What this is

Comic Chaos is an interactive comic creator. The reader picks a comic, types
into an empty speech, thought or narration bubble, and the next panel is
written by an OpenAI chat model ("Narratron") and painted by an OpenAI image
model. OpenCV finds the empty bubble in each generated image, Pillow renders
text into it, and the finished strip downloads as a PNG. The stack is Flask with
Server-Sent Events plus one vanilla-JS page, with English and Norwegian (Bokmål)
UIs. It runs locally, one process, for the people at the keyboard.

Development is on pause; it's published by Artificial Realities. Keep changes
small and keep the existing experience intact.

## Repository map

All code lives in the `comic_chaos/` package; `comics/` holds data only.

```
comic_chaos/
  __main__.py               entry point: python -m comic_chaos [--check]
  app.py                    Flask routes, in-memory sessions (expire after an hour)
  config.py                 paths, .env loading, API-key detection, check_config()
  comic_session.py          one comic: orchestrates Narratron, images, state, strip
  comic_registry.py         comic discovery
  narratron/                story engine (narratron.py) and response models/schemas (models.py)
  prompts/*.md              prompt templates (Python str.format: literal braces must be doubled)
  image_gen/                image_generator.py (OpenAI images), panel_detector.py (OpenCV),
                            text_renderer.py (Pillow)
  comic_strip.py            final strip assembly
  state/                    static_config.py (Blueprint, ComicConfig with the model settings,
                            validate_comic_dir), comic_state.py (story state)
  text_sanitizer.py         cleans user and model text (null bytes, invisible characters)
  templates/index.html      the entire frontend, including EN/NO strings (`translations`)
  static/                   fonts (Comic Neue, OFL) and UI images
comics/<id>/                blueprint.json (+ optional config.json); comics/archive/ is ignored
tests/                      offline pytest suite; tests/helpers.py has synthetic images and an SSE parser
docs/                       architecture.md
.github/workflows/ci.yml    ruff + pytest
```

## Commands

Run everything from the repository root inside a virtual environment.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt     # runtime + pytest + ruff (pinned)
python -m comic_chaos --check           # offline config/blueprint validation; exit 1 if no key or a broken comic
python -m pytest                        # offline test suite (blocks network access, needs no key)
ruff check .                            # lint (rules in pyproject.toml)
python -m comic_chaos                   # serve on http://127.0.0.1:5000 (PORT to change)
```

Supported Python: 3.11–3.14; CI runs Ruff and pytest on 3.13. There is no
formatter or type checker configured; don't reformat files you aren't changing.

## Secrets and configuration

- The only secret is `OPENAI_API_KEY`, read from the environment or from `.env`
  in the repo root (`cp .env.example .env`). `.env` is git-ignored.
- **Never print, log, commit, echo or paste the key or the contents of `.env`.**
  Don't open `.env` to "check" it. Use `python -m comic_chaos --check`, which reports
  only whether a key is configured. If no key is set, tell the human to create
  one at <https://platform.openai.com/api-keys> and put it in `.env` themselves.
  Never ask them to paste it into chat.
- The only other variable is `PORT` (default 5000). If you add one, update
  `.env.example` and this file.
- Model settings are the `ComicConfig` defaults in `comic_chaos/state/static_config.py`;
  a comic can override them in `comics/<id>/config.json`. Don't switch models
  without the owner's agreement and a real test.

## Paid API calls: rules

Starting a comic or submitting a bubble calls OpenAI and costs money (a story
request plus one or more images).

- **Never call the OpenAI API, or start/submit a comic, without the human's explicit
  permission for that run.** Tests, CI and `--check` must stay offline.
- New tests must not make network calls. The `offline` fixture in
  `tests/conftest.py` makes any socket connection fail. Fake model calls with
  `monkeypatch`, as in `tests/test_generation_mocked.py`.
- A real end-to-end check (start a comic in the browser, submit two bubbles,
  finish, download) needs the human's key, their go-ahead, and their attention.
  Report it as untested otherwise.

## Verifying changes without paid calls

1. `ruff check .` and `python -m pytest` must pass.
2. `python -m comic_chaos --check` with no key should exit 1 and name `OPENAI_API_KEY`.
3. UI smoke test with no key:
   `OPENAI_API_KEY= PORT=5055 python -m comic_chaos`, then
   `curl -s localhost:5055/api/status` → `{"api_available":false,"reason":"missing_api_key"}`,
   `curl -s localhost:5055/api/comics` lists the comics, and `/` loads. The comic
   picker shows a missing-key notice. (An empty `OPENAI_API_KEY` in the real
   environment overrides `.env`.)
4. For frontend logic, `tests/test_generation_mocked.py` drives a whole comic
   through the real routes with fakes. Extend it rather than calling OpenAI.

## Adding or editing a comic

1. Create `comics/<comic_id>/` (lowercase, underscores; the directory name is the ID).
2. `blueprint.json`: required `title` and `synopsis`. Also give it at least one
   entry in `locations` (the first is where the story starts) and in
   `characters` (the first is the hero). Optional: `title_no`, `synopsis_no`
   (Norwegian UI text), `visual_style`, `rules`, `long_term_narrative`,
   `narrative_premise`. The schema is `Blueprint` in `comic_chaos/state/static_config.py`;
   copy an existing comic as a template.
3. Optional `config.json`: any `ComicConfig` field to override.
4. Validate with `python -m comic_chaos --check` and `python -m pytest`
   (`tests/test_comics.py` validates every bundled comic). The picker has
   bubbles for three comics; a fourth needs a new bubble in `comic_chaos/templates/index.html`.

## Code style and constraints

- Keep the stack: Flask, Server-Sent Events, vanilla JS in the single
  `comic_chaos/templates/index.html`, Pydantic v2 models. No new frameworks, build steps,
  databases or services.
- Match the surrounding code: type hints on signatures, docstrings on public
  functions, `print("[AREA] ...")` for server logs (there is no logging
  framework), 120-character lines.
- UI strings exist in both languages in `translations` in `comic_chaos/templates/index.html`.
- Text from users or models must go through `escapeHtml` before `innerHTML`.
- Narratron uses Structured Outputs only; when a call fails it logs the error and
  shows a fallback panel. Don't add JSON repair or parsing fallbacks.
- Don't rename modules, comic IDs, routes or SSE event types without need.

## Safety rules

- **Network exposure:** the app listens on `127.0.0.1` only. Never change that
  or document public hosting as safe. The app has no authentication, so anyone
  who can reach it spends the owner's API credit.
- **Filesystem:** the app writes nothing to disk. Client-supplied values
  (session IDs, comic IDs) must never become paths without validation
  (`is_valid_session_id`, `ComicRegistry.get_comic_config_dir`).
- Don't add telemetry or third-party calls.

## Definition of done

- Focused diff that does one thing, with no unrelated reformatting.
- `ruff check .` and `python -m pytest` pass, with tests added for new behaviour.
- No secrets in code, logs, test fixtures or commit messages, and no paid API
  calls made unless the human authorised them.
- Docs updated when behaviour, configuration or setup changes: README.md,
  docs/, `.env.example`, and this file.
- State plainly what was verified and what wasn't (for example "UI tested
  offline; generation not run").
