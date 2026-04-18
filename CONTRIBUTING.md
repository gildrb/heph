# Contributing to Hephaistos

Thanks for your interest! Hephaistos is a personal learning project, but suggestions and fixes are welcome.

## Setup

```bash
# Install with dev dependencies
uv sync --group dev

# Optional: enable RAG extras
uv sync --group rag
```

## Development workflow

1. Create a feature branch from `main`.
2. Make your changes.
3. Run the checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run pytest
```

4. Commit with a clear message.
5. Open a pull request.

## Code style

- Linting and formatting: [ruff](https://docs.astral.sh/ruff/) (config in `pyproject.toml`).
- Type checking: [basedpyright](https://basedpyright.com/) (`standard` mode).
- Line length: 99 characters.
- Target Python: 3.13+.
- Use `from __future__ import annotations` at the top of every module.

### Naming conventions

These are enforced via ruff (the N rules):

- **Classes**: PascalCase (e.g., `ChatConfig`, `EngineError`)
- **Functions and methods**: snake_case (e.g., `build_parser()`, `stream_completion()`)
- **Variables**: snake_case (e.g., `api_key`, `max_tokens`)
- **Constants (module-level and class-level)**: UPPER_SNAKE_CASE (e.g., `_VERSION`, `_RETRYABLE_TYPES`)
- **Private variables**: underscore prefix (e.g., `_tools`, `_registry`)
- **Dataclass fields**: snake_case

## Commit messages

Short, imperative mood. Examples:

```
Add --version flag to CLI
Fix citation verification for empty sources
Refactor RAG injection and transcript compaction
```

## Tests

```bash
# Run the full suite
uv run pytest

# Run a single file
uv run pytest tests/test_tools.py

# Run with verbose output
uv run pytest -v
```

Tests use `pytest` with coverage via `pytest-cov`. Aim to cover new code with tests.

## Reporting issues

Open a GitHub issue with:

- What you expected to happen.
- What actually happened.
- Steps to reproduce (commands, config, etc.).
- Relevant logs or error output.
