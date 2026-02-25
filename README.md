# Hephaistos

Minimal Python CLI for armory-based study workflows.

## Quickstart

```bash
uv sync
uv run hephaistos
```

`hephaistos` (or `heph`) with no args opens the interactive menu in a TTY.
In non-interactive shells, it prints help.

Create and validate an armory:

```bash
uv run hephaistos armory init ./my-armory
uv run hephaistos armory open ./my-armory
```

Short alias:

```bash
uv run heph --help
```

Install shell entrypoints:

```bash
uv tool install --force --editable .
heph
```

## Commands

- `armory` -> initialize/open armory folders

## Project Layout

```text
hephaistos/
  app/
  armory/
tests/
```

## Status

- Implemented: CLI wiring, armory init/open validation, tests.

## Development

```bash
uv run pytest
```

Local runtime artifacts (for example `*-armory/` and `.hephaistos/`) are intentionally ignored and not tracked.
