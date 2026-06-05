<p align="center">
  <img alt="Hephaion" src="https://gildrb.github.io/heph/logo-auto.svg" width="128">
</p>

# heph-interfaces

`heph-interfaces` owns user-facing adapters: terminal primitives, Textual TUI
composition, rendering, key handling, inline menus, transcript display, and
interface-specific session actions.

Interfaces are views over the same harness. They should adapt input and
presentation, not invent separate product logic or duplicate correctness
decisions.

## Package Role

Use `heph-interfaces` when a change is about:

- Textual app lifecycle, widgets, resize behavior, keybindings, inline menus,
  composer controls, or transcript rendering;
- terminal styling, direct input/output, source opening, and input history;
- adapting slash commands and chat event streams into interactive UI behavior;
- interface diagnostics and dependency messages.

Do not put provider auth rules, retrieval policy, citation checks, memory
extraction, armory storage, or command business logic here. Promote reusable
decisions into `hephaion`, `heph-ai`, or `heph` and leave the interface as a
consumer.

## Import Surface

The package exports two flat adapter roots:

```text
src/
  terminal/  Terminal styling, I/O, history, source opening, theme state
  tui/       Textual app, widgets, flows, keymaps, rendering, streaming adapter
```

Common imports:

```python
from terminal import print_info, styled
from tui import run_tui_for_path, set_command_registry_fn
```

The app package wires command registries into this package at startup. That keeps
the TUI from owning the command package.

## Boundaries

`heph-interfaces` may import broadly because adapters need to compose the
product. The important rule is ownership:

- UI state and rendering belongs here.
- Reusable workflow decisions belong below the interface.
- Commands are injected into the interface, not imported as a reusable business
  dependency.
- Textual compatibility workarounds stay isolated in `tui.textual_compat`,
  `tui.resize`, and focused adapter modules.

When interface code grows a domain decision, move that decision into `hephaion`
or `heph` and keep only the display or input mapping here.

## Development

Run the focused interface tests:

```bash
uv run pytest --no-cov packages/interfaces/test
```

Run the app in a source checkout after visible TUI changes:

```bash
uv run heph
```

Run boundary checks when moving behavior out of adapters:

```bash
uv run python -m scripts.check_repo_policies
uv run lint-imports
```

## Related Docs

- [Architecture](docs/architecture.md)
- [Workspace package map](../README.md)
- [Root architecture guide](../../docs/architecture.md)
