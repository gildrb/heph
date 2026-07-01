<p align="center">
  <img alt="Heph" src="https://raw.githubusercontent.com/gildrb/heph/main/assets/logo-auto.svg" width="320">
</p>

# Harness

This package contains the validation and correctness harness behind Heph. The
public Python package is `heph`; this workspace currently imports the harness
through `harness.*`.

It owns the local document machinery that lets Heph answer from user materials
with verifiable citations, armory-scoped memory, retrieval indexes, learning
state, diagnostics, and session persistence.

The harness is not the agent brain or persona. Users talk to Heph.

## Source Layout

```text
src/
  harness/
    agent/       Tool execution, prompt assembly, citations, agent loop helpers
    armory/      Portable armory validation, discovery, and local state helpers
    chat/        Session state, turn orchestration, evidence, events, storage
    diagnostics/ Redacted crash, anonymous event, and armory trace surfaces
    matching/    Human-facing fuzzy matching helpers
    materials/   Material discovery, ignore rules, import helpers
    memory/      Armory-scoped learning memory extraction and persistence
    parameters/  Settings storage and parameter helpers
    privacy/     Consent and release-time diagnostics config
    rag/         Chunking, indexing, retrieval, source mapping
    safety/      Local safety contracts
    study/       Learning controller, schedules, priority workflows
    version/     Package version helpers
    vocab/       Vocabulary parsing, scheduling, drills
```

## Boundaries

The harness may depend on `ai.*` primitives and extension contracts. It must not
import Heph app modules or interface adapters. Extension work should call
harness APIs instead of editing guardrails directly.

Within the harness:

- `materials` owns discovery and ignore policy;
- `rag` may import `materials`, but `materials` must not import `rag`, `chat`,
  `agent`, or `study`;
- `study` remains a controller/state layer and must not import `chat`, `agent`,
  `rag`, or adapters;
- `agent` must not import `chat`;
- `chat.session` and `chat.orchestrator` stay independent at runtime.

The current `agent` and `chat` packages include migration-era loop mechanics.
Keep guardrails, evidence resolution, citation verification, memory, and armory
state here. Move new Heph-facing conversational strategy toward Heph rather than
expanding the harness into a second agent.

## Development

```bash
uv run pytest --no-cov packages/harness/test
uv run python -m scripts.check_repo_policies
uv run lint-imports
```

## Related Docs

- [Root architecture guide](../../docs/architecture.md)
