# Contributing to EchoMind

EchoMind is a local-first research prototype. Contributions should keep the system inspectable, reproducible and honest about what was measured.

## Development setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,science]"
```

Run the fast local checks before opening a pull request:

```powershell
ruff check src tests app.py scripts
python -m compileall -q src app.py scripts
pytest -q
```

## Contribution rules

- Keep audio local by default. Do not add a hosted inference dependency without an explicit opt-in and documentation.
- Preserve the baseline transcript and provenance when adding corrections.
- Never commit model weights, raw recordings, generated reports or credentials.
- Add a focused test for new decision logic or schema fields.
- Do not report benchmark numbers unless a checked-in manifest, command and environment can reproduce them.
- Keep licenses and dataset source URLs in `data/evaluation/corpus/SOURCES.json` and `docs/data_card.md`.

## Pull requests

Describe the user-visible change, the evaluation performed, and any known limitation. For UI changes, include a local screenshot or a short reproduction path when practical.
