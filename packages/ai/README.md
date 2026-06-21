<p align="center">
  <img alt="Hephaion" src="https://raw.githubusercontent.com/gildrb/heph/main/docs/assets/logo-auto.svg" width="128">
</p>

# AI

AI is the provider and model runtime package. It owns the code that talks to LLM
providers and normalizes their behavior for the rest of the system. Like Pi's
AI package, it is substrate: most Heph features should not require touching it.

Use this package for:

- provider configuration, auth, API keys, OAuth, endpoints, and model catalogs;
- chat request payloads, streaming, retry, recovery, and usage accounting;
- provider-neutral diagnostics, logging, and payload type helpers.

Do not put Heph identity, research strategy, harness validation, armory
behavior, retrieval, citations, memory, commands, terminal rendering, or TUI
styling here.

## Source Layout

```text
src/
  ai/
    diagnostics/  Provider-neutral metric and tracing no-op surfaces
    logging/      Structured logging, redaction, and timers
    providers/    Provider config, auth, endpoints, catalogs, model metadata
    runtime/      Chat config, messages, streaming, retry, prompt cache, usage
    types/        Narrow runtime type guards for SDK payloads
```

The package is intentionally namespaced as `ai.*`, so each source directory can
use the short name that describes its responsibility.

## Boundaries

AI is below every Heph-specific package. It may know about provider SDKs and
generic runtime concerns, but it must not import `heph`, `hephaion`,
`interfaces`, or `extensions` code. Extend provider behavior through explicit
provider/runtime APIs rather than product-specific conditionals.

If code needs armory paths, citations, source files, learning memory, or UI
state, it is too high-level for AI.

## Development

```bash
uv run pytest --no-cov packages/ai/test
uv run python -m scripts.check_repo_policies
uv run lint-imports
```

## Related Docs

- [Root architecture guide](../../docs/architecture.md)
