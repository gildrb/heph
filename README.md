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

Set an OpenAI-compatible provider with `HARNESS_BASE_URL` and `HARNESS_MODEL`. Use `/login` inside Heph to configure a custom endpoint and API key, or configure the provider key through its documented environment variable. Keyless local endpoints may leave the key empty.

## Run INTELLECT-MATH locally

`PrimeIntellect/INTELLECT-MATH` is a 7B Hugging Face checkpoint, not a hosted API. Run it behind an OpenAI-compatible server such as vLLM on an NVIDIA GPU:

```sh
uv pip install vllm
vllm serve PrimeIntellect/INTELLECT-MATH \
  --served-model-name intellect-math \
  --dtype bfloat16 \
  --max-model-len 4096 \
  --api-key heph
```

Start Heph with `heph` (or `uv run heph` from a checkout), then type `/login`, choose `CUSTOM`, and enter:

- Base URL: `http://127.0.0.1:8000/v1`
- Model: `intellect-math`
- API key: `heph`

The model does not provide a tool-call chat template. For armory sessions, set `HARNESS_FEATURE_FLAGS=disable_tools`; Heph still injects retrieved evidence, but will not send tool schemas the model cannot render.

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
