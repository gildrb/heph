<p align="center">
  <img alt="Hephaion" src="https://gildrb.github.io/heph/logo-auto.svg" width="128">
</p>

# heph

`heph` is the app package: the console command, product composition layer, and
the home for Heph's identity and self-knowledge surfaces. It is the package that
wires the AI runtime, correctness harness, interfaces, and extension contracts
into the user-facing `heph` command.

This package should stay small and decisive. It may compose broadly, but reusable
decisions should move down into the package that owns them.

## Package Role

Use `heph` when a change is about:

- command-line entrypoints and top-level argument routing;
- slash-command registration and command implementations that coordinate the
  harness, providers, terminal output, and TUI behavior;
- product identity and self-knowledge that Heph should be able to explain;
- app-level composition of `heph-ai`, `hephaion`, `heph-interfaces`, and
  `heph-extensions`.

Do not put reusable RAG, citation verification, memory extraction, provider
configuration, or TUI rendering logic here. The app should call those packages,
not own them.

## Import Surface

The package exports flat app concerns:

```text
src/
  cli/       Console entrypoint and subcommand dispatcher
  commands/  Slash-command handlers and command registry
  product/   Product context bridge for extension contracts
  identity/  Stable Heph self-description target
  prompts/   Prompt-program target for Heph-facing behavior
  state/     Declarative state contract target
```

The public console scripts are:

```text
heph
hephaion
```

`heph` is canonical. `hephaion` remains as a long-form alias for the harness.

## Boundaries

`heph` may import the harness, AI runtime, interface adapters, and extension
contracts. It should not become the owner of their business logic.

- CLI parsing belongs in `cli`.
- Command coordination belongs in `commands`.
- Provider/model behavior belongs in `heph-ai`.
- Retrieval, citations, memory, study state, and armory persistence belong in
  `hephaion`.
- Textual, terminal, and rendering behavior belongs in `heph-interfaces`.
- Stable user-extension contracts belong in `heph-extensions`.

When a command starts to accumulate reusable behavior, move the behavior down and
leave the command as a thin coordinator.

## Development

Run the focused app tests:

```bash
uv run pytest --no-cov packages/heph/test
```

Run CLI smoke checks from a source checkout:

```bash
uv run heph --help
uv run heph armory init /tmp/heph-smoke-armory
```

Run boundary checks when moving code between app and reusable packages:

```bash
uv run python -m scripts.check_repo_policies
uv run lint-imports
```

## Related Docs

- [Architecture](docs/architecture.md)
- [Workspace package map](../README.md)
- [Root architecture guide](../../docs/architecture.md)
