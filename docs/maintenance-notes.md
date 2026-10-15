# Maintenance notes

What changed when Comic Chaos was prepared for open source under Artificial
Realities (October 2026), why, and what is still open. Useful background for
anyone picking the project up later.

## Decisions

| Area | Before | Now | Why |
|---|---|---|---|
| Default address | `0.0.0.0` | `127.0.0.1` (`HOST` to change) | No authentication, and every comic is billed to the key owner |
| Session checkpoints | `pickle` in shared `/tmp/comic_chaos_sessions`, file name from the client's session ID | Versioned JSON in private `output/sessions/`, IDs validated, atomic writes, age-based cleanup | Loading pickle runs code; unvalidated IDs allowed path traversal |
| Comic lookup | `comics/<anything>` joined unchecked | Only comics found by the registry | Path traversal; archived comics were loadable |
| Paths | Relative to the working directory | Anchored to the project root | App showed no comics when started from elsewhere |
| Hosting files | `Procfile` (Railway) | Removed; the gunicorn command is in `docs/self-hosting.md` | The hosted demo is offline, and public hosting isn't supported |
| Config check | none | `python main.py --check`, missing-key notice in the UI | Clear first-run errors without calling OpenAI |
| Model choice | per comic only | plus `COMIC_CHAOS_LLM_MODEL` / `COMIC_CHAOS_IMAGE_MODEL` | Lets self-hosters move off retired models without editing comics |
| Narratron errors | swallowed silently | logged as `[NARRATRON] ... failed` | A retired model or a bad key otherwise just yields endless fallback panels |
| Frontend text | inserted into `innerHTML` raw | escaped | HTML injection from user or model text |
| Dependencies | lower bounds only (`openai>=1.0` was wrong) | bounded ranges | Image streaming needs `openai>=1.97` |

The defaults for models, prompts, comics and creative behaviour were not changed.

## Verified (14 October 2026)

- Offline test suite (`python -m pytest`) passes on Python 3.10, 3.11, 3.12, 3.13
  and 3.14 with the newest allowed dependencies, and on 3.11 with the **lowest**
  allowed versions (`uv pip install --resolution lowest-direct`).
- Prebuilt wheels exist for every dependency on Windows x64, macOS arm64, and
  macOS x86_64 12+.
- UI and API start and serve without a key, from any working directory, with a
  read-only code directory (only `output/` writable).
- Gunicorn with two gevent workers, plus two separate server processes sharing
  `output/sessions/`, carried one comic across processes (with faked models).
- The real UI, driven in headless Chromium through a whole comic with faked
  models: missing-key notice, streamed panels, HTML typed into a bubble shown
  as plain text, finished strip. No page or console errors.
- No secrets in tracked files or in git history (pattern scan; `.env` was never committed).

## Not verified

- **Real generation against OpenAI** after these changes. No paid calls were
  made. The OpenAI call sites are unchanged, and the SDK signatures were checked
  on `openai` 1.97 and 3.31.
- **Docker** on a real host. CI builds the image and checks it starts without a key.
- **Native Windows and macOS** runs (only wheel availability was checked).

## Known limitations and risks

- **Model retirement:** `gpt-image-1.5` and `gpt-image-1-mini` shut down on
  2026-12-01, and `gpt-4.1` and `gpt-4o-mini` on 2027-01-14. Replacements are
  untested and may reject parameters such as `temperature`, `top_p`,
  `max_tokens`, `moderation` or `partial_images`.
- **No authentication or per-user budget.** Flask-Limiter (in-memory, per IP,
  per process) is a guard rail, not cost control.
- Sessions are addressed by a browser-generated random ID. Anyone who learns the
  ID can continue or finish that comic.
- `get_session` re-reads the whole checkpoint (including images) on every
  request. That's fine for a few users and wasteful for many.
- The comic picker has room for three comics. Their order follows the
  filesystem's directory order.
- Model error messages are printed to the server log and passed to the browser
  in SSE `error` events. The UI shows only a friendly message. OpenAI masks keys
  in its error messages.
