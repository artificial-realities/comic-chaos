# Contributing to Comic Chaos

Thanks for stopping by. Development of Comic Chaos is on pause, so the most
useful contributions are bug fixes, setup and documentation improvements, and
new comics. For anything bigger, open an issue first so we can agree on the
approach. Replies may be slow.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: py -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest        # offline: no API key, no network
ruff check .
```

To run the app, see the [README](README.md#run-it-locally).
[AGENTS.md](AGENTS.md) has the repository map, conventions, and the checklist
we use for every change, whether written by a person or a coding agent.

## Guidelines

- **Keep pull requests focused**, and match the style of the code around your change.
- **Tests stay offline.** Fake model calls the way `tests/test_generation_mocked.py`
  does; the suite fails any test that tries to use the network.
- **Generation costs money.** Testing a change by hand with real comics uses your
  own OpenAI key and credit. In the PR, say whether you did, so reviewers know
  what was tested for real.
- **Never commit secrets** (`.env`) or generated data (`output/`).
- **Update the docs** (README, `docs/`, `.env.example`, `AGENTS.md`) when
  behaviour, configuration or setup changes.
- **New comics** need a valid `blueprint.json` and should pass
  `python main.py --check`. Keep content suitable for a general audience.
- The UI is bilingual: add new strings in both English and Norwegian.

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
