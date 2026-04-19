<coding_guidelines>
# Hephaistos — Agent Guide

## Setup
```bash
uv sync --frozen           # install all dependencies
uv sync --group dev        # install dev tools (lint, type-check, test)
uv sync --group docs       # install doc-building tools
```

## Run
```bash
uv run heph                # launch interactive shell
uv run heph chat           # start a chat session
uv run heph armory create NAME  # create a new armory
```

## Lint & Format
```bash
uv run ruff check .        # lint
uv run ruff check --fix .  # lint with auto-fix
uv run ruff format .       # format
uv run ruff format --check .  # format check (CI mode)
```

## Type Check
```bash
uv run basedpyright        # type-check the project
```

## Dead Code / Architecture / Duplicates
```bash
uv run vulture hephaistos tests vulture-whitelist.py  # dead-code detection
uv run pylint --disable=all --enable=duplicate-code hephaistos  # duplicate code
uv run lint-imports        # verify import boundaries
```

## Test
```bash
uv run pytest                              # run all tests
uv run pytest --cov --cov-fail-under=75    # run with coverage gate
uv run pytest tests/test_chat_engine.py    # single file
uv run pytest -k "test_stream_recovery"    # by keyword
uv run pytest -m flaky                     # flaky-marked tests only
```

## Build & Release
```bash
uv build                   # build sdist + wheel
```
Releases are automated via `.github/workflows/release.yml` on `v*` tags.
Edge deploys run on every push to `main` via `.github/workflows/deploy.yml`.

## Project Conventions
- Python ≥3.13, `from __future__ import annotations` in every module
- Line length: 99 chars, double quotes, LF line endings
- Naming: PascalCase classes, snake_case functions/variables, UPPER_SNAKE_CASE constants (enforced by ruff N rules)
- Type checking: basedpyright standard mode
- Import boundaries: only `app` may import other packages; all other packages are forbidden from importing `app` (enforced by import-linter)
- Tests: pytest with `--cov-fail-under=75`, `@pytest.mark.flaky(reruns=2)` for flaky tests
- Pre-commit: ruff, ruff-format, basedpyright, check-large-files, vulture, pylint, lint-imports
</coding_guidelines>
