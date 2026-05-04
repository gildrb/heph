# Architecture

Hephaistos follows strict import boundaries enforced by `import-linter`. Only
adapter packages may import broadly; lower tiers must stay copyable and must
not depend on product workflows.

## Architecture tiers

- **Core reusable packages**: `runtime`, `providers`, `logging`, `matching`,
  `terminal.palette`, `_types`. These are the most copyable packages and must
  not import product workflow packages.
- **Domain reusable packages**: `materials`, `rag`, `memory`, `armory`, `vocab`,
  `study`. These may model Hephaistos concepts, but must not depend on
  adapters, CLI command handlers, TUI modules, or chat session orchestration.
- **Application services**: `chat` and focused workflow modules. These compose
  core/domain packages into session lifecycle, evidence, memory workflows, and
  turn orchestration.
- **Adapters**: `cli`, `commands`, `tui`, `source`, and shell compatibility
  modules. These may depend broadly, but reusable decisions should be promoted
  into services or domain packages instead of staying in adapter code.

## Dependency flow

```mermaid
graph TD
    CLI[cli] --> TUI[tui]
    CLI --> Commands[commands]
    TUI --> Chat[chat]
    TUI --> Commands
    Commands --> Chat
    Commands --> Providers[providers]
    Commands --> Runtime[runtime]
    Commands --> Armory[armory]
    Commands --> Study[study]
    Commands --> Memory[memory]
    Commands --> Parameters[parameters]
    Commands --> Materials[materials]
    Commands --> Logging[logging]
    Commands --> Palette[palette]
    Commands --> RAG[rag]
    Commands --> Vocab[vocab]

    Chat --> Agent
    Chat --> Providers
    Chat --> Runtime
    Chat --> Logging
    Chat --> Memory

    Agent --> Providers
    Agent --> Runtime
    Agent --> Logging
    Agent --> Memory

    Memory --> Runtime
    Parameters --> Runtime

    RAG --> Materials

    Vocab --> Logging

    Providers --> Logging
    Providers --> Palette

    Study --> Logging

    Armory --> Logging

    Parameters --> Logging

    Materials --> Logging

    Logging --> Palette

    Runtime -->|API calls| LLM[OpenAI / Anthropic / etc.]
    Providers -->|Key storage| Keyring[OS Keyring]

    Agent -->|RAG index| FileStore[Armory Files]
    Chat -->|Session state| FileStore
```

The top layer is the adapter surface: **cli**, **commands**, **tui**, **shell**,
and **terminal**. `cli` is the public command dispatcher, `commands` contains
slash-command handlers, `tui` is the interactive Textual adapter, `shell` holds
plain-terminal session actions, and `terminal` owns low-level terminal I/O,
styling, history, and shell-input dispatch. Reusable packages communicate
through their public APIs and must not import adapter packages. Shared LLM
request primitives live in **runtime** so chat, agent, memory, parameters, and
providers do not import each other just to share message types or streaming
helpers.

## Package layout

```
hephaistos/
  cli/          Public command dispatcher and CLI argument parsing
  commands/     Slash-command handlers for shell/TUI adapters
  tui/          Textual interactive adapter: widgets, key handling, rendering
  shell/        Plain-terminal session, armory, and saved-chat actions
  terminal/     Terminal I/O, styling, prompts, history, shell-input dispatch
  matching/     Fuzzy matching helpers for human-facing selectors
  chat/         Session lifecycle, storage, turn orchestration — no adapter imports
  runtime/      Shared LLM messages, config, client streaming, retry helpers
  agent/        Prompt building, persona, citation, tools — no adapter imports
  providers/    LLM provider registry, config, auth — no adapter imports
  rag/          RAG chunking, indexing, retrieval — no adapter imports
  materials/    Study-file discovery, ignore rules, source/library classification
  armory/       Armory data and commands — no adapter imports
  study/        Study controller — no adapter imports
  memory/       Memory extraction and storage — no adapter imports
  parameters/   Parameter management CLI — no adapter imports
  privacy/      Consent, anonymous install ID, release-time diagnostics config
  diagnostics/  Anonymous events, local diagnostics, redacted crash reports
  source/       Deprecated CLI compatibility alias for materials
  vocab/        Vocabulary drill, scheduler, state — no adapter imports
  logging.py    Shared logging — must NOT import adapters
  terminal/palette.py  ANSI color primitives — must NOT import adapters
```

## Import rules

### Forbidden: reusable packages must not import adapters

The following packages cannot import anything from adapter packages:
`hephaistos.cli`, `hephaistos.commands`, `hephaistos.tui`, `hephaistos.shell`,
`hephaistos.terminal.banner`, `hephaistos.terminal.display`,
`hephaistos.terminal.history`, or `hephaistos.terminal.input`.

- `hephaistos.chat`
- `hephaistos.agent`
- `hephaistos.providers`
- `hephaistos.rag`
- `hephaistos.armory`
- `hephaistos.study`
- `hephaistos.memory`
- `hephaistos.parameters`
- `hephaistos.materials`
- `hephaistos.source`
- `hephaistos.runtime`
- `hephaistos.vocab`
- `hephaistos.logging`
- `hephaistos.terminal.palette`
- `hephaistos.matching`

### Forbidden: logging and diagnostics must not import adapters

`hephaistos.logging` and `hephaistos.diagnostics.crashes` must not import from
`hephaistos.cli`, `hephaistos.commands`, or `hephaistos.tui`.

### Independent: chat.session and chat.orchestrator

`hephaistos.chat.session` and `hephaistos.chat.orchestrator` must be independent at runtime (no direct runtime imports between them).

### Independent: materials

`hephaistos.materials` owns study material discovery and ignore-policy parsing.
It must not import `hephaistos.chat`, `hephaistos.agent`, or `hephaistos.rag`.
`hephaistos.rag` may import `materials`, but that dependency
is one-way.

### Low level: runtime

`hephaistos.runtime` owns shared LLM primitives such as `ChatConfig`,
`Conversation`, message conversion, client construction, streaming completion,
and retry helpers. It must not import adapters, `chat`, `agent`, `rag`, `study`,
`materials`, `memory`, or `armory`. Providers may be used by runtime, but
providers must not import product workflow packages.

### Core: providers

`hephaistos.providers` owns provider configuration, model catalogs, registry
metadata, and key resolution. It must not import adapters, `chat`, `agent`,
`rag`, `study`, or `materials`.

### Domain: memory and study

`hephaistos.memory` may use `runtime` to extract concepts, but it must not
import adapters, `chat`, or `agent`. `hephaistos.study` stays a pure
controller/state layer and must not import adapters, `chat`, `agent`, or `rag`.

## Armory layout

An armory is a normal directory with a fixed layout:

```
my-armory/
  .hephaistos/
    armory.toml         # armory marker and metadata
    system_prompt.md    # optional custom system prompt (replaces default persona)
    history             # shell history for this armory (created on use)
    memory.json         # extracted study memory
    rag_index.json      # persisted retrieval index
    traces/             # per-session JSONL traces
    usage/              # per-session usage/cost snapshots
  source/               # primary study material, indexed for RAG
  library/              # additional reference material, indexed for RAG
  notes/                # workspace notes the agent can edit
  chats/                # saved chat sessions
  parameters/           # reserved workspace parameters directory
```

Only `source/` and `library/` are used for retrieval. Hidden files inside those
directories are skipped by the materials scanner. `source/` is the folder for
primary study materials, `library/` is the folder for reference materials, and
`source` in citations or chunk metadata remains the provenance path.

## Study memory

Hephaistos is local-first by default: extracted study concepts are written to
`<armory>/.hephaistos/memory.json` and injected into future prompts so the
assistant can avoid repeating material the user already covered.

Users can opt in to Supermemory through `/memory setup`. When enabled,
Hephaistos writes extracted concepts to an armory-specific Supermemory
container tag and to a dedicated global study profile tag. This gives semantic
recall across armories while keeping setup explicit and reversible. If
Supermemory is disabled, unconfigured, or unavailable, session creation falls
back to the local JSON memory store.

## Diagnostics

Hephaistos uses local diagnostics that keep debugging data inside the CLI
workflow and armory workspace.

```mermaid
graph TD
    CLI[CLI session] --> Logs[Structured logs]
    CLI --> Traces[Armory trace files]
    CLI --> Profiles[CPU / memory profiles]

    Engine[chat.engine] --> Logs
    Orchestrator[chat.orchestrator] --> Traces

    Traces --> Armory[<armory>/.hephaistos/traces/]
    Profiles --> Cache[~/.cache/hephaistos/profiles/]
```

### Structured logging

- Configure with `HEPHAISTOS_LOG_LEVEL`, `HEPHAISTOS_LOG_FILE`, and `HEPHAISTOS_LOG_FORMAT`
- Secrets are scrubbed before logs or trace files are written
- Interactive sessions default to human-readable output; non-interactive runs default to JSON

### Trace files

- Each armory can keep append-only JSONL traces in `.hephaistos/traces/`
- Trace files capture session events, retrieval activity, tool calls, and LLM timing
- Plain chat mode skips armory trace files unless a workspace is attached

### Profiling

- `--profile` flag: CPU profiling via cProfile (stdlib)
- `--profile-memory` flag: memory profiling via tracemalloc (stdlib)
- `py-spy` available in dev dependencies for flame graphs
- Profiles saved to `~/.cache/hephaistos/profiles/`

<!-- sync-docs:privacy-diagnostics-architecture:start -->
## Privacy & Diagnostics

Hephaistos keeps privacy-impacting diagnostics optional and maintainer-facing.

- `hephaistos.diagnostics.events` sends anonymous PostHog events only when a backend is
  configured and the user explicitly opts in.
- `hephaistos.diagnostics.crashes` sends redacted Sentry crash reports only when a
  backend is configured and the user explicitly opts in.
- `hephaistos/privacy/release.py` is committed as a safe stub in the public
  repository. Official release and edge workflows overwrite it in CI before
  building artifacts.
- Source, editable, and Git installs stay bare by default. Forks and custom
  builds can wire their own endpoints with `HEPHAISTOS_POSTHOG_PROJECT_TOKEN`,
  `HEPHAISTOS_POSTHOG_HOST`, and `HEPHAISTOS_SENTRY_DSN`.
- Agents and contributors should preserve this split: diagnostics exist only for
  opt-in maintainer visibility into usage/errors and is never a required product
  dependency.
<!-- sync-docs:privacy-diagnostics-architecture:end -->

### Runbooks

Operational playbooks are in `docs/runbooks/`:
- [CI Failure](runbooks/ci-failure.md)
- [Slow LLM Response](runbooks/slow-llm-response.md)
- [Deployment Rollback](runbooks/deployment-rollback.md)
- [RAG Retrieval Issues](runbooks/rag-retrieval-issues.md)
