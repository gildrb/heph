# Hephaistos (Learning Build Guide)

This repo is for building a **CLI study app** in Python:

- LLM-provider agnostic (OpenAI/Anthropic/Gemini via adapters)
- Local folder-based armories (portable like Obsidian vaults)
- Markdown-first data format
- PDF lecture/exercise ingestion for grounded Q&A
- Interactive parameter controls (like `/parameters`)

You said you want to do the coding yourself, so this README is a **step-by-step implementation path**.

## Your Goal (v1)

Build a Python CLI app where a user can:

1. Create/open a study armory folder.
2. Add PDFs (lectures/exercises).
3. Chat with an LLM using armory context.
4. Switch provider/model without changing app logic.
5. Tweak advanced params interactively with `/parameters`.
6. Store everything as readable Markdown files.

Current CLI behavior:

1. Running `heph` or `hephaistos` with no arguments opens an interactive main menu.
2. Running with arguments (for example, `heph armory init ./my-armory`) dispatches directly.

## Minimal Dependency Baseline

Keep v1 intentionally small:

1. `argparse` (stdlib) for CLI parsing.
2. `httpx` for provider API calls.
3. `pytest` (dev dependency) for lightweight regression tests.

Do not add more dependencies until a concrete feature blocks you.

## Architecture Map (Mole-style Mental Model)

Use this mapping while building:

1. `bin` -> generated executables from `[project.scripts]` (`heph`, `hephaistos`).
2. `app` -> global CLI parser, entrypoints, and interactive startup menu (`src/hephaistos/app/`).
3. feature packages -> command wiring + use-cases + storage for each domain (`armory/`, `source/`, `chat/`, `parameters/`).
4. `shared` -> cross-feature helpers and base errors (`src/hephaistos/shared/`).
5. `scripts` -> dev/install helpers (`scripts/`).
6. `tests` -> unit/integration checks (`tests/`).

## Suggested Final Folder Structure

```text
Hephaistos/
  README.md
  pyproject.toml
  .gitignore
  src/
    hephaistos/
      __init__.py
      __main__.py
      app/
        cli.py
        menu.py
        aliases.py
      armory/
        cli.py
        service.py
        storage.py
        types.py
      source/
        cli.py
        service.py
        storage.py
        types.py
      chat/
        cli.py
        service.py
        session_store.py
        slash_commands.py
        repl.py
        types.py
      parameters/
        cli.py
        service.py
        store.py
        types.py
      shared/
        errors.py
        paths.py
        io.py
  tests/
    test_armory_lib.py
    test_armory_cmd.py
    test_cli_integration.py
```

## Current State Alignment (Because You Used `uv init`)

Keep only one package location: `src/hephaistos/`.
Keep command entrypoints in `src/hephaistos/app/` and feature behavior in feature folders (`armory/`, `source/`, `chat/`, `parameters/`).

## How To Build It (Do In This Exact Order)

### Step 1: Bootstrap the codebase

Create:

- `pyproject.toml`
- `.gitignore`
- `src/hephaistos/__main__.py`
- `src/hephaistos/app/cli.py`

What to implement:

1. CLI entry command `hephaistos`.
2. A simple `--help`.
3. Set `[project.scripts]` to `hephaistos = "hephaistos.app.cli:main"` in `pyproject.toml`.
4. No business logic yet.

Done when:

- `uv run hephaistos --help` works.

---

### Step 2: Define shared + feature types first

Create:

- `src/hephaistos/shared/errors.py`
- `src/hephaistos/armory/types.py`

Define dataclasses (stdlib) for:

- `ArmoryInfo`
- `SourceItem`
- `ChatSessionRef`
- `ParameterProfile`

Done when:

- You can import these types from anywhere with no circular imports.

---

### Step 3: Build armory feature package

Create:

- `src/hephaistos/armory/cli.py`
- `src/hephaistos/armory/service.py`
- `src/hephaistos/armory/storage.py`

Implement:

1. `armory init <path>` creates required folders.
2. `armory open <path>` validates structure.
3. Marker + layout validation helpers.

Done when:

- You can create an armory and inspect folders manually.

---

### Step 4: Add shared filesystem safety helpers

Create:

- `src/hephaistos/shared/io.py`

Implement:

1. Atomic write (temp file + rename).
2. Add lock/conflict policy later when sync is implemented.
3. Keep write path centralized in shared helpers.

Done when:

- Writes are abstracted in one shared place, not duplicated by feature.

---

### Step 5: Build provider abstraction (before any real API calls)

Create:

- `src/hephaistos/providers/base.py`
- `src/hephaistos/providers/registry.py`
- `src/hephaistos/providers/parameter_map.py`

Implement:

1. `ProviderAdapter` interface.
2. Provider registry lookup by name.
3. Parameter normalization per provider.

Done when:

- A fake provider adapter can pass through the system.

---

### Step 6: Add auth storage (API keys first)

Create:

- `src/hephaistos/auth/base.py`
- `src/hephaistos/auth/keychain_store.py`
- `src/hephaistos/auth/oauth_stub.py`

Implement:

1. Credential store interface.
2. Keychain-backed implementation.
3. OAuth placeholder (interface only, minimal stub).

Done when:

- You can set/get API keys without storing secrets in armory Markdown.

---

### Step 7: Implement real provider adapters

Create:

- `src/hephaistos/providers/openai_adapter.py`
- `src/hephaistos/providers/anthropic_adapter.py`
- `src/hephaistos/providers/gemini_adapter.py`

Implement:

1. Auth header creation.
2. Request mapping from `ChatRequest`.
3. Response parsing to `ChatResponse`.
4. Retry + timeout behavior.

Done when:

- You can run one chat call against each provider using the same internal request type.

---

### Step 8: Build chat orchestration service

Create:

- `src/hephaistos/chat/service.py`

Implement:

1. Load active armory/session.
2. Merge saved parameter profile + per-session overrides.
3. Call retrieval (later) + provider adapter.
4. Append messages to chat Markdown.

Done when:

- A full user->assistant turn persists in a chat file.

---

### Step 9: Implement CLI chat REPL and slash commands

Create:

- `src/hephaistos/chat/repl.py`
- `src/hephaistos/chat/slash_commands.py`
- `src/hephaistos/chat/cli.py`
- `src/hephaistos/parameters/cli.py`

Implement:

1. Chat loop for normal messages.
2. Slash command router.
3. `/parameters` interactive selector.
4. Parameter profile save/apply/list.

Done when:

- You can switch params without editing files manually.

---

### Step 10: Add PDF ingestion pipeline

Create:

- `src/hephaistos/ingest/pdf_extract.py`
- `src/hephaistos/ingest/chunking.py`
- `src/hephaistos/ingest/pipeline.py`
- `src/hephaistos/source/cli.py`

Implement:

1. Add PDF to `sources/`.
2. Extract text with fallback strategy.
3. Chunk content and write to `library/*.md`.

Done when:

- A PDF becomes searchable Markdown chunks with source/page metadata.

---

### Step 11: Add retrieval and grounding

Create:

- `src/hephaistos/retrieval/index.py`
- `src/hephaistos/retrieval/search.py`
- `src/hephaistos/retrieval/context_builder.py`

Implement:

1. Build lexical index from `library/`.
2. Retrieve top-k chunks by query.
3. Inject context + citations into chat request.

Done when:

- Responses cite specific source chunks/pages.

---

### Step 12: Add config and parameter profile storage

Create:

- `src/hephaistos/config/app_config.py`
- `src/hephaistos/config/parameters_store.py`

Implement:

1. Global app config (defaults, provider selection).
2. Armory-level parameter profile files.
3. Session override precedence rules.

Done when:

- Parameter resolution is deterministic and testable.

---

### Step 13: Write tests while stabilizing behavior

Create tests in `tests/`:

1. `test_armory_layout.py`
2. `test_markdown_roundtrip.py`
3. `test_conflict_writes.py`
4. `test_parameters_command.py`
5. `test_pdf_ingest_pipeline.py`
6. `test_retrieval_search.py`

Done when:

- Core flow is covered: init armory -> ingest PDF -> ask question -> persist cited answer.

---

### Step 14: Final polish for v1

Implement:

1. Friendly error messages (missing key, invalid model, empty context).
2. Logging with secret redaction.
3. Clear CLI help text for each command.
4. Example armory in docs.

Done when:

- A new user can clone repo and run first chat in under 10 minutes.

## Development Workflow (How You Should Manage The Work)

Use small slices and commit often:

1. One step above = one branch or one tight commit sequence.
2. Run tests after each step, not only at the end.
3. Keep files focused (one responsibility per file).
4. Prefer readability over cleverness.

Recommended commit rhythm:

1. `chore: bootstrap cli skeleton`
2. `feat: add core domain types`
3. `feat: add armory init/open and markdown io`
4. `feat: add atomic writes and conflict handling`
5. `feat: add provider interface and registry`
6. `feat: add provider adapters`
7. `feat: add repl and slash commands`
8. `feat: add pdf ingestion and retrieval`
9. `test: add core integration and unit tests`

## Rules You Should Follow While Coding

1. Never store secrets in armory Markdown files.
2. Canonical user data must stay Markdown.
3. Never silently overwrite conflicts.
4. Keep provider-specific logic inside `providers/`.
5. Keep CLI parsing separate from business logic.
6. Write tests for all file-write paths and parsing logic.

## MVP “Definition of Done”

You are done with v1 when all are true:

1. `hephaistos armory init` creates a valid armory.
2. `hephaistos source add lecture.pdf` ingests to Markdown chunks.
3. `hephaistos chat new` starts a session.
4. `/parameters` lets you interactively set advanced params.
5. Provider can be changed without changing chat service code.
6. Chat answers persist to Markdown with citations.
7. Conflict writes create explicit `.conflict-*` files.

## What To Do Next (First 3 Actions)

1. Create `pyproject.toml` + CLI skeleton (`Step 1`).
2. Implement `src/hephaistos/shared/errors.py` and `src/hephaistos/armory/storage.py` (`Steps 2-3`).
3. Add first tests for armory init and markdown roundtrip (`Step 13 subset early`).
