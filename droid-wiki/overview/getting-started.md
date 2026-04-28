# Getting started

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

## Install from source

```bash
git clone https://github.com/gildrb/hephaistos
cd hephaistos
uv sync --frozen
```

## Install as a tool

```bash
uv tool install hephaistos
heph
```

## Optional dependency groups

```bash
uv sync --group rag       # BM25, embedding retrieval, cross-encoder re-ranking
uv sync --group docling    # PDF, DOCX, PPTX, XLSX conversion
uv sync --group dev        # Lint, type-check, test tools
uv sync --group docs       # MkDocs documentation building
```

## Run

```bash
uv run heph                # Launch TUI (plain-chat mode)
uv run heph <armory-path>  # Launch TUI attached to an armory
uv run heph armory init ~/armories/exams  # Create an armory
```

## Test

```bash
uv run pytest                              # Run all tests
uv run pytest --cov --cov-fail-under=75    # Run with coverage gate
uv run pytest tests/test_chat_engine.py    # Single file
uv run pytest -k "test_stream_recovery"    # By keyword
```

## Lint and format

```bash
uv run ruff check .        # Lint
uv run ruff check --fix .  # Lint with auto-fix
uv run ruff format .       # Format
```

## Type check

```bash
uv run basedpyright        # Strict type-check the project
```

## Dead code and architecture checks

```bash
uv run vulture hephaistos tests vulture-whitelist.py  # Dead code detection
uv run pylint --persistent=no --score=no --disable=all --enable=duplicate-code hephaistos
uv run lint-imports        # Verify import boundaries
```
