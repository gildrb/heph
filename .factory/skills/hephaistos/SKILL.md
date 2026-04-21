---
name: hephaistos
description: Local-first study CLI with armories, source-grounded answers, and a public-facing `heph` command
---

# Hephaistos Project Skill

## Overview

Hephaistos is a local-first study CLI built with Python 3.13+. It provides an
interactive shell for source-grounded study sessions, armory management, and
RAG-based retrieval.

## Public Install

```bash
uv tool install hephaistos
heph --version
```

For a local checkout:

```bash
uv sync --group dev
uv run heph
uv tool install --force --editable .
```

## Key Commands

```bash
heph                       # launch interactive shell
heph chat start PATH       # start a chat session
heph armory init PATH      # create a new armory
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
- Keep repo-level agent context in `.factory/skills/hephaistos/` and `.codex/skills/hephaistos/`
- Keep personal agent config and maintainer-only tooling out of the repository

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
