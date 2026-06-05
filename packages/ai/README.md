<p align="center">
  <img alt="Hephaion" src="https://gildrb.github.io/heph/logo-auto.svg" width="128">
</p>

# heph-ai

`heph-ai` is the low-level AI package for Heph. It owns provider configuration,
model metadata, API access, streaming runtime primitives, retry behavior, prompt
cache request shaping, token usage accounting, logging, diagnostics meters, and
terminal-neutral palette tokens.

This package must stay below the product, harness, and interface packages. Code
here should be portable AI infrastructure, not a place for armory workflows,
retrieval policy, citation behavior, slash commands, or TUI decisions.

## Package Role

Use `heph-ai` when a change is about:

- provider registration, auth, API keys, OAuth credential resolution, or model
  catalog hydration;
- request payload construction, runtime streaming, retry and circuit breaker
  behavior, prompt caching, usage, or cost accounting;
- AI-safe logging and diagnostics primitives that do not know about Heph
  sessions, armories, or interfaces;
- shared palette tokens that terminal and TUI adapters can render later.

Do not put code here when it needs to inspect armory files, run RAG, verify
citations, mutate learning memory, render UI, or route slash commands. Those
belong in `hephaion`, `heph`, or `heph-interfaces`.

## Import Surface

The exported module roots are flat and intentionally product-neutral:

```text
src/
  ai_diagnostics/  Metrics and tracing no-op surfaces
  ai_logging/      Structured logging, redaction, trace writing
  ai_types/        Narrow runtime type helpers
  palette/         Color tokens shared by adapters
  providers/       Provider config, catalogs, auth, key stores
  runtime/         ChatConfig, Conversation, streaming, retry, usage
```

Public imports should prefer package facades such as:

```python
from providers import ProviderConfig, get_registry
from runtime import ChatConfig, Conversation, stream_reply
```

Focused modules remain available for tests and implementation code when the
facade would hide an important boundary.

## Boundaries

`heph-ai` may depend on third-party SDKs and the Python standard library. It must
not import:

- `agent`, `armory`, `chat`, `materials`, `memory`, `rag`, `study`, or other
  harness/domain modules;
- `cli`, `commands`, `terminal`, or `tui`;
- user-facing Heph identity or extension implementation code.

Tests for harness behavior that use `agent` or `chat` belong under
`packages/hephaion/test`, even when they exercise AI runtime helpers. Keeping
those tests with the harness prevents the AI package from becoming an accidental
integration layer.

## Development

Run the focused package tests:

```bash
uv run pytest --no-cov packages/ai/test
```

Run the package policy and import checks after moving code across boundaries:

```bash
uv run python -m scripts.check_repo_policies
uv run lint-imports
```

When adding a provider, keep vendor-specific behavior isolated in `providers`
and request-shaping helpers. Higher layers should choose providers through
swappable config rather than hardcoded branches.

## Related Docs

- [Architecture](docs/architecture.md)
- [Workspace package map](../README.md)
- [Root architecture guide](../../docs/architecture.md)
