# Heph App

Heph is the user-facing app and agent identity. It composes the interface
adapters, correctness harness, AI runtime, and extension contracts into the
console command.

## Ownership

The package owns:

- `cli`: top-level argument parsing, source-checkout startup behavior, and
  subcommand dispatch;
- `commands`: slash-command registry and command implementations that coordinate
  lower packages;
- `product`: product context bridge into extension contracts;
- `identity`, `prompts`, and `state`: declarative homes for Heph's stable
  self-description and model-facing behavior.

## Dependency Direction

Allowed direction:

```text
heph -> heph-ai
heph -> hephaion
heph -> heph-interfaces
heph -> heph-extensions
```

The app may compose broadly, but it should not own reusable behavior. If command
code begins to contain retrieval, citation, memory, provider, or TUI mechanics,
move the reusable decision into the package that owns that concern and keep the
command as orchestration.

## Migration Pressure

This package should grow through clearer composition, identity, and command
boundaries, not through new god modules. Heph is the user-facing app surface;
the harness and interfaces are still separate packages.
