# heph-ai Architecture

`heph-ai` is the foundation package for model access and runtime primitives. It
should be understandable and useful without importing the Heph app, the
Hephaion harness, or any interface adapter.

## Ownership

The package owns:

- `providers`: provider config, model registry, model availability, OAuth/API
  key resolution, and provider-specific request profile helpers;
- `runtime`: message types, `ChatConfig`, conversations, streaming completion,
  retry/circuit breaker behavior, prompt-cache request shaping, and token usage;
- `ai_logging`: structured logging, redaction, timers, and trace writing;
- `ai_diagnostics`: no-op metrics/tracing surfaces that higher packages can
  call without taking a hosted diagnostics dependency;
- `ai_types`: narrow type guards for SDK payloads;
- `palette`: product color tokens that adapters may render.

## Dependency Direction

Allowed direction:

```text
heph / interfaces / hephaion
        -> heph-ai

runtime -> providers
runtime -> ai_logging / ai_diagnostics / ai_types
providers -> ai_logging / ai_types / palette
```

Forbidden direction:

```text
heph-ai -> hephaion
heph-ai -> heph
heph-ai -> heph-interfaces
heph-ai -> heph-extensions
```

Tests in this package follow the same rule. Integration tests that need
`agent`, `chat`, `rag`, or other harness modules belong in
`packages/hephaion/test`.

## Migration Pressure

Move code into `heph-ai` only when it is genuinely product-neutral AI
infrastructure. If a helper needs armory paths, citations, learning state, or
interface text, it is too high-level for this package.
