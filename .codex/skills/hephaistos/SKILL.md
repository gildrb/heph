---
name: hephaistos
description: Local-first study CLI with armories, verified citations, and the public-facing `heph` command
---

# Hephaistos Project Skill

## Overview

Hephaistos is a local-first study CLI built with Python 3.13+. It works with
armories, source-grounded answers, citation verification, and swappable LLM
providers.

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
heph source index PATH     # rebuild retrieval state
```

## Development Workflow

```bash
uv sync --group dev
uv run ruff check .
uv run ruff format .
uv run basedpyright
uv run pytest
```

## Project Conventions

- Prefer readable code over cleverness or micro-optimizations
- Python >=3.13 with `from __future__ import annotations` in every module
- Line length: 99 chars, double quotes, LF line endings
- Import boundaries: only `app` may import other packages
- Shared repo skills live in `.factory/skills/hephaistos/` and `.codex/skills/hephaistos/`
- Personal agent config and maintainer-only tooling should stay outside the repo

## Architecture

```text
hephaistos/
  app/        CLI shell, commands, workspace
  chat/       Engine, session, orchestrator
  harness/    Prompting, tools, RAG helpers
  providers/  Provider registry and auth
  armory/     Workspace management
  study/      Study-loop state and control
  memory/     Armory-scoped memory
  parameters/ Config and defaults
  source/     Source indexing and listing
```
