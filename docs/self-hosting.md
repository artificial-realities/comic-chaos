# Running Comic Chaos yourself

Comic Chaos is designed to run on your own computer, for you and the people at
your keyboard. This page covers installation, configuration, costs, Docker, and
troubleshooting. The [README](../README.md) has the short version.

- [Requirements](#requirements)
- [Install and run (Python)](#install-and-run-python)
- [Run with Docker](#run-with-docker)
- [Configuration](#configuration)
- [Models and costs](#models-and-costs)
- [What is stored on disk](#what-is-stored-on-disk)
- [Exposing it beyond your computer](#exposing-it-beyond-your-computer)
- [Troubleshooting](#troubleshooting)

## Requirements

- **Python 3.11–3.14.** The test suite passes on 3.11, 3.12, 3.13 and 3.14
  (and on 3.10, which reaches end of life in October 2026, so it isn't
  recommended).
- **An OpenAI API key** from <https://platform.openai.com/api-keys>, on an
  account with API credit. The UI loads without a key, but comics can't be
  generated.
- Windows (x64), Linux, or macOS (Apple Silicon, or Intel on macOS 12 or newer:
  older Intel Macs have no prebuilt OpenCV package).

## Install and run (Python)

**macOS / Linux**

```bash
git clone https://github.com/artificial-realities/comic-chaos.git
cd comic-chaos
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then open .env and paste your OpenAI API key
python main.py
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/artificial-realities/comic-chaos.git
cd comic-chaos
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then open .env and paste your OpenAI API key
python main.py
```

In Command Prompt, activate with `.venv\Scripts\activate.bat` and copy with
`copy .env.example .env`. If PowerShell refuses to run `Activate.ps1`, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once. (The Windows
commands follow standard Python conventions but haven't been tested on native
Windows by the maintainers; the Linux steps have, including under WSL.)

Then open <http://localhost:5000>. On start-up the server prints any
configuration problems, such as a missing key.

Check your setup at any time without starting the server or calling OpenAI:

```bash
python main.py --check
```

It confirms that a key is configured (not that OpenAI accepts it) and that every
comic's blueprint loads.

## Run with Docker

> The Docker files are new. CI builds the image and checks that it starts, but
> it hasn't yet been tried on a maintainer's own Docker host.

```bash
cp .env.example .env    # then paste your OpenAI API key into .env
docker compose up --build
```

Open <http://localhost:5000>. Stop it with `Ctrl+C`, or `docker compose down`.

- The key is read from `.env` when the container starts. It is never copied into
  the image (`.dockerignore` excludes `.env`).
- The port is published on `127.0.0.1` only, so other machines can't reach it.
  Inside the container the app listens on `0.0.0.0`, which is what makes the
  published port work.
- Nothing needs to persist between runs, so no volume is mounted. Finished
  comics are downloaded in the browser.

Without Compose:

```bash
docker build -t comic-chaos .
docker run --rm --env-file .env -e HOST=0.0.0.0 -p 127.0.0.1:5000:5000 comic-chaos
```

## Configuration

All settings are environment variables, usually set in `.env` in the project
root. Real environment variables take precedence over `.env`.

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | **Required to generate comics.** Billed for every comic. |
| `HOST` | `127.0.0.1` | Address `python main.py` listens on. See [exposing it](#exposing-it-beyond-your-computer). |
| `PORT` | `5000` | Port `python main.py` listens on. |
| `API_ENABLED` | `true` | `false` switches generation off; the UI still loads. |
| `COMIC_CHAOS_LLM_MODEL` | per comic | Use this story model for every comic. |
| `COMIC_CHAOS_IMAGE_MODEL` | per comic | Use this image model for every comic. |
| `DEBUG` | `false` | Flask debug mode with auto-reload. Refused unless `HOST` is loopback. |

The OpenAI Python SDK also honours its own standard variables, such as
`OPENAI_BASE_URL`, `OPENAI_ORG_ID` and `OPENAI_PROJECT_ID`.

Per-comic settings (models, quality, temperature, panel font) live in
`comics/<comic_id>/config.json`. See [Creating a comic](../README.md#create-your-own-comic).

## Models and costs

Every comic uses OpenAI's paid API. Each bundled comic's `config.json` selects:

| Purpose | Model | Settings |
|---|---|---|
| Story (Narratron) | `gpt-4.1` | temperature 0.8, top_p 0.9, max 2048 tokens |
| Panel art | `gpt-image-1.5` | 1024×1024, quality `medium`, streamed previews |

A comic without a `config.json` falls back to `gpt-4o-mini` and
`gpt-image-1-mini` at quality `low` (the `ComicConfig` defaults in
`src/state/static_config.py`).

**What gets billed:**

| Action | Requests |
|---|---|
| Start a comic | 1 story request + 2 images (title card and first panel) |
| Each bubble you submit | 1 story request + 1–2 images (sometimes an extra transition panel) |
| Finish / download | Nothing (the strip is assembled locally) |

Sometimes there are extra requests. If no empty bubble is detected in a new
panel, the image is generated once more. If the story model's reply can't be
parsed, it is retried up to twice. So a ten-turn comic means roughly 11 story
requests and 12–25 images. Images make up most of the cost. Prices change, so
check <https://openai.com/api/pricing/> and consider setting a monthly budget
limit in your OpenAI account. To spend less, set `image_quality` to `low` in a
comic's `config.json`, or point `COMIC_CHAOS_IMAGE_MODEL` at a cheaper model.

OpenAI may require your organization to be verified before it allows GPT Image
models or image streaming. If image requests are refused, check your
organization settings on the OpenAI platform.

### Model retirement

OpenAI has announced shutdown dates for the models Comic Chaos uses
([deprecations page](https://developers.openai.com/api/docs/deprecations),
checked 14 October 2026):

| Model | Shutdown | OpenAI's suggested replacement |
|---|---|---|
| `gpt-image-1.5`, `gpt-image-1-mini` | 1 December 2026 | `gpt-image-2.5-sunburst` or `gpt-image-2.5-flare` |
| `gpt-4.1`, `gpt-4o-mini` | 14 January 2027 | `gpt-6-luna` |

After those dates the configured models stop working. The replacements haven't
been tested with Comic Chaos. To try one, set `COMIC_CHAOS_IMAGE_MODEL` /
`COMIC_CHAOS_LLM_MODEL`, or edit the comics' `config.json`. Newer models may
reject parameters this app sends (for example `temperature`, `top_p`,
`max_tokens`, `moderation` or `partial_images`). Errors show up in the server
log.

## What is stored on disk

Everything the app writes goes under `output/` (ignored by git):

- `output/sessions/`: a JSON checkpoint per comic in progress (panels as
  base64 images, story state, and what you typed). It lets a second server
  worker, or a restarted server, continue a comic. The directory is private to
  your user. A checkpoint is deleted when you finish the comic. Abandoned ones
  are deleted after an hour, the next time a comic is started.
- `output/logs/`: full prompts and responses, only if you set
  `ENABLE_LOGGING = True` in `src/config.py`.

The server talks only to OpenAI. The page itself loads the Roboto Mono font from
Google Fonts.

## Exposing it beyond your computer

Comic Chaos has **no accounts, no login and no per-user budget**. Anyone who can
reach the server can start comics on your API key. Built-in rate limits (6 new
comics and 10 submissions per minute per IP address, held in memory per
process) slow down accidents. They are not cost control.

- On a trusted home network, `HOST=0.0.0.0 python main.py` makes it reachable from
  other devices. Only do this on networks you trust.
- On the public internet, put it behind real authentication (for example a
  reverse proxy with login) and HTTPS, and set a hard budget limit in your
  OpenAI account. This setup is not provided or supported here.

Production-style server (Linux/macOS; same settings the old hosted demo used):

```bash
gunicorn --bind 127.0.0.1:5000 --worker-class gevent --workers 2 --timeout 300 app:app
```

Sessions are shared between workers through `output/sessions/`. `main.py`
isn't used here, so `HOST`, `PORT` and `DEBUG` are ignored.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Comic picker says *"Add an OpenAI API key to .env to start!"* | Copy `.env.example` to `.env`, set `OPENAI_API_KEY`, restart. `python main.py --check` confirms. |
| *"Failed to start comic"* / *"Something went wrong"* | Read the terminal running the server. `401` means a wrong key. `429` / `insufficient_quota` means no credit or rate-limited. `model_not_found` / `does not exist` means the model is retired or not enabled for your account (see [Model retirement](#model-retirement)). A `403` on images may mean organization verification is needed. |
| Every panel says *"Something unexpected happened..."* | The story model call failed. The server log shows `[NARRATRON] ... failed` with the reason. |
| *"OpenAI didn't like that"* | OpenAI's safety system rejected the image. Write something else; the panel is rolled back so you can retry. |
| `Address already in use` | Another program uses port 5000 (on macOS often AirPlay Receiver). Use `PORT=5050 python main.py`, or change the `ports` line in `compose.yaml`. |
| `pip install` tries to compile OpenCV or NumPy | Use a supported Python version (3.11–3.14), 64-bit. On Intel Macs, macOS 12+ is needed. |
| *"Session expired"* | The server restarted or the session was idle for over an hour. Start a new comic. |
| Opened from another device and nothing loads | By default the server only listens on `127.0.0.1`. See [above](#exposing-it-beyond-your-computer). |
