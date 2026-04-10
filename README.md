# Hephaistos

Hephaistos is an armory-first study CLI. It attaches to an "armory" workspace that holds source material, retrieves relevant context via RAG, runs a guarded agent loop with tool access inside the workspace, verifies citations after each answer, and stores per-armory memory so repeated sessions stay grounded.

## Quickstart

### Requirements

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/)
- An API key for the provider you want to use

### Install dependencies

```bash
uv sync
```

To enable embedding retrieval and cross-encoder re-ranking:

```bash
uv sync --group rag
```

To enable document conversion (PDF, DOCX, PPTX, HTML) via [docling](https://github.com/docling-project/docling):

```bash
uv sync --group docling
```

### Create an armory and start a session

```bash
uv run hephaistos armory init ~/armories/demo
# add study files to ~/armories/demo/source or ~/armories/demo/library
uv run hephaistos chat start ~/armories/demo
```

If you `cd` into a valid armory first, `uv run hephaistos` will auto-attach it. Without arguments, Hephaistos opens the interactive shell only when stdin/stdout are TTYs; otherwise it prints CLI help.

### Configure an API key

You can either:

- set a provider-specific environment variable such as `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `ZAI_API_KEY`, or `CUSTOM_API_KEY`
- set a generic override with `HEPHAISTOS_API_KEY`
- start the shell and use `/api key <your-key>`

API keys are resolved from the OS keychain first, then environment variables, then a session-only in-memory override. They are not written to `providers.toml`.

### Install as a tool

```bash
uv tool install --force --editable .
heph
```

## How It Works

1. Create or open an armory workspace.
2. Put study material in `source/` or `library/`.
3. Start a chat in that armory.
4. For each question, Hephaistos builds or loads the RAG index, retrieves relevant chunks, injects them into the prompt, and runs the agent loop (LLM + tools).
5. After the reply, it verifies cited sources against what was actually retrieved, tracks usage/cost, and extracts durable memory entries from substantive exchanges.

If an armory has no source files, `chat start` will fail until you add material to `source/` or `library/`.

## Features

- Interactive TTY shell built on `prompt_toolkit` with a forge-inspired colour palette and live bottom toolbar
- Slash commands for armory/session/model/provider management
- Shell mode via `!command`, gated by autonomy tiers that classify the actual command
- Armory auto-discovery from the current directory or `./armory`
- Agent loop with `bash`, `read_file`, `write_file`, `edit_file`, `list_files`, `search_files`, `web_fetch`, and `compact`
- Steering — type while the agent is working to inject follow-up messages mid-loop
- Three-layer context compaction: silent micro-compact every turn, auto-compact at token thresholds, and manual `/compact`
- Citation verification against the sources actually retrieved for the answer
- Per-armory memory extraction stored in `.hephaistos/memory.json`
- Session usage and estimated cost tracking with model-specific pricing
- Context window budget management with compaction urgency warnings
- Structured logging plus per-session JSONL traces
- Multi-provider model switching with a built-in model registry (context windows, pricing, capabilities)
- TF-IDF retrieval by default; optional embedding/hybrid retrieval, cross-encoder re-ranking, and query transformation (HyDE, multi-query, keyword expansion) when extra dependencies are installed
- Document conversion for PDF, DOCX, PPTX, and HTML via optional `docling` integration
- Mutation queue serialising concurrent file writes per-path
- Keychain-based API key storage with lazy resolution

## Commands

### CLI

```text
hephaistos armory init <path>         Create a new armory workspace
hephaistos armory open <path>         Validate an existing armory
hephaistos chat start <path>          Start a new chat session in an armory
hephaistos chat resume <path> <id>    Resume a saved chat session
hephaistos chat list <path>           List saved chat sessions
```

The top-level CLI is shell-first, so `chat` is implemented but hidden from `hephaistos --help`.

### Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/status` | Show armory, session, model, memory, and usage state |
| `/save` | Save the current chat to the active armory |
| `/clear` | Start a fresh chat session |
| `/armory` | Open the armory management menu |
| `/model` | Show or switch the active model |
| `/provider` | Show or switch the active provider and model |
| `/models` | List the built-in model catalog across providers |
| `/api` | Inspect or set the API key / base URL |
| `/compact` | Summarize the conversation to free context |
| `/history` | Show turn counts and a token estimate |
| `/usage` | Show tracked token usage and estimated cost |
| `/edit` | Edit and resend the last user message |
| `/exit` | Leave the shell |

### Shell Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Alt+Enter` / `Esc+Enter` | Insert newline |
| `\` at end of line | Continue on the next line |
| `Up` / `Down` | Browse prompt history |
| `Tab` | Autocomplete slash commands |
| `Ctrl+C` | Cancel the current response |
| `Ctrl+D` | Exit the shell |
| `Ctrl+A` / `Ctrl+E` | Move to start / end of line |
| `Ctrl+U` / `Ctrl+K` | Clear to start / kill to end |

## Armory Layout

An armory is a normal directory with a fixed layout:

```text
my-armory/
  .hephaistos/
    armory.toml         # armory marker and metadata
    config.toml         # optional autonomy and permission overrides
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

Only `source/` and `library/` are used for retrieval. Hidden files inside those directories are skipped by the indexer.

## Configuration

### Provider configuration

Provider definitions live in `~/.config/hephaistos/providers.toml`. On first load, Hephaistos writes a default config with:

- `openrouter`
- `openai-codex`
- `zai`
- `custom`

The default active provider is `zai`. Switch providers in the shell with `/provider`, or switch models with `/model`.

### Autonomy tiers

Shell commands (`!`) and tool calls are gated by autonomy tiers. The system classifies each command by what it actually does rather than by tool name:

| Tier | Allows | Example |
|------|--------|---------|
| `none` | Read-only operations | `ls`, `cat`, `grep`, `git status` |
| `low` | Low-risk file ops | `touch`, `mkdir`, `cp`, `mv` |
| `medium` | Dev operations | `pip install`, `git commit`, `pytest` |
| `high` | Production / privileged | `sudo`, `git push`, `rm -rf` |

The default autonomy level is `low`. Override per-armory in `.hephaistos/config.toml`:

```toml
autonomy = "medium"
```

### Environment variables

| Variable | Description |
|----------|-------------|
| `HEPHAISTOS_API_KEY` | Generic API key override |
| `HEPHAISTOS_BASE_URL` | Override the API base URL |
| `HEPHAISTOS_MODEL` | Override the active model |
| `HEPHAISTOS_MAX_TOKENS` | Max output tokens per response |
| `HEPHAISTOS_RAG_CONTEXT_BUDGET` | Token budget for injected retrieval context |
| `HEPHAISTOS_MAX_RETRIES` | Max streaming retry attempts |
| `HEPHAISTOS_RETRY_BASE_DELAY` | Initial retry backoff in seconds |
| `HEPHAISTOS_RETRY_MAX_DELAY` | Max retry backoff in seconds |
| `HEPHAISTOS_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `HEPHAISTOS_LOG_FILE` | Optional append-only log file path |
| `HEPHAISTOS_LOG_FORMAT` | `json` or `text` for stderr logs |
| `HEPHAISTOS_EMBED_MODEL` | Override the embedding model used by retrieval |
| `HEPHAISTOS_RERANK_MODEL` | Override the reranker model when available |
| `OPENAI_API_KEY` | API key for the OpenAI-compatible provider path |
| `OPENROUTER_API_KEY` | API key for OpenRouter |
| `ZAI_API_KEY` | API key for Z.AI / GLM |
| `CUSTOM_API_KEY` | API key for the custom provider entry |

Defaults are stored in [`hephaistos/parameters/default.toml`](hephaistos/parameters/default.toml).

## Project Layout

```text
hephaistos/
  app/            CLI entrypoint, shell, commands, menus, display, palette
  armory/         armory creation and validation
  chat/           session lifecycle, engine, usage, persistence
  harness/        tool loop, permissions, compaction, citations, RAG
  memory/         learned-concept extraction and persistence
  parameters/     default parameter loading and env overrides
  providers/      provider config, model registry, keyring integration
  source/         public package entrypoint (re-exports CLI)
  logging.py      structured JSON logging and per-session trace writer
tests/            unit and integration tests
```

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## License

All rights reserved.
