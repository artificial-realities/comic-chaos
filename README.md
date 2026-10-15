# Comic Chaos

An interactive comic generator built with generative AI.

An [Artificial Realities](https://github.com/artificial-realities) project.

Comic Chaos generates comic panels based on user input. Users can write dialogue, influence the story, and generate new panels using language and image models. Finished comics can be exported as a single image.

## Features

- **Interactive storytelling:** Generate comic panels based on dialogue and user input.
- **Speech bubbles:** Detect speech bubbles using OpenCV and render text into them.
- **Multiple comics:** Includes GTA: The Comic, Norway vs. Sweden, and Ticker Town.
- **Language support:** English and Norwegian.
- **Export:** Download completed comics as PNG images.
- **Custom comics:** Define new comics using JSON configuration files.

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

Comic Chaos is a completed project and is no longer actively maintained. The hosted demo has been discontinued, but the application can still be run locally.

The source code remains available for self-hosting, modification, and contributions.

## License and credits

[MIT](LICENSE). Created by Simen Bihaug-Frøyland
([@sbfroy](https://github.com/sbfroy)) and published by
[Artificial Realities](https://github.com/artificial-realities).

Panel text uses [Comic Neue](https://github.com/crozynski/comicneue)
(SIL Open Font License, [`static/fonts/OFL.txt`](static/fonts/OFL.txt)).
Story and artwork are generated with OpenAI models.
