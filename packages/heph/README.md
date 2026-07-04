<p align="center">
  <img alt="Heph" src="https://raw.githubusercontent.com/gildrb/heph/main/assets/logo-auto.svg" width="240">
</p>

# Heph

Heph CLI is a local document agent. It indexes files in an armory, answers from
those files, and shows the cited source passages.

Heph is built around normal folders. An armory keeps your documents in
`materials/` and Heph-owned local state in `.harness/`, so the workspace stays
portable and inspectable.

## What Heph Does

- Answers from local armory materials with verifiable citations.
- Indexes PDFs, Office documents, notes, code, and other supported text sources.
- Opens retrieved evidence and source context from the terminal UI.
- Keeps chats, retrieval indexes, memory, traces, and usage snapshots in local
  armory state.
- Lets provider and model choices remain configurable instead of hardcoded.
- Exposes a Python SDK for native apps, GUI shells, and automation.

## Install

```bash
uv tool install heph@latest
```

You can also install with pip:

```bash
pip install heph
```

Heph requires Python 3.13 or newer.

## Update

```bash
heph update
heph --version
```

## Quick Start

```bash
heph armory init my-notes
cp ~/Downloads/example.pdf ~/.armories/my-notes/materials/
heph my-notes
```

Inside Heph, ask questions about your materials. When Heph cites evidence, use
the Evidence panel or `/evidence` command to inspect the cited source context.

## Trust Model

Heph is local-first beta software. Source files remain in your armory, and
memory is scoped to that armory unless you explicitly choose to move or share
state. Analytics and crash reporting are opt-in from `/settings`.

Model providers may receive prompt content when selected for a turn. Review
[Trust and ownership](https://github.com/gildrb/heph/blob/main/docs/trust.md)
and [Privacy](https://github.com/gildrb/heph/blob/main/docs/privacy.md) for the
full data, cache, prompt, and compute contract.

## Docs

- [Getting started](https://github.com/gildrb/heph/blob/main/docs/getting-started.md)
- [Armories](https://github.com/gildrb/heph/blob/main/docs/armories.md)
- [CLI reference](https://github.com/gildrb/heph/blob/main/docs/cli-reference.md)
- [Configuration](https://github.com/gildrb/heph/blob/main/docs/configuration.md)
- [Models](https://github.com/gildrb/heph/blob/main/docs/models.md)
- [SDK](https://github.com/gildrb/heph/blob/main/docs/sdk.md)
- [Troubleshooting](https://github.com/gildrb/heph/blob/main/docs/troubleshooting.md)

## Development

The public package bundles the Heph CLI, harness, AI runtime, interfaces, and
extension contracts into one installable distribution. Repository development
still keeps those layers separated under `packages/`.

```bash
uv run pytest --no-cov packages/heph/test
uv run heph --help
uv run python -m scripts.check_repo_policies
uv run lint-imports
```
