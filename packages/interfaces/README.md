<p align="center">
  <img alt="Hephaion" src="https://raw.githubusercontent.com/gildrb/heph/main/docs/assets/logo-auto.svg" width="128">
</p>

# Interfaces

Interfaces owns the user-facing adapters around Heph and Hephaion.

This package contains terminal primitives, Textual TUI composition, rendering,
key handling, inline menus, transcript display, source opening, and theme
tokens.

## Source Layout

```text
src/
  interfaces/
    palette/   Theme and ANSI color tokens for terminal/TUI rendering
    terminal/  Terminal styling, I/O, history, source opening, theme state
    tui/       Textual app, widgets, flows, keymaps, rendering, streaming adapter
```

## Boundaries

Interfaces adapts input and presentation. It should not own provider behavior,
retrieval policy, citation verification, memory extraction, armory persistence,
or command business logic.

When interface code needs a domain decision, move that decision to Hephaion,
AI, or Heph and keep only the display/input mapping here.

## Development

```bash
uv run pytest --no-cov packages/interfaces/test
uv run heph
uv run python -m scripts.check_repo_policies
uv run lint-imports
```

## Related Docs

- [Root architecture guide](../../docs/architecture.md)
