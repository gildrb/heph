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
provider. Current armories keep Hephaion state in `.hephaion/`; armories created
before the rename with `.hephaistos/` state are migrated automatically when opened.

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
uv tool install git+https://github.com/gildrb/heph
```

## Start

```bash
heph armory init exams
# add documents to ~/.armories/exams/materials
heph exams
```

You can also run:

```bash
heph .
heph ~/.armories/exams
```

From a source checkout, use `uv run heph`.

## Models

Use `/login` to connect OAuth or API-key access, then `/models` to choose from the
models available to those credentials.

Heph works with Pollinations AI, OpenRouter, OpenAI API keys, OpenAI Codex
subscription login, Z.AI, and custom OpenAI-compatible endpoints. You can also use
environment variables such as `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `ZAI_API_KEY`,
`CUSTOM_API_KEY`, `HEPHAION_BASE_URL`, and `HEPHAION_MODEL`.

## Commands

```text
heph [path]             Open Heph.
heph armory init PATH   Create an armory.
heph index [path]       Refresh the materials index.
heph health [path]      Check indexed materials.
heph update             Show the update command.
```

Inside Heph, the important commands are `/login`, `/models`, `/armory`, `/evidence`,
`/settings`, and `/exit`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local development, tests, and pull request
guidelines.

## Safety

Analytics and crash reporting are opt-in from `/settings`. Source and Git installs do
not enable hosted diagnostics by default.

Model-generated terminal commands are not exposed as a default agent tool. Explicit
`!` terminal escapes and armory plugins should only be used in armories you trust.

## License

This project is licensed under the [GNU General Public License v3.0 only](LICENSE).
