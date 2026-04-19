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

API keys are resolved in this order: `HEPHAISTOS_API_KEY`, OS keychain, OAuth credentials, provider-specific environment variable, then a session-only in-memory override. They are not written to `providers.toml`.

### Install as a tool

```bash
uv tool install --force --editable .
heph
```

## Features

- Interactive TTY shell built on `prompt_toolkit` with a forge-inspired palette, borderless dynamic composer, and live status rows beneath the input
- Slash commands for armory/session/model/provider management
- Shell mode via `!command`
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
- Persona switching — change agent tone per session (drill instructor, tutor, examiner, summarizer, debater) via `/persona`
- TF-IDF retrieval by default; optional embedding/hybrid retrieval, cross-encoder re-ranking, and query transformation (HyDE, multi-query, keyword expansion) when extra dependencies are installed
- Document conversion for PDF, DOCX, PPTX, and HTML via optional `docling` integration
- Mutation queue serialising concurrent file writes per-path
- Keychain-based API key storage with lazy resolution
