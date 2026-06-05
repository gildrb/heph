# Heph Architecture

Heph is the agent brain the user talks to. It owns agent identity,
research/talking orchestration, and the command entrypoint, then composes the
interface adapters, Hephaion harness, AI runtime, and extension contracts.

## Ownership

The package owns:

- `cli`: top-level argument parsing, source-checkout startup behavior, and
  subcommand dispatch;
- `commands`: slash-command registry and command implementations that coordinate
  lower packages;
- `product`: temporary self-knowledge bridge into extension contracts;
- `identity`, `prompts`, and `state`: declarative homes for Heph's stable
  self-description and model-facing behavior.

New conversational strategy, research orchestration, and Heph-facing identity
belong here. The current `hephaion/agent` and `hephaion/chat` modules still
contain migration-era loop mechanics; new work should move the agent-brain
boundary toward Heph while continuing to call Hephaion for correctness checks.

## Dependency Direction

Allowed direction:

```text
heph -> ai
heph -> hephaion
heph -> interfaces
heph -> extensions
```

Heph may compose broadly, but lower packages must not import Heph. If command
code begins to contain retrieval, citation, memory, provider, or TUI mechanics,
move the reusable decision into the package that owns that concern.

Commands may use terminal output helpers, but they must not import `tui`
internals. The TUI adapter calls the command registry; command logic does not
know widgets, flows, or keybindings.

## Migration Pressure

This package should grow through clearer identity and command boundaries, not
through new god modules. The harness and interfaces are separate packages.
