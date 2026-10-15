# AGENTS.md: working on Comic Chaos

Project facts and rules for coding agents (and humans). Read this before changing
anything. Details live in [docs/architecture.md](docs/architecture.md) and
[docs/self-hosting.md](docs/self-hosting.md).

## What this is

Comic Chaos is an interactive comic creator. The reader picks a comic, types
into an empty speech, thought or narration bubble, and the next panel is
written by an OpenAI chat model ("Narratron") and painted by an OpenAI image
model. OpenCV finds the empty bubble in each generated image, Pillow renders
text into it, and the finished strip downloads as a PNG. The stack is Flask with
Server-Sent Events plus one vanilla-JS page, with English and Norwegian (Bokmål)
UIs.

Development is on pause while the team works on other projects. It's
published by Artificial Realities. Keep changes small and keep the existing
experience intact.

## Repository map

```
main.py                     entry point: python main.py [--check]
app.py                      Flask routes, rate limits, session cache + JSON checkpoints
src/config.py               paths, .env loading, API-key detection, check_config()
src/comic_session.py        one comic: orchestrates Narratron, images, state, strip
src/narratron/              story engine (narratron.py) and response models/schemas (models.py)
src/prompts/*.md            prompt templates (Python str.format: literal braces must be doubled)
src/image_gen/              image_generator.py (OpenAI images), panel_detector.py (OpenCV),
                            text_renderer.py (Pillow)
src/comic_strip.py          final strip assembly
src/state/                  static_config.py (Blueprint, ComicConfig, validate_comic_dir),
                            comic_state.py (story state)
src/json_sanitizer.py       cleaning and repair of model JSON
src/logging/                optional prompt/response logging (off: ENABLE_LOGGING in src/config.py)
comics/<id>/                blueprint.json (+ optional config.json); comics/archive/ is ignored
comics/comic_registry.py    comic discovery
templates/index.html        the entire frontend, including EN/NO strings (`translations`)
static/                     fonts (Comic Neue, OFL) and UI images
tests/                      offline pytest suite; tests/helpers.py has synthetic images and an SSE parser
output/                     runtime data (git-ignored): sessions/, logs/
```

## Commands

Run everything from the repository root inside a virtual environment.

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: py -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt                  # runtime + pytest + ruff (pinned)
python main.py --check      # offline config/blueprint validation; exit 1 if no key or a broken comic
python -m pytest            # offline test suite (blocks network access, needs no key)
ruff check .                # lint (rules in pyproject.toml)
python main.py              # serve on http://127.0.0.1:5000 (HOST/PORT to change)
docker compose up --build   # container alternative (needs .env)
```

Supported Python: 3.11–3.14. CI (`.github/workflows/ci.yml`) runs Ruff and
pytest on 3.11 and 3.14, then builds and smoke-tests the Docker image. There is
no formatter or type checker configured; don't reformat files you aren't
changing.

## Secrets and configuration

- The only secret is `OPENAI_API_KEY`, read from the environment or from `.env`
  in the repo root (`cp .env.example .env`). `.env` is git-ignored and excluded
  from Docker builds.
- **Never print, log, commit, echo or paste the key or the contents of `.env`.**
  Don't open `.env` to "check" it. Use `python main.py --check`, which reports
  only whether a key is configured. If no key is set, tell the human to create
  one at <https://platform.openai.com/api-keys> and put it in `.env` themselves.
  Never ask them to paste it into chat.
- Other variables: `HOST` (default `127.0.0.1`), `PORT` (5000), `API_ENABLED`,
  `DEBUG`, `COMIC_CHAOS_LLM_MODEL`, `COMIC_CHAOS_IMAGE_MODEL`. See the table in
  [docs/self-hosting.md](docs/self-hosting.md#configuration). If you add one,
  update `.env.example` and that table.
- Per-comic model settings live in `comics/<id>/config.json`; defaults are in
  `ComicConfig`. The models in use are scheduled for retirement by OpenAI (see
  [Model retirement](docs/self-hosting.md#model-retirement)). Don't switch models
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
2. `python main.py --check` with no key should exit 1 and name `OPENAI_API_KEY`.
3. UI smoke test with no key:
   `OPENAI_API_KEY= PORT=5055 python main.py`, then
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
   `narrative_premise`. The schema is `Blueprint` in `src/state/static_config.py`;
   copy an existing comic as a template.
3. Optional `config.json`: any `ComicConfig` field (`llm_model`,
   `llm_temperature`, `llm_top_p`, `llm_max_tokens`, `image_model`,
   `image_size`, `image_quality`, `image_moderation`, `panel_font`).
4. Validate with `python main.py --check` and `python -m pytest`
   (`tests/test_comics.py` validates every bundled comic). The picker has
   bubbles for three comics; a fourth needs a new bubble in `templates/index.html`.

## Code style and constraints

- Keep the stack: Flask, Server-Sent Events, vanilla JS in the single
  `templates/index.html`, Pydantic v2 models. No new frameworks, build steps,
  databases or services.
- Match the surrounding code: type hints on signatures, docstrings on public
  functions, `print("[AREA] ...")` for server logs (there is no logging
  framework), 120-character lines.
- UI strings exist in both languages in `translations` in `templates/index.html`.
- Text from users or models must go through `escapeHtml` before `innerHTML`.
- Don't rename modules, comic IDs, routes, SSE event types or the checkpoint
  format without need. If the checkpoint format changes, bump
  `CHECKPOINT_VERSION` in `app.py`.

## Safety rules

- **Network exposure:** default to `127.0.0.1`. Never change defaults to listen
  publicly, and don't document public hosting as safe. The app has no
  authentication, so anyone who can reach it spends the owner's API credit.
- **Filesystem:** the app writes only under `output/`. Client-supplied values
  (session IDs, comic IDs) must never become paths without validation
  (`is_valid_session_id`, `ComicRegistry.get_comic_config_dir`).
- **Session data:** checkpoints contain what people typed and their panels. Keep
  them in `output/sessions/`. Never use `pickle` or other code-executing
  formats for them.
- Don't add telemetry or third-party calls.

## Troubleshooting

See the table in [docs/self-hosting.md](docs/self-hosting.md#troubleshooting).
The usual suspects are a missing key (`--check`), a busy port (`PORT=5050`), an
unsupported Python version, or a retired model, which shows as
`[NARRATRON] ... failed` or `model_not_found` in the server log.

## Definition of done

- Focused diff that does one thing, with no unrelated reformatting.
- `ruff check .` and `python -m pytest` pass, with tests added for new behaviour.
- No secrets in code, logs, test fixtures or commit messages, and no paid API
  calls made unless the human authorised them.
- Docs updated when behaviour, configuration or setup changes: README.md,
  docs/, `.env.example`, and this file.
- State plainly what was verified and what wasn't (for example "UI tested
  offline; generation not run").
