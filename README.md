# Hephaistos

Minimal Python CLI for armory-based study workflows.

## Quickstart

```bash
uv sync
uv run hephaistos --help
```

Create and validate an armory:

```bash
uv run hephaistos armory init ./my-armory
uv run hephaistos armory open ./my-armory
```

Short alias:

```bash
uv run heph --help
```

## Commands

- `armory` -> initialize/open armory folders

Running `hephaistos` with no arguments opens the interactive menu when stdin/stdout are TTY.

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
