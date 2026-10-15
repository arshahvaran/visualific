# Contributing to Visualific

Thank you for your interest. Visualific is at an early stage, so the most useful contributions right now are figure templates from published work, bug reports and comments on the design decisions in [`docs/decisions`](docs/decisions).

## Proposing a new template

Open an issue with the "New template" form. Include:

- a link or DOI to a published figure that shows the template,
- the question the figure answers for a reader,
- the shape of the data it needs, for example "one row per time step with observed, predicted and model columns",
- why the existing templates do not cover it.

A template is added after the steps in [decision 0005](docs/decisions/0005-template-fidelity-and-review.md): an approved specification, passing measured checks, review by AI reviewer agents, and the author's approval of a side-by-side comparison.

## Development setup

```bash
git clone https://github.com/arshahvaran/visualific.git
cd visualific
python -m venv .venv
```

Activate the environment (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` elsewhere), then:

```bash
pip install -e ".[test]"
pytest
```

Keep the clone and the virtual environment on a local disk. Cloud-synced folders such as Google Drive or OneDrive can corrupt the `.git` folder.

## Pull requests

- Keep each pull request to one change.
- Add a line to `CHANGELOG.md` under "Unreleased".
- Make sure `pytest` passes.
- If an AI tool helped write the change, name it and say what it did, so it can be added to `AI_USAGE.md`.
- For a new template, attach the rendered figure and link to the published figure it reproduces. Attach an image of the original only if its licence allows it, for example CC BY.
