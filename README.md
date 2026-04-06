# Hephaistos

A chat-first, armory-based study CLI with an interactive terminal shell, LLM-powered agent loop, RAG context retrieval, and multi-provider model management.

## Quickstart

```bash
uv sync
uv run hephaistos
```

Running `hephaistos` (or `heph`) with no arguments opens the interactive chat shell in a TTY. Type a message to chat with the LLM, or use `/armory` to open the workspace menu (arrow keys or `j`/`k`, Enter to select). In non-interactive shells it prints help.

### Install as a tool

```bash
uv tool install --force --editable .
heph
```

## Features

- **Interactive TTY shell** — custom line editor with box-drawn UI, autocomplete, history, and multi-line input
- **Slash commands** — `/help`, `/status`, `/save`, `/clear`, `/armory`, `/model`, `/provider`, `/api`, `/compact`, `/history`, `/edit`, `/exit`
- **Shell mode** — prefix input with `!` to run a bash command (e.g. `!ls`)
- **Armory workspaces** — isolated folders with source material, chat history, and RAG index
- **Agent loop with tools** — when an armory is attached, the LLM can use `bash`, `read_file`, `write_file`, `edit_file`, and `list_files` to explore and modify the workspace
- **RAG context injection** — source files in armory `source/` and `library/` directories are chunked, indexed, and automatically retrieved as context for each question
- **Multi-provider support** — switch between OpenRouter, OpenAI Codex, Z.AI/GLM, and custom endpoints via `/provider` or `/model`
- **Streaming with retry** — real-time token streaming with exponential backoff and partial-content recovery on connection failures
- **Autonomy tiers** — bash commands are classified into permission tiers (`none` → `low` → `medium` → `high` → `unsafe`) based on actual operations
- **Session persistence** — chats are saved to armories and can be resumed later
- **Provider configuration** — stored in `~/.config/hephaistos/providers.toml`, auto-created with defaults

## Commands

### CLI subcommands

```
hephaistos armory init <path>     Create a new armory workspace
hephaistos armory open <path>     Validate and open an armory
hephaistos chat start <path>      Start a new chat session in an armory
hephaistos chat resume <path> <id> Resume a saved chat session
hephaistos chat list <path>       List saved sessions in an armory
```

### Slash commands (inside the shell)

| Command | Description |
|---------|-------------|
| `/help` | Show available commands and shortcuts |
| `/status` | Show armory, session, model, and mode info |
| `/save` | Save current chat to the armory |
| `/clear` | Start a fresh chat session |
| `/armory` | Open the armory management menu |
| `/model` | Show or switch the active model |
| `/provider` | Show or switch LLM provider and model |
| `/api` | Set or inspect API key and base URL |
| `/compact` | Summarize conversation to reduce context size |
| `/history` | Show conversation turn count and token estimate |
| `/edit` | Edit and resend the last user message |
| `/exit` | Leave the shell |

### Shell shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `⌥Enter` / `Esc+Enter` | Insert newline (multi-line input) |
| `\\` at end of line | Continue on next line |
| `↑` / `↓` | Browse input history |
| `Tab` | Autocomplete slash commands |
| `Ctrl+C` | Cancel current response |
| `Ctrl+D` | Exit shell |
| `Ctrl+A` / `Ctrl+E` | Home / End |
| `Ctrl+U` / `Ctrl+K` | Clear to start / Kill to end |

## Armory Structure

An armory is a folder with a `.hephaistos/marker.json` file that acts as a workspace for study sessions:

```text
my-armory/
  .hephaistos/
    marker.json          # armory metadata (created_at)
    config.toml          # optional overrides (autonomy, etc.)
    rag_index.json       # persisted chunk index
    history.json         # shell input history
    chats/               # saved chat sessions
  source/                # source material (auto-indexed for RAG)
  library/               # additional reference material
```

## Configuration

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEPHAISTOS_API_KEY` | — | API key (falls back to `OPENAI_API_KEY`) |
| `HEPHAISTOS_BASE_URL` | `https://api.openai.com/v1` | API base URL |
| `HEPHAISTOS_MODEL` | `gpt-4o-mini` | Model name |
| `HEPHAISTOS_MAX_TOKENS` | `4096` | Max response tokens |

### Provider config

Providers are managed via `/provider` or `/model` in the shell and persisted to `~/.config/hephaistos/providers.toml`. Default providers include OpenRouter, OpenAI Codex, Z.AI/GLM, and a custom endpoint option.

### Project parameters

Default model settings are stored in `hephaistos/parameters/default.toml` and can be overridden per-armory.

## Project Layout

```text
hephaistos/
  app/             CLI entrypoint, shell, line editor, menu, commands, display, autocomplete, history
  armory/          Workspace init, validation, storage
  chat/            LLM engine, conversation, session management, chat storage
  harness/
    dispatch.py    Agent loop (tool-call → execute → continue)
    tools.py       Tool schemas and handlers (bash, read/write/edit/list)
    permissions.py Autonomy tier classification and enforcement
    rag/           Chunking, indexing, retrieval, context building
  providers/       Multi-provider configuration
  parameters/      TOML config loading and env overrides
  source/          Domain logic CLI module (placeholder)
  logging.py       Structured logging and trace writer
tests/
  test_app_menu.py, test_app_shell.py
  test_armory_cmd.py, test_armory_lib.py
  test_chat_engine.py, test_chat_storage.py
  test_cli_integration.py
  test_harness.py
  test_rag_chunker.py, test_rag_context.py, test_rag_index.py, test_rag_retrieve.py
  test_stream_recovery.py
  test_logging.py
```

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
```

## Dependencies

- Python ≥ 3.13
- [openai](https://github.com/openai/openai-python) — API client (core)
- [sentence-transformers](https://www.sbert.net/) — local embeddings (optional, for RAG)

## License

All rights reserved.
