# Comic Chaos

An interactive comic platform powered by generative AI. Users write dialogue in
empty speech bubbles, while language and image models generate new panels and
adapt the story. Built as a fun exploration of interactive storytelling,
combining LLMs, image generation and computer vision.

An [Artificial Realities](https://github.com/artificial-realities) project.

## How it works

```
┌─▶ user writes in the bubble
│     → LLM plans the next panel
│     → image model draws it with an empty bubble
│     → OpenCV finds the bubble
└──── panel streams to the browser
```

- **Story:** an LLM plans each panel as structured JSON and tracks the plot
  with a rolling summary and story arcs.
- **Images:** an image model draws each panel with one empty speech bubble,
  thought bubble or narration box, streaming previews while it draws.
- **Computer vision:** OpenCV finds the empty bubble through thresholding and
  contour analysis, and Pillow renders the text into it.

Built with Flask, Server-Sent Events, Pydantic, OpenCV and Pillow. Details in
[docs/architecture.md](docs/architecture.md).

## Run it locally

Requires **Python 3.11–3.14** and an
[OpenAI API key](https://platform.openai.com/api-keys).

```bash
git clone https://github.com/artificial-realities/comic-chaos.git
cd comic-chaos
python3 -m venv .venv             # Windows: py -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
                                   # then add your API key to .env
python -m comic_chaos
```

Open <http://localhost:5000>. `python -m comic_chaos --check` validates the
setup without calling OpenAI.

Or with Docker (new, and so far only tested in CI):

```bash
cp .env.example .env               # then add your API key to .env
docker compose up --build
```

More in [docs/self-hosting.md](docs/self-hosting.md).

## API key and costs

Comic Chaos uses OpenAI's paid API. Starting a comic costs one story request
and two images, and each bubble costs one story request and one or two images.
Consider a monthly budget limit on your OpenAI account.

The key stays in `.env`, which is git-ignored and excluded from Docker images.
The server listens on `127.0.0.1` only and has no login, so anyone who can reach
it can spend your credit. See
[exposing it beyond your computer](docs/self-hosting.md#exposing-it-beyond-your-computer).

> **Model retirement:** OpenAI retires the image models used here on
> **1 December 2026** and the story models on **14 January 2027**. Models can be
> switched with `COMIC_CHAOS_IMAGE_MODEL` / `COMIC_CHAOS_LLM_MODEL`, but
> replacements are untested. See [Model retirement](docs/self-hosting.md#model-retirement).

## Comics

- **GTA: The Comic.** Open-world chaos: what happens in Oslo Streets stays in
  Oslo Streets.
- **Norway vs. Sweden.** Who is the best ski nation?
- **Ticker Town.** Life as a stock, where market forces feel like acts of god.

### Create your own comic

Add a folder under `comics/` with a `blueprint.json`. The folder name is the
comic's ID, the first location is where the story starts, and the first
character is the hero:

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

An optional `config.json` sets models, image quality, panel font and more (copy
one from [`comics/gta/`](comics/gta)). The full schema is in
[`comic_chaos/state/static_config.py`](comic_chaos/state/static_config.py).
Validate with `python -m comic_chaos --check`. The picker has room for three
comics, so a fourth needs a new bubble in `comic_chaos/templates/index.html`.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](.github/CONTRIBUTING.md),
[AGENTS.md](AGENTS.md) for conventions, and [SECURITY.md](.github/SECURITY.md)
for reporting vulnerabilities. Tests run offline and never call OpenAI.

## Project status

Comic Chaos is on pause while we work on other projects. It still runs locally,
and issues and pull requests are welcome. The hosted demo is offline.

## License and credits

[MIT](LICENSE). Created by Simen Bihaug-Frøyland
([@sbfroy](https://github.com/sbfroy)) and published by
[Artificial Realities](https://github.com/artificial-realities).

Panel text uses [Comic Neue](https://github.com/crozynski/comicneue)
(SIL Open Font License,
[`comic_chaos/static/fonts/OFL.txt`](comic_chaos/static/fonts/OFL.txt)).
Story and artwork are generated with OpenAI models.
