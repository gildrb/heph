# Hephaistos Project Skill

## Overview

Hephaistos is an armory-first study CLI built with Python 3.13+. It provides an interactive
shell for LLM-powered study sessions, armory (knowledge base) management, and RAG-based
retrieval.

## Key Commands

```bash
uv run heph                # launch interactive shell
uv run heph chat           # start a chat session
uv run heph armory create NAME  # create a new armory
```

## Development Workflow

```bash
uv sync --frozen           # install all dependencies
uv sync --group dev        # install dev tools
uv run ruff check .        # lint
uv run ruff format .       # format
uv run basedpyright        # type-check
uv run pytest              # run tests
```

## Project Conventions

- Python >=3.13 with `from __future__ import annotations` in every module
- Line length: 99 chars, double quotes, LF line endings
- PascalCase classes, snake_case functions, UPPER_SNAKE_CASE constants
- Import boundaries: only `app` may import other packages (enforced by import-linter)
- Tests: pytest with `--cov-fail-under=75`

## Architecture

```
hephaistos/
  app/        CLI, shell, commands
  chat/       Chat engine, session, orchestrator
  harness/    LLM abstraction layer
  providers/  LLM provider registry and auth
  armory/     Knowledge base management
  study/      Study session logic
  memory/     Conversation memory
  parameters/ Parameter definitions
  source/     Document source adapters
```

## CI Checks

- **lint**: ruff check + ruff format
- **typecheck**: basedpyright
- **security**: bandit + gitleaks
- **dead-code**: vulture
- **duplicate-code**: pylint
- **architecture**: import-linter
- **test**: pytest with coverage gate
- **tech-debt**: TODO/FIXME issue link enforcement

## When to Use This Skill

- When working on the Hephaistos codebase
- When you need to understand project structure or conventions
- When setting up a new development environment
- When adding new modules or features to the project
