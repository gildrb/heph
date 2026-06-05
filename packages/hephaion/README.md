<p align="center">
  <img alt="Hephaion" src="https://gildrb.github.io/heph/logo-auto.svg" width="128">
</p>

# hephaion

`hephaion` is the correctness harness. It owns the local document system that
lets Heph answer from user materials with verifiable citations, armory-scoped
memory, retrieval indexes, study state, diagnostics, and session persistence.

The harness is the protected core of the product. It may call AI primitives and
extension contracts, but it must stay independent from app commands and UI
adapters.

## Package Role

Use `hephaion` when a change is about:

- armory discovery, validation, storage, and material import;
- document extraction, chunking, indexing, retrieval, source mapping, and RAG
  health checks;
- chat session lifecycle, turn planning, evidence resolution, grounded
  generation, citation checks, reply repair, and finalization;
- agent tool contracts, safe local tool execution, prompt building, and dynamic
  armory tool loading;
- local memory extraction, study planning, recall scheduling, vocabulary drills,
  and priority analysis;
- privacy consent, redacted diagnostics, traces, usage snapshots, and release
  safe stubs.

Do not put terminal rendering, Textual widgets, CLI argument parsing, provider
SDK configuration, or product identity copy here.

## Import Surface

The package exposes reusable harness modules as flat roots:

```text
src/
  agent/       Tool execution, prompts, citations, agent loop
  armory/      Portable workspace validation and lookup
  chat/        Session state, turn orchestration, evidence, streaming events
  diagnostics/ Redacted crash and anonymous event surfaces
  matching/    Human-facing fuzzy matching helpers
  materials/   Material discovery, ignore rules, import helpers
  memory/      Armory-scoped memory extraction and persistence
  parameters/  Settings storage and parameter CLI helpers
  privacy/     Consent and release-time diagnostics config
  rag/         Chunking, indexing, retrieval, source mapping
  safety/      Local safety contracts
  study/       Learning controller, schedules, priority workflows
  version/     Package version helpers
  vocab/       Vocabulary parsing, scheduling, drills
```

Prefer public facades for stable consumers:

```python
from chat.session import ChatSession, create_plain_session
from rag import ArmoryIndex, TurnEvidence, retrieve
from armory.storage import initialize, validate
```

## Boundaries

`hephaion` may import `runtime`, `providers`, `ai_logging`, `ai_diagnostics`,
`ai_types`, `palette`, and `extension_contracts`.

It must not import app or adapter modules at runtime:

- no `cli` or `commands`;
- no `tui`;
- no terminal input/history adapters.

Domain packages inside the harness should also stay one-way:

- `materials` owns discovery and ignore policy; `rag` may import `materials`,
  but `materials` must not import `rag`, `chat`, `agent`, or `study`;
- `runtime` primitives live in `heph-ai`; harness modules use them rather than
  re-defining provider message types;
- `study` remains a controller/state layer and should not depend on chat or UI
  adapters;
- `chat.session` and `chat.orchestrator` stay separate public composition
  surfaces.

## Development

Run the focused harness tests:

```bash
uv run pytest --no-cov packages/hephaion/test
```

Run checks that protect harness shape:

```bash
uv run python -m scripts.check_repo_policies
uv run lint-imports
uv run ty check
```

When fixing retrieval or overview behavior, keep the solution structural:
provider-swappable prompts, evidence handling, and generic fixtures. Do not add
private corpus keyword lists or one-off phrase tables.

## Related Docs

- [Architecture](docs/architecture.md)
- [Workspace package map](../README.md)
- [Root architecture guide](../../docs/architecture.md)
