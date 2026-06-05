# AI Architecture

AI is the provider and model runtime package. It should be understandable and
useful without importing Heph, Hephaion, Interfaces, or Extensions. Treat it as
API substrate: it should almost never change for Heph-specific behavior.

## Ownership

The package owns:

- `ai.providers`: provider config, model registry, model availability, OAuth/API
  key resolution, and provider-specific request profile helpers;
- `ai.runtime`: message types, `ChatConfig`, conversations, streaming completion,
  retry/circuit breaker behavior, prompt-cache request shaping, and token usage;
- `ai.logging`: structured logging, redaction, and timers;
- `ai.diagnostics`: no-op metrics/tracing surfaces that higher packages can
  call without taking a hosted diagnostics dependency;
- `ai.types`: narrow type guards for SDK payloads.

## Dependency Direction

Allowed direction:

```text
heph / hephaion / interfaces -> ai

ai.runtime -> ai.providers
ai.runtime -> ai.logging / ai.diagnostics / ai.types
ai.providers -> ai.logging / ai.types
```

Forbidden direction:

```text
ai -> hephaion
ai -> heph
ai -> interfaces
ai -> extensions
ai -> palette
```

Tests in this package follow the same rule. Integration tests that need
`agent`, `chat`, `rag`, or other harness modules belong in
`packages/hephaion/test`.

## Migration Pressure

Move code into AI only when it is genuinely provider/model runtime
infrastructure. If a helper needs armory paths, citations, learning state,
research strategy, Heph identity, or interface text, it is too high-level for
this package.
