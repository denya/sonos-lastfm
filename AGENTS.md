# Repository Guidelines

## Project Structure & Module Organization
- Core package lives in `src/sonos_lastfm`, with `cli.py` exposing the Typer CLI, `config.py` handling environment/keyring loading, and `sonos_lastfm.py` managing discovery and scrobbling.
- `data/` holds sample JSON snapshots for manual verification; avoid committing real credentials or playback history.
- `pyproject.toml` and the `Makefile` define packaging, tooling, and automation. Build artifacts land in `dist/`, while `uv.lock` pins workspace dependencies.

## Build, Test, and Development Commands
- First-time setup: `make setup` to create a `uv` virtualenv, then `make install` (runtime deps) or `make install-dev` (includes mypy and ruff).
- Run the scrobbler locally with `make run`, which executes `uv run -m sonos_lastfm`.
- Quality gates: `make check-types` (mypy strict mode) and `make check-ruff` (ruff linting). Use `make check-all` before opening a PR.
- Package workflows: `make build-package` produces wheels via `uv build`; `make release` walks through clean, version bump, build, publish, and verification.

## Coding Style & Naming Conventions
- Target Python 3.11+ features; type hints are mandatory (`disallow_untyped_defs = true`).
- Ruff enforces Google-style docstrings, 88-character lines, and a wide lint surface (`select = ALL`). Run `ruff check --fix` for quick clean-ups.
- Functions and modules follow `snake_case`, classes use `PascalCase`, and Typer commands mirror CLI flag names (e.g., `resetup`).
- Keep configuration values in environment variables or keyring; never hard-code secrets.

## Testing Guidelines
- There is no dedicated test suite yet. Create `tests/` alongside `src/` when adding unit or integration coverage, preferably with `pytest`.
- For manual smoke tests, run `sonos-lastfm test` to validate Last.fm connectivity and use the JSON fixtures in `data/` as controlled inputs.
- Document any new test entry points in the README and wire them into the Makefile so contributors can discover them via `make help`.

## Commit & Pull Request Guidelines
- Use short, imperative commit messages (e.g., `Add retry around playback fetch`); group unrelated changes into separate commits.
- Reference GitHub issues in the body when applicable (`Refs #123`). Include screenshots or CLI transcripts for user-facing adjustments.
- PRs should summarize behavior changes, list test commands executed, and call out any configuration updates or migration steps.
