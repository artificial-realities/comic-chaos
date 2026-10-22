# Comic Chaos

An interactive comic where you write the words. Type into an empty speech
bubble, and language and image models draw the next panel and carry the story on.

```
┌─▶ you write in the bubble
│     → an LLM plans the next panel
│     → an image model draws it with an empty bubble
│     → OpenCV finds the bubble
└──── the panel streams to the browser
```

- **Story:** an LLM plans each panel as structured JSON and keeps track of the
  plot with a rolling summary and story arcs.
- **Images:** an image model draws each panel with one empty speech bubble,
  thought bubble or narration box, streaming previews while it draws.
- **Computer vision:** OpenCV finds the empty bubble by thresholding and contour
  analysis, and Pillow renders the text into it for the finished strip.

Built with Flask, Server-Sent Events, Pydantic, OpenCV and Pillow, with English
and Norwegian UIs. [docs/architecture.md](docs/architecture.md) explains how it fits together.

## Run it

You need Python 3.11–3.14 and an [OpenAI API key](https://platform.openai.com/api-keys):

```bash
git clone https://github.com/artificial-realities/comic-chaos.git
cd comic-chaos
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # then add your OpenAI API key to .env
python -m comic_chaos             # open http://127.0.0.1:5000
```

`python -m comic_chaos --check` says what is missing, without calling OpenAI.
Starting a comic costs one story request and two images, and each bubble one
story request and one or two images. The app has no login and listens on
`127.0.0.1` only: every comic is billed to your key.

## Comics

- **GTA: The Comic.** Open-world chaos: what happens in Oslo Streets stays in Oslo Streets.
- **Norway vs. Sweden.** Who is the best ski nation?
- **Ticker Town.** Life as a stock, where market forces feel like acts of god.

A comic is a folder under `comics/` with a `blueprint.json`. The folder name is
its ID, the first location is where the story starts, and the first character
is the hero:

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

The schema is `Blueprint` in [`comic_chaos/state/static_config.py`](comic_chaos/state/static_config.py);
an optional `config.json` overrides any `ComicConfig` setting there (models,
image quality, panel font). The picker has room for three comics, so a fourth
needs a new bubble in `comic_chaos/templates/index.html`.

## Status

Comic Chaos is on pause while we work on other projects. `pip install -r requirements-dev.txt`,
then `python -m pytest` and `ruff check .`: the tests run offline, without a key.
Issues and pull requests are welcome.

## License

The code is [MIT](LICENSE). An [Artificial Realities](https://github.com/artificial-realities)
project by Simen Bihaug-Frøyland ([@sbfroy](https://github.com/sbfroy)).
Panel text uses [Comic Neue](https://github.com/crozynski/comicneue) (SIL Open Font
License, [`OFL.txt`](comic_chaos/static/fonts/OFL.txt)). Story and artwork are
generated with OpenAI models.
