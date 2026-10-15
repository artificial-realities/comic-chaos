# Comic Chaos

**An interactive, AI-powered comic adventure.**

*An [Artificial Realities](https://github.com/artificial-realities) project.*

<p align="center">
  <img src="static/images/logo.webp" alt="Comic Chaos logo" width="420">
</p>

Pick a comic and you're handed the first panel with an empty speech bubble.
Type what the hero says, thinks, or what happens next, and the story writes and
paints the next panel around your words while you watch it appear. Keep going
panel by panel, then download the finished strip as a single image. You steer
the story; the AI takes care of the art and the chaos.

<!-- TODO (optional): add a real screenshot or short GIF of a comic in progress,
     e.g. docs/images/screenshot.png. Don't link the old hosted demo; it's offline. -->

## Features

- **You write the dialogue.** Fill speech bubbles, thought bubbles and narration
  boxes, and the story follows your lead.
- **Panels paint themselves live.** Each panel streams in as a rough preview
  before the finished art lands.
- **Bubbles that fit the art.** Empty bubbles are drawn into the artwork itself,
  then found with computer vision so your text sits inside them.
- **Three comics included**: *GTA: The Comic*, *Norway vs. Sweden* and
  *Ticker Town*. Each has its own cast, locations, art style and rules.
- **English and Norwegian.** The interface and the story switch languages.
- **Download the strip.** Your comic is assembled into one shareable PNG.
- **Make your own comic** with two JSON files.

## Run it locally

You need **Python 3.11–3.14** and an **OpenAI API key**
([create one](https://platform.openai.com/api-keys)).

```bash
git clone https://github.com/artificial-realities/comic-chaos.git
cd comic-chaos
python3 -m venv .venv             # Windows: py -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
                                   # then open .env and paste your API key
python main.py
```

Open **<http://localhost:5000>**. Run `python main.py --check` to validate your
setup without starting the server or calling OpenAI.

### Or with Docker

```bash
cp .env.example .env               # then paste your API key into .env
docker compose up --build
```

The app is published on `127.0.0.1:5000` only. The Docker setup is new: CI
builds and smoke-tests the image, but it hasn't been tried on a real Docker
host yet.

Windows details, configuration options, troubleshooting and more are in
**[docs/self-hosting.md](docs/self-hosting.md)**.

## Your API key and costs

Comic Chaos uses OpenAI's **paid** API: a chat model writes the story and an
image model paints the panels. Starting a comic costs one story request and two
images. Each bubble you fill costs one story request and one or two images
(occasionally one more, when a panel has to be repainted). Images make up most
of the cost. Check [OpenAI's pricing](https://openai.com/api/pricing/) and
consider a monthly budget limit on your OpenAI account.

- Your key lives in `.env` on your computer. It's ignored by git and excluded
  from Docker images, so never commit it or share it.
- The server listens on `127.0.0.1` only. Comic Chaos has no login, so anyone
  who could reach it could spend your credit. See
  [exposing it beyond your computer](docs/self-hosting.md#exposing-it-beyond-your-computer)
  before changing that.

> **Model retirement:** OpenAI will shut down the image models these comics use
> (`gpt-image-1.5`, `gpt-image-1-mini`) on **1 December 2026**, and the story
> models (`gpt-4.1`, `gpt-4o-mini`) on **14 January 2027**. You can switch models
> with the `COMIC_CHAOS_IMAGE_MODEL` / `COMIC_CHAOS_LLM_MODEL` settings, but
> replacement models haven't been tested with Comic Chaos yet. See
> [Model retirement](docs/self-hosting.md#model-retirement).

## Create your own comic

Add a folder under `comics/`. The folder name becomes the comic's ID:

```
comics/my_comic/
├── blueprint.json    # the world: title, cast, places, style, rules
└── config.json       # optional: models, image quality, panel font
```

A minimal `blueprint.json`. The first location is where the story starts, and
the first character is the hero:

```json
{
  "title": "My Comic",
  "title_no": "Min tegneserie",
  "synopsis": "A one-line hook for the story.",
  "synopsis_no": "En kort krok for historien.",
  "visual_style": "Describe the art style in detail",
  "locations": [{ "name": "Starting Place", "description": "Where the story begins" }],
  "characters": [{ "name": "Hero", "description": "Two or three visual features and one personality trait" }],
  "rules": ["Tone and behaviour guidelines for the storyteller"],
  "narrative_premise": "What the story is fundamentally about"
}
```

`config.json` can set `llm_model`, `image_model`, `image_quality`
(`low`/`medium`/`high`), `panel_font`, and more. Copy one from
[`comics/gta/`](comics/gta). The full schema is `Blueprint` and `ComicConfig`
in [`src/state/static_config.py`](src/state/static_config.py). Validate with
`python main.py --check`. The comic picker shows three comics, so a fourth needs
a new bubble in `templates/index.html`.

## How it works

```
your text → Narratron (chat model) plans the next panel → image model paints it with an empty bubble
          ← text rendered into the bubble ← OpenCV finds the bubble ←┘
```

It's a Flask backend streaming panels over Server-Sent Events to a single
vanilla-JavaScript page. Pydantic models hold the story state, OpenCV finds
bubbles, and Pillow renders the text and the final strip. Details are in
**[docs/architecture.md](docs/architecture.md)**.

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. The
test suite runs offline and never calls OpenAI. Coding agents (and curious
humans) should start with [AGENTS.md](AGENTS.md), and security reports go
through [SECURITY.md](SECURITY.md).

## Project status

Comic Chaos is a **completed project**. The former public demo is offline, so
run it on your own computer instead. It isn't under active development, but the
source is open for exploring, remixing and contributions. Replies to issues and
pull requests may be slow.

## License and credits

[MIT](LICENSE). Created by Simen Bihaug-Frøyland
([@sbfroy](https://github.com/sbfroy)) and published by
[Artificial Realities](https://github.com/artificial-realities).

Panel text uses [Comic Neue](https://github.com/crozynski/comicneue)
(SIL Open Font License, [`static/fonts/OFL.txt`](static/fonts/OFL.txt)).
Story and artwork are generated with OpenAI models.
