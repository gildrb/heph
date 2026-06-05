# Hephaion Harness

Hephaion owns the correctness-critical harness:

`intent -> planning -> evidence -> generation/repair -> verification/finalization`

It may depend on `ai.*` primitives plus extension contracts, but it does not
import Heph or interface adapters. Hephaion protects correctness; Heph owns the
agent brain that decides how to use this harness.

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
  opt-in events, armory-scoped traces, and redacted crash reporting.

The current `agent` and `chat` modules still host migration-era loop mechanics.
Preserve their guardrail and evidence responsibilities, but move new
conversational strategy, research orchestration, and Heph-facing persona toward
Heph-facing modules.

## Dependency Direction

Allowed direction:

```text
hephaion -> ai
hephaion -> extensions
rag -> materials
chat -> rag / memory / study / agent / ai.runtime
```

Forbidden direction:

```text
hephaion -> heph
hephaion -> interfaces
materials -> rag / chat / agent / study
study -> chat / agent / rag / adapters
ai -> hephaion
```

Integration tests may exercise app and interface composition when they are
testing migrated workflows, but runtime source should keep the harness portable.

## Migration Pressure

If a harness module starts to render UI, parse command-line arguments, or know
about TUI keybindings, move that behavior to Interfaces or Heph. If a module
starts to know provider SDK details, move that part to AI.

If a harness module starts to decide who Heph is, how Heph should talk, or how
Heph should conduct research beyond invoking correctness services, move that
behavior to Heph and keep Hephaion as the validation boundary.
