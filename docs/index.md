<!-- Managed by scripts/sync_docs.py. Do not edit directly. -->

# Hephaion

**Hephaion is a local document harness for accurate, cited answers.**

Hephaion is the harness: the tool you install, run, and write in. Inside it,
the agent (Heph) helps you understand and work with document-heavy projects
without handing your files to a hosted workspace. Put materials in an **armory**,
start Heph with `heph`, and ask questions. Heph retrieves from your files before
answering, checks citations against the retrieved evidence, and keeps memory
scoped to that armory.

Heph is the part that reasons over the material, asks follow-up questions, tests
your understanding, and keeps long sessions grounded. Hephaion provides the
guardrails around that agent: retrieval, citation checks, memory scoping, and
model/provider boundaries. Accuracy, verification, and privacy come first; model
choice stays swappable.

An armory is the core idea: a normal portable folder with your source files, saved
chats, retrieval index, and local memory. Your documents are not locked into a
provider.

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

PDF, DOCX, PPTX, and XLSX conversion support is built in through Docling so
new armories can index common study materials without extra setup.

Upgrade with:

```bash
uv tool upgrade heph
```

Install from GitHub:

```bash
uv tool install git+https://github.com/gildrb/heph
```

## Start

```bash
heph armory init exams
# add documents to ~/.armories/exams/materials
heph exams
```

Heph stores named armories under `~/.armories`. To move to another PC, install
Heph there, copy or sync the `.armories` folder, set up provider credentials,
and run `heph`.

You can also run Heph from an explicit armory path when needed:

```bash
heph .
heph ~/.armories/exams
```

From a source checkout, use `uv run heph`.

## Models

Use `/login` to connect OAuth or API-key access, then `/models` to choose from the
models available to those credentials.

Heph works with Pollinations AI, OpenRouter, OpenAI API keys, OpenAI Codex
subscription login, Z.AI, local tool-capable llama.cpp models, and custom
OpenAI-compatible endpoints. You can also use environment variables such as
`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `ZAI_API_KEY`, `CUSTOM_API_KEY`,
`HEPHAION_BASE_URL`, and `HEPHAION_MODEL`.

## Commands

```text
heph [name-or-path]     Open Heph.
heph armory init NAME   Create an armory in ~/.armories.
heph index [path]       Refresh the materials index.
heph health [path]      Check indexed materials.
heph local status       Show local llama.cpp status.
heph update             Show the update command.
```

Inside Heph, the important commands are `/login`, `/local`, `/models`, `/armory`,
`/materials`, `/keymap`, `/detach`, `/evidence`, `/turn`, `/settings`, and `/exit`.

## Docs

- [getting-started.md](getting-started.md) — first armory and materials walkthrough
- [armories.md](armories.md) — portable armory layout and local storage
- [cli-reference.md](cli-reference.md) — CLI commands, slash commands, and environment variables
- [configuration.md](configuration.md) — provider and model configuration
- [models.md](models.md) — provider choices, model selection, and API keys
- [privacy.md](privacy.md) — local-first storage, diagnostics, and network behavior
- [architecture.md](architecture.md) — package boundaries and data flow
- [troubleshooting.md](troubleshooting.md) — common setup, indexing, and provider issues
- [developers/index.md](developers/index.md) — developer docs and internal guides
- [developers/runbooks/index.md](developers/runbooks/index.md) — operational debugging runbooks
- [../CONTRIBUTING.md](../CONTRIBUTING.md) — repo layout, development workflow, and contribution guidelines

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for local development, tests, and pull request
guidelines.

## Safety

Analytics and crash reporting are opt-in from `/settings`. Source and Git installs do
not enable hosted diagnostics by default.

Model-generated terminal commands are not exposed as a default agent tool. Explicit
`!` terminal escapes and armory plugins should only be used in armories you trust.

## Next Steps

- Read the [CLI reference](cli-reference.md) for commands and keyboard shortcuts.
- Read the [architecture guide](architecture.md) for package boundaries and data flow.
- Read [agentic development](developers/agentic-development.md) for agent-readiness conventions.
- Read the [runbooks](developers/runbooks/index.md) for operational debugging.
