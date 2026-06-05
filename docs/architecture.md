# Architecture

Hephaion follows strict import boundaries enforced by `import-linter`. Source
packages live under `packages/` so stable product ownership is separated from
extension surfaces. Only adapter packages may import broadly; lower tiers must
stay copyable and must not depend on product workflows.

## Package ownership

The target package root mirrors the Pi-style split between the agent identity,
the harness, and extensible surfaces:

```
packages/
  heph/        App package: command entrypoint, identity, product composition
  hephaion/    Correctness harness: turns, grounding, citations, memory/study
  ai/          Providers, runtime, logging, palette, AI primitives
  interfaces/  CLI/TUI/terminal adapters
  extensions/  Extension contracts
```

Each package uses its own `src/` and `test/` tree where useful. Source folders
are flat by concern: `packages/ai/src/runtime`, `packages/interfaces/src/tui`,
`packages/heph/src/commands`, and `packages/hephaion/src/chat`, not duplicate
package-name wrappers. Heph is the thing the user talks to and the canonical
console command (`heph`), while `hephaion` remains a command alias. Hephaion is
the harness that prepares context, runs loops, validates grounding, streams
events, records state, and persists sessions.

The long-term goal is a closed kernel with an open extension plane. Heph and
Hephaion should know their own contracts well enough that a user can ask Heph to
add, remove, or adapt behavior through extension points. The user should not
need every personal workflow built into the core. Extension code can add tools,
prompts, workflows, or interface affordances, but it must compose stable
contracts instead of bypassing grounding, citation verification, memory scope, or
session persistence.

Heph-facing behavior should be open for extension through prompt/state files.
It should not learn about TUI keybindings, terminal details, provider internals,
or one-off phrase lists. Hephaion may enforce structure around Heph, but it
should not hardcode semantic dispatch for every possible user phrase.

## Architecture tiers

- **Heph app package**. This owns the console command target, product
  composition, Heph identity, and self-knowledge surfaces.
- **AI package**. This owns provider configuration/auth, model
  catalogs, runtime streaming, retry, usage, logging, palette, prompt-cache
  request shaping, and conversation/message primitives.
- **Domain reusable packages**: `materials`, `rag`, `memory`, `armory`, `vocab`,
  `study` under `hephaion`. These model harness state and materials but must not
  depend on app or adapter packages.
- **Application services**: `chat` and focused workflow modules. These compose
  AI/domain packages into session lifecycle, evidence, memory workflows, and
  turn orchestration inside the `hephaion` harness.
- **Interfaces**. This owns Textual TUI, CLI-facing terminal
  behavior, keybindings, transcript/composer/status rendering, and adapter
  diagnostics. It is not a reusable TUI framework. Interface packages may depend
  broadly, but reusable decisions should be promoted into services or domain
  packages instead of staying in adapter code.
  Interface modes should expose the same harness as interactive TUI,
  print/plain CLI, JSON streaming, and future RPC/process integration surfaces
  without duplicating core routing, validation, or extension decisions.
- **Extensions**. This package owns stable extension
  contracts for user tools, prompt/workflow hooks, and examples. User-modifiable
  behavior should depend on stable contracts, not modify Heph identity or
  Hephaion harness internals directly.

## Dependency flow

```mermaid
graph TD
    Heph[heph app] --> Interfaces[interface adapters]
    Heph --> Harness[hephaion harness]
    Heph --> AI[AI runtime and providers]
    Heph --> Extensions[extension contracts]
    Interfaces --> Harness
    Interfaces --> AI
    Interfaces --> Extensions
    Harness --> AI
    Harness --> Extensions
    Harness --> Materials[materials]
    Harness --> RAG[rag]
    Harness --> Study[study]
    Harness --> Memory[memory]
    Harness --> Agent[agent]
    RAG --> Materials
    AI -->|API calls| LLM[OpenAI / Anthropic / etc.]
    Harness -->|Armory and sessions| FileStore[Armory Files]
```

The top layer is the app surface: `heph` wires command entrypoints and composes
the interface adapters, harness, AI runtime, and extension contracts.
The `interfaces` package owns human and process adapters through flat source
concerns such as `terminal` and `tui`. Reusable packages communicate through
public APIs and must not import adapter packages. Shared LLM request primitives
live in `runtime` so chat, agent, memory, and study workflows do not import each
other just to share message types or streaming helpers.

## Core harness flow

The correctness-critical chat harness follows a narrow reusable flow:

```mermaid
graph LR
    Intent["intent classification"] --> Planning["turn planning"]
    Planning --> Evidence["evidence resolution"]
    Evidence --> Generation["generation / repair"]
    Generation --> Finalization["verification / finalization"]
```

- `chat.intent` owns the classifier schema, prompt contract, and payload parser.
  Intent handling must be structural and model-facing; it must not devolve into
  phrase-table semantic dispatch such as treating every greeting or overview
  wording as a separate code branch.
- `chat.turn_orchestrator` composes lifecycle, armory-turn setup, execution, and
  finalization mixins. `chat.orchestrator` keeps `TurnOrchestrator`,
  `iter_chat_events`, and `send_user_message` as public composition surfaces.
  Behavior-specific helpers should move into focused chat modules instead of
  growing the orchestrator.
- `chat.message_delivery` owns rendered one-shot sending, while
  `chat.session_persistence` owns session save behavior. This keeps
  `chat.session` and `chat.orchestrator` independent at runtime.
- `chat.evidence` owns retrieval resolution and assessment. Planning may request
  current, prior, or overview evidence, but it should not perform adapter work.
  Low-content filtering lives in `chat.evidence_text`; overview sampling lives
  in `chat.evidence_overview` so query retrieval, overview sampling, and
  assessment remain separate responsibilities.
- Generation and repair must remain grounded in `TurnEvidence`, citation
  verification, and structural reply checks before turn finalization records the
  result, usage, memory scheduling, and learning state changes.

Interfaces follow the same split as the Codex Rust layout: core services stay
reusable, while TUI/CLI/command surfaces compose them. TUI frame behavior such
as resize handling and terminal protocol support lives in `tui.resize`;
external slash-command and managed-resend execution lives in
`tui.external_commands`; generic inline-menu rendering/filtering lives in
`tui.inline_menu`; model picker label parsing lives in `tui.model_flow`.
Study prompt construction and turn-plan contracts live in `study.prompt_plans`,
while `study.controller` keeps learning routing and state transitions.
Priority scan orchestration remains in `study.priority`; analysis, progress,
web search, report, and rendering details live in focused priority modules.
Plugin registry and dynamic armory tool loading lives in `agent.tool_registry`.

## Package layout

```
packages/
  ai/
    ai_diagnostics/ Metrics and tracing primitives
    ai_logging/     Structured logging, redaction, trace writing
    ai_types/       Narrow payload type helpers
    palette/        Product color tokens
    providers/      LLM provider registry, config, auth, model catalogs
    runtime/        Chat config, messages, streaming, retry, usage
  extensions/
    extension_contracts.py  Stable user-extension/product-context contracts
  heph/
    cli/        Console entrypoint and top-level subcommands
    commands/   Slash-command registry and command coordinators
    product/    Product context bridge
    identity/   Stable self-description and conversational identity target
    prompts/    Prompt programs treated as code
    state/      Declarative JSON/Markdown state contract target
  hephaion/
    agent/       Prompt building, citation, tool registry/handlers
    armory/      Armory data, validation, and known-armory lookup
    chat/        Session lifecycle, intent contracts, evidence, turn orchestration
    diagnostics/ Anonymous events, local diagnostics, redacted crash reports
    matching/    Fuzzy matching helpers for human-facing selectors
    materials/   Study-file discovery, ignore rules, and material role classification
    memory/      Memory extraction and storage
    parameters/  Parameter management and settings
    privacy/     Consent, anonymous install ID, release-time diagnostics config
    rag/         RAG chunking, indexing, retrieval, source mapping
    safety/      Local safety contracts
    study/       Prompt plans, learning controller, priority analysis
    version/     Package version helpers
    vocab/       Vocabulary drill, scheduler, state
  interfaces/
    terminal/    Terminal I/O, styling, prompts, history, source opening
    tui/         Textual adapter: lifecycle, widgets, inline menus, rendering
```

## Import rules

### Forbidden: reusable packages must not import adapters

The following packages cannot import anything from adapter packages:
`cli`, `commands`, `tui`,
`terminal.history` or `terminal.input`.

- `chat`
- `agent`
- `providers`
- `rag`
- `armory`
- `study`
- `memory`
- `parameters`
- `materials`
- `runtime`
- `vocab`
- `ai_logging`
- `palette`
- `matching`

### Forbidden: logging and diagnostics must not import adapters

`ai_logging` and `diagnostics.crashes` must not import from
`cli`, `commands`, or `tui`.

### Independent: chat.session and chat.orchestrator

`chat.session` and `chat.orchestrator` must be independent at runtime (no direct runtime imports between them).

### Independent: materials

`materials` owns material discovery and ignore-policy parsing.
It must not import `chat`, `agent`, or `rag`.
`rag` may import `materials`, but that dependency
is one-way.

### Low level: runtime

`runtime` owns shared LLM primitives such as `ChatConfig`,
`Conversation`, message conversion, client construction, streaming completion,
and retry helpers. It must not import adapters, `chat`, `agent`, `rag`, `study`,
`materials`, `memory`, or `armory`. Providers may be used by runtime, but
providers must not import product workflow packages.

### Core: providers

`providers` owns provider configuration, model catalogs, registry
metadata, and key resolution. It must not import adapters, `chat`, `agent`,
`rag`, `study`, or `materials`.

### Domain: memory and study

`memory` may use `runtime` to extract concepts, but it must not
import adapters, `chat`, or `agent`. `study` stays a pure
controller/state layer and must not import adapters, `chat`, `agent`, or `rag`.

## Armory layout

An armory is a normal directory with a fixed layout:

```
my-armory/
  .hephaion/
    armory.toml         # armory marker and metadata
    system_prompt.md    # optional custom system prompt (replaces the default role prompt)
    history             # input history for this armory (created on use)
    memory.json         # extracted armory memory
    rag_index.json      # persisted retrieval index
    traces/             # per-session JSONL traces
    usage/              # per-session usage/cost snapshots
  materials/            # user study files, indexed for RAG
  parameters/           # reserved workspace parameters directory
```

Only `materials/` is used for retrieval. Hidden files inside that directory are
skipped by the materials scanner. `source` in citations or chunk metadata means
the provenance path for a retrieved chunk.

## Study memory

Hephaion is local-first by default: extracted study concepts are written to
`<armory>/.hephaion/memory.json` and injected into future prompts so the
assistant can avoid repeating material the user already covered.

Memory stays armory-scoped. `/status` includes the current armory session's
memory count when a local memory store is attached.

## Diagnostics

Hephaion uses local diagnostics that keep debugging data inside the CLI
workflow and armory workspace.

```mermaid
graph TD
    CLI[CLI session] --> Logs[Structured logs]
    CLI --> Traces[Armory trace files]
    CLI --> Profiles[CPU / memory profiles]

    Engine[runtime.engine] --> Logs
    Orchestrator[chat.orchestrator] --> Traces

    Traces --> Armory[<armory>/.hephaion/traces/]
    Profiles --> Cache[~/.cache/hephaion/profiles/]
```

### Structured logging

- Configure with `HEPHAION_LOG_LEVEL`, `HEPHAION_LOG_FILE`, and `HEPHAION_LOG_FORMAT`
- Secrets are scrubbed before logs or trace files are written
- Interactive sessions default to human-readable output; non-interactive runs default to JSON

### Trace files

- Each armory can keep append-only JSONL traces in `.hephaion/traces/`
- Trace files capture session events, user messages, retrieval activity, retrieved
  excerpts, material/tool metadata, and LLM timing
- Trace files are local armory data; recognized secrets are redacted before writing,
  but trace contents should still be treated as private when sharing an armory
- Plain chat mode skips armory trace files unless a workspace is attached

### Profiling

- `--profile` flag: CPU profiling via cProfile (stdlib)
- `--profile-memory` flag: memory profiling via tracemalloc (stdlib)
- `py-spy` available in dev dependencies for flame graphs
- Profiles saved to `~/.cache/hephaion/profiles/`

<!-- sync-docs:privacy-diagnostics-architecture:start -->
## Privacy & Diagnostics

Hephaion keeps privacy-impacting diagnostics optional and maintainer-facing.

- `diagnostics.events` sends anonymous PostHog events only when a backend is
  configured and the user explicitly opts in.
- `diagnostics.crashes` sends redacted Sentry crash reports only when a
  backend is configured and the user explicitly opts in.
- `packages/hephaion/src/privacy/release.py` is committed as a safe stub in the public
  repository. Official release and edge workflows overwrite it in CI before
  building artifacts.
- Source, editable, and Git installs stay bare by default. Forks and custom
  builds can wire their own endpoints with `HEPHAION_POSTHOG_PROJECT_TOKEN`,
  `HEPHAION_POSTHOG_HOST`, and `HEPHAION_SENTRY_DSN`.
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
