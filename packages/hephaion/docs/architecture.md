# Hephaion Harness

Hephaion owns the correctness-critical harness:

`intent -> planning -> evidence -> generation/repair -> verification/finalization`

It may depend on AI primitives from `runtime`, `providers`, `ai_logging`, and
related `packages/ai/src` concerns, plus extension contracts, but it does not
import the app package or interface adapters.

## Ownership

The package owns:

- `agent`: prompt building, citation helpers, tool schemas, local tool execution,
  mutation queues, and dynamic armory tool loading;
- `armory`: portable workspace markers, validation, and known-armory lookup;
- `chat`: session state, turn orchestration, evidence, reply repair, event
  streaming, persistence, and usage;
- `materials`: material discovery, ignore policy, material import, and generic
  material-role inference;
- `rag`: extraction, chunking, indexing, retrieval, source mapping, and health;
- `memory`: armory-scoped learning memory extraction and storage;
- `study` and `vocab`: learning state, recall scheduling, assessment, priority
  analysis, and drills;
- `privacy` and `diagnostics`: local consent, safe release stubs, anonymous
  opt-in events, and redacted crash reporting.

## Dependency Direction

Allowed direction:

```text
hephaion -> heph-ai
hephaion -> heph-extensions
rag -> materials
chat -> rag / memory / study / agent / runtime
```

Forbidden direction:

```text
hephaion -> heph
hephaion -> heph-interfaces
materials -> rag / chat / agent / study
study -> chat / agent / rag / adapters
runtime -> hephaion
```

Integration tests may exercise app and interface composition when they are
testing migrated workflows, but runtime source should keep the harness portable.

## Migration Pressure

If a harness module starts to render UI, parse command-line arguments, or know
about TUI keybindings, move that behavior to `heph-interfaces` or `heph`. If a
module starts to know provider SDK details, move that part to `heph-ai`.
