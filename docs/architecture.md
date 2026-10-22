# Architecture

Comic Chaos is a small Flask app with a single-page vanilla-JavaScript frontend.
A comic is a loop: the story model plans the next panel, an image model paints
it with an empty bubble, OpenCV finds that bubble, and the reader types into it.

All code lives in the `comic_chaos/` package, and code paths below are relative to it.
Comic definitions live in the top-level `comics/` folder.

```
                 ┌──────────── browser (templates/index.html) ────────────┐
                 │ pick comic → type into bubble → watch panel stream in  │
                 └───────┬──────────────────────────────▲─────────────────┘
          POST JSON      │                              │  Server-Sent Events
                         ▼                              │  (init / partial / complete …)
 app.py ── routes, in-memory sessions ─────────────────┤
   │                                                    │
   └─ ComicSession (comic_session.py) ──────────────────┘
        ├─ Narratron (narratron/)           story model → next panel(s) as structured JSON
        ├─ ImageGenerator (image_gen/)      image model → streamed partial + final PNG
        │    └─ PanelDetector               OpenCV: locate the empty bubble / narration box
        ├─ ComicState (state/)              rolling summary, recent panels, render state
        └─ ComicStrip (comic_strip.py)      on finish: TextRenderer draws text, panels → one PNG
```

## Request flow

| Route | What happens | Paid calls |
|---|---|---|
| `GET /` | Serves `templates/index.html` (HTML, CSS and JS in one file). | — |
| `GET /api/comics` | Lists comics discovered in `comics/`. | — |
| `GET /api/status` | `{"api_available": bool, "reason"?}`. Reports a missing key. | — |
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

- **`app.py`**: Flask routes and the sessions, held in memory by the one
  server process. Idle sessions expire after an hour; a restarted server
  forgets them.
- **`__main__.py`**: entry point (`python -m comic_chaos`). Reads `PORT`,
  prints configuration problems, and runs Flask's built-in server on
  `127.0.0.1`. `python -m comic_chaos --check` runs the offline checks only.
- **`config.py`**: project-root paths, `.env` loading, API-key detection,
  and `check_config()`.
- **`comic_session.py`**: orchestrates one comic. Keeps `panels_data` (image
  bytes, elements, the reader's text, detected bubbles) and rolls back a turn if
  image generation fails, so the reader can try different words.
- **`narratron/`**: the story engine. Builds prompts from
  `prompts/*.md` (Python `str.format` templates, so literal braces are
  doubled) and calls the chat model with Structured Outputs. If a call fails
  or the model refuses, it logs the error and uses a safe fallback panel.
  `models.py` enforces at most two panels per turn, the last one interactive.
  `text_sanitizer.py` cleans the reader's text and the model's.
- **`image_gen/image_generator.py`**: builds the image prompt (style,
  setting, characters, and an instruction for *one empty bubble*), streams
  partial images, and regenerates once if no bubble is detected.
- **`image_gen/panel_detector.py`**: OpenCV thresholding and contour
  filtering. Round shapes are speech and thought bubbles; rectangles are
  narration boxes. Area limits assume 1024×1024 images.
- **`image_gen/text_renderer.py`**: Pillow. Fits and wraps text into a
  detected region, or draws a fallback bubble. Uses the bundled Comic Neue font.
- **`comic_strip.py`**: lays panels out three per row, styled like the web UI.
- **`state/`**: Pydantic models. `static_config.py` holds `Blueprint` and
  `ComicConfig` (with the model defaults) plus `validate_comic_dir`;
  `comic_state.py` holds the evolving story state.
- **`comic_registry.py`**: discovers the comics in the top-level `comics/`
  folder, one directory per comic. `comics/archive/` is ignored.
- **`templates/index.html`**: the whole UI, including the English/Norwegian
  strings (`translations`). The browser renders bubbles over the live image,
  while the downloadable strip is rendered server-side.

## Design notes and limits

- **Local and single-user by design.** No accounts, it listens on `127.0.0.1`
  only, and sessions are addressed only by the browser-generated ID.
- **Bubble detection depends on the image model drawing a clean white bubble.**
  When detection fails twice, text is drawn in a programmatic bubble instead.
- **Language** is `no` (Norwegian Bokmål, the default) or `en`. Internal
  fields such as scene descriptions stay in English for consistent image prompts.
