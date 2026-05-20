<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->

# Hephaistos

**A local-first document agent that works with your files and any LLM.**

Hephaistos, or `heph`, is a terminal app for working with document-heavy projects.
Put files in an **armory**, start Heph, and ask questions. Heph retrieves from your
materials before answering, checks citations against the retrieved evidence, and keeps
memory scoped to that armory.

An armory is the core idea: a normal portable folder with your materials, saved chats,
retrieval index, and local memory. Your documents are not locked into a provider.

## Install

```bash
uv tool install heph@latest
heph
heph --version
```

Or with pip:

```bash
pip install heph
```

Upgrade with:

```bash
uv tool upgrade heph
```

Install from GitHub:

```bash
uv tool install git+https://github.com/gildrb/hephaistos
```

## Start

```bash
heph armory init ~/armories/exams
# add documents to ~/armories/exams/materials
heph start ~/armories/exams
```

You can also run:

```bash
heph start .
heph ~/armories/exams
```

From a source checkout, use `uv run heph`.

## Models

Use `/login` to connect OAuth or API-key access, then `/models` to choose from the
models available to those credentials.

Heph works with Pollinations AI, OpenRouter, OpenAI API keys, OpenAI Codex
subscription login, Z.AI, and custom OpenAI-compatible endpoints. You can also use
environment variables such as `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `ZAI_API_KEY`,
`CUSTOM_API_KEY`, `HEPHAISTOS_BASE_URL`, and `HEPHAISTOS_MODEL`.

## Commands

```text
heph start [path]       Open Heph.
heph armory init PATH   Create an armory.
heph index [path]       Refresh the materials index.
heph health [path]      Check indexed materials.
heph update             Show the update command.
```

Inside Heph, the important commands are `/login`, `/models`, `/armory`, `/evidence`,
`/memory`, `/settings`, and `/exit`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local development, tests, and pull request
guidelines.

## Safety

Analytics and crash reporting are opt-in from `/settings`. Source and Git installs do
not enable hosted diagnostics by default.

Model-generated shell commands are not exposed as a default agent tool. Explicit `!`
shell escapes and armory plugins should only be used in armories you trust.

## Next Steps

- Read the [CLI reference](cli-reference.md) for commands and keyboard shortcuts.
- Read the [architecture guide](architecture.md) for package boundaries and data flow.
- Read [agentic development](agentic-development.md) for agent-readiness conventions.
- Read the [runbooks](runbooks/index.md) for operational debugging.
