# Architecture

Comic Chaos is a small Flask app with a single-page vanilla-JavaScript frontend.
A comic is a loop: the story model plans the next panel, an image model paints
it with an empty bubble, OpenCV finds that bubble, and the reader types into it.

```
                 ┌──────────── browser (templates/index.html) ────────────┐
                 │ pick comic → type into bubble → watch panel stream in  │
                 └───────┬──────────────────────────────▲─────────────────┘
          POST JSON      │                              │  Server-Sent Events
                         ▼                              │  (init / partial / complete …)
 app.py ── routes, session cache + JSON checkpoints ────┤
   │                                                    │
   └─ ComicSession (src/comic_session.py) ──────────────┘
        ├─ Narratron (src/narratron/)       story model → next panel(s) as structured JSON
        ├─ ImageGenerator (src/image_gen/)  image model → streamed partial + final PNG
        │    └─ PanelDetector               OpenCV: locate the empty bubble / narration box
        ├─ ComicState (src/state/)          rolling summary, recent panels, render state
        └─ ComicStrip (src/comic_strip.py)  on finish: TextRenderer draws text, panels → one PNG
```

## Request flow

| Route | What happens | Paid calls |
|---|---|---|
| `GET /` | Serves `templates/index.html` (HTML, CSS and JS in one file). | — |
| `GET /api/comics` | Lists comics discovered in `comics/`. | — |
| `GET /api/status` | `{"api_available": bool, "reason"?}`. Reports a missing key or `API_ENABLED=false`. | — |
| `POST /api/start-stream` | Creates a `ComicSession`, streams the title card and the first interactive panel. | 1 LLM + 2+ images |
| `POST /api/submit-stream` | Records the reader's text, asks Narratron for the next panel(s), streams them. | 1 LLM + 1–2+ images |
| `POST /api/finish` | Rebuilds the strip from stored panels, renders text into bubbles, returns a base64 PNG. | — |

Streaming endpoints return `text/event-stream`. Each `data:` line is a JSON
event. The types are `init_title_card`, `complete_title_card`, `init`,
`init_auto`, `partial` (low-resolution preview), `complete`, `complete_auto`
and `error`. *Auto* panels are transition panels with pre-filled text; the
last panel of every turn is interactive.

The browser generates a random `session_id` and sends it with every request.
The server accepts only `[A-Za-z0-9_-]{16,128}`.

## Components

- **`app.py`**: Flask routes, rate limits (Flask-Limiter, in memory), and the
  session cache. After each panel the session is written to
  `output/sessions/<id>.json` (versioned JSON, written atomically). Another
  worker or a restarted server can then continue it, and `get_session` merges
  in a newer checkpoint if one exists. Idle sessions expire after an hour.
- **`main.py`**: entry point. Reads `HOST`/`PORT`/`DEBUG`, prints configuration
  problems, runs Flask's built-in server. `python main.py --check` runs the
  offline checks only.
- **`src/config.py`**: project-root paths, `.env` loading, API-key detection,
  and `check_config()`.
- **`src/comic_session.py`**: orchestrates one comic. Keeps `panels_data` (image
  bytes, elements, the reader's text, detected bubbles) and rolls back a turn if
  image generation fails, so the reader can try different words.
- **`src/narratron/`**: the story engine. Builds prompts from
  `src/prompts/*.md` (Python `str.format` templates, so literal braces are
  doubled), calls the chat model with Structured Outputs, and falls back to
  JSON mode and then to repair (`src/json_sanitizer.py`). If everything fails it
  uses a safe fallback panel and logs the error. `models.py` enforces at most two
  panels per turn, the last one interactive.
- **`src/image_gen/image_generator.py`**: builds the image prompt (style,
  setting, characters, and an instruction for *one empty bubble*), streams
  partial images, and regenerates once if no bubble is detected.
- **`src/image_gen/panel_detector.py`**: OpenCV thresholding and contour
  filtering. Round shapes are speech and thought bubbles; rectangles are
  narration boxes. Area limits assume 1024×1024 images.
- **`src/image_gen/text_renderer.py`**: Pillow. Fits and wraps text into a
  detected region, or draws a fallback bubble. Uses the bundled Comic Neue font.
- **`src/comic_strip.py`**: lays panels out three per row, styled like the web UI.
- **`src/state/`**: Pydantic models. `static_config.py` holds `Blueprint` and
  `ComicConfig` (with the model defaults) plus `validate_comic_dir`;
  `comic_state.py` holds the evolving story state.
- **`comics/`**: one directory per comic, discovered by `comic_registry.py`.
  `comics/archive/` is ignored.
- **`templates/index.html`**: the whole UI, including the English/Norwegian
  strings (`translations`). The browser renders bubbles over the live image,
  while the downloadable strip is rendered server-side.

## Design notes and limits

- **Single-user by design.** No accounts, and sessions are addressed only by the
  browser-generated ID. See [self-hosting](self-hosting.md#exposing-it-beyond-your-computer).
- **Bubble detection depends on the image model drawing a clean white bubble.**
  When detection fails twice, text is drawn in a programmatic bubble instead.
- **Language** is `no` (Norwegian Bokmål, the default) or `en`. Internal
  fields such as scene descriptions stay in English for consistent image prompts.
