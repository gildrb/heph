# Heph

Heph is a local document harness. An **armory** is a folder with `materials/` and a private `.harness/` state directory. The terminal UI remains the primary interface; the CLI also supports scripts.

<p align="center">
  <img alt="Heph TUI" src="assets/app-screenshot.png" width="100%">
</p>

## Install

```sh
uv tool install heph
```

For a checkout:

```sh
uv sync
uv run heph --help
```

## Use an armory

```sh
heph armory init notes
cp notes.md ~/.armories/notes/materials/
heph index ~/.armories/notes
heph notes
```

The agent retrieves local material before answering and cites source paths and line numbers. It can read, search, edit, and write files inside the armory. Shell execution is disabled unless you explicitly trust the armory:

```sh
export HARNESS_TRUST_ARMORY_SHELL="$HOME/notes"
heph trust "$HOME/notes"
```

Set an OpenAI-compatible provider with `HEPH_BASE_URL`, `HEPH_API_KEY`, and `HEPH_MODEL`. Keyless local endpoints may leave the key empty.

## Design

The code has three runtime packages: `heph-ai` owns provider streaming, `harness` owns armories/retrieval/tools/sessions, and `heph` composes them. `interfaces` is the Textual adapter. Optional SDK, study workflows, hosted telemetry, and release automation are not part of the runtime.

State writes are armory-local, permission-restricted, and atomic. No hosted telemetry is collected.

## Development

```sh
uv sync
uv run pytest
uv run ruff check packages tests
```

See `CONTRIBUTING.md` and `SECURITY.md` for project policy.
