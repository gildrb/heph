# Chat engine

The chat engine is the low-level LLM communication layer. It wraps the OpenAI Python SDK to provide streaming completions with automatic retry, circuit breaking, and token usage tracking. Every higher-level system — the agent harness, the turn orchestrator, the session manager — ultimately calls through `stream_completion()`.

## Purpose

- Make streaming LLM calls to any OpenAI-compatible endpoint (OpenAI, OpenRouter, Pollinations, Z.AI, custom).
- Handle transient failures (connection drops, timeouts, rate limits) with exponential backoff and a circuit breaker.
- Preserve partial responses when a stream is interrupted mid-delivery (`StreamRecoveryError`).
- Track token usage and latency via the observability layer.

## Directory layout

```
hephaistos/chat/
├── engine.py          # ChatConfig, stream_completion(), RetryConfig, StreamRecoveryError
├── resilience.py      # CircuitBreaker, CircuitState, is_network_error()
├── orchestrator.py    # TurnOrchestrator — single-turn orchestration with RAG
├── session.py         # ChatSession lifecycle (see session-management.md)
├── storage.py         # File-based chat persistence
├── titles.py          # Auto-generate session titles from first exchange
├── usage.py           # TokenUsage, SessionUsage, ContextBudget, cost estimation
├── events.py          # Typed turn events (AssistantDeltaEvent, ToolCallEvent, etc.)
├── _api_types.py      # Shared API message types
└── cli.py             # Chat-specific CLI subcommands
```

## Key abstractions

| Abstraction | File | Purpose |
|---|---|---|
| `ChatConfig` | `hephaistos/chat/engine.py` | Dataclass holding model, base URL, max tokens, feature flags, and a provider reference for lazy key resolution |
| `RetryConfig` | `hephaistos/chat/engine.py` | Controls retry behaviour: max retries, base/max delay |
| `CircuitBreaker` | `hephaistos/chat/resilience.py` | Thread-safe state machine (CLOSED → OPEN → HALF_OPEN) that blocks calls after `failure_threshold` consecutive failures |
| `StreamRecoveryError` | `hephaistos/chat/engine.py` | Exception carrying `partial_content` when a retry fails after output was already streamed |
| `CompletionDelta` | `hephaistos/chat/engine.py` | A single streamed chunk: content, tool_calls, finish_reason, usage |
| `Conversation` | `hephaistos/chat/engine.py` | Ordered list of `Message` objects with an API-format cache |

## How it works

### Streaming flow

1. `stream_completion()` is called with a `ChatConfig`, messages, and optional tools/abort event.
2. `_build_client()` creates an OpenAI SDK client. It validates the model against the endpoint, resolves the API key lazily via `resolved_api_key`, and detects keyless endpoints (Pollinations).
3. The circuit breaker is checked. If OPEN, the call is rejected immediately.
4. For each retry attempt (up to `RetryConfig.max_retries`):
   - An OpenAI `chat.completions.create(stream=True)` call is made.
   - Chunks are yielded as `CompletionDelta` events.
   - If a transient error occurs before any output (`saw_output == False`), the attempt is retried with exponential backoff + jitter.
   - If a transient error occurs after output was already streamed, a `StreamRecoveryError` is raised carrying the partial content.
   - On success, the circuit breaker records success and usage metrics are emitted.
5. Token usage from the final chunk is recorded via `_record_usage()`.

### Key resolution

`ChatConfig.resolved_api_key` delegates to `resolve_key()` in `hephaistos/providers/keyring_store.py`, which follows the chain: OS keychain → OAuth token → environment variable → volatile in-memory store. See [authentication.md](authentication.md).

### Keyless endpoints

`is_keyless_endpoint()` detects providers that don't require API keys (currently only `https://text.pollinations.ai/openai`). For these, a placeholder `"no-key-required"` key is used.

### Circuit breaker

The `CircuitBreaker` (in `hephaistos/chat/resilience.py`) uses three states:
- **CLOSED**: Normal operation. Failures increment `_failure_count`.
- **OPEN**: Blocking. After `failure_threshold` (default 5) consecutive failures, all calls are rejected. Transitions to HALF_OPEN after `recovery_timeout` (default 60s).
- **HALF_OPEN**: One probe call is allowed. If it succeeds, the circuit closes. If it fails, the circuit reopens.

### Account setup errors

Some errors (authentication failures, billing issues) are not retryable. `_is_account_setup_error()` detects these and raises immediately with a user-facing hint suggesting `/api key`, `/provider`, or `/login`.

### Observability integration

The engine integrates with `hephaistos/observability.py` for:
- **Tracing**: `llm.completion` spans with model, latency, and error attributes.
- **Metrics**: `llm.request.duration` histogram and `llm.token.usage` counter.

## Integration points

- **Agent harness** (`hephaistos/harness/dispatch.py`): Calls `stream_completion()` inside the model/tool loop.
- **Turn orchestrator** (`hephaistos/chat/orchestrator.py`): Wraps the engine for single-turn RAG + tool orchestration.
- **Provider config** (`hephaistos/providers/config.py`): Calls `apply_to_config()` to set base URL, model, and provider reference on `ChatConfig`.
- **Resilience** (`hephaistos/chat/resilience.py`): `CircuitBreaker` used as `_circuit_breaker` module singleton.
- **Observability** (`hephaistos/observability.py`): No-op tracers and meters in source builds; CI-injected telemetry in releases.

## Key source files

| File | Lines | Role |
|---|---|---|
| `hephaistos/chat/engine.py` | ~650 | Core engine: config, streaming, retry, key resolution |
| `hephaistos/chat/resilience.py` | ~180 | Circuit breaker and network error detection |
| `hephaistos/chat/orchestrator.py` | ~470 | Single-turn orchestration with RAG, study state, memory |
| `hephaistos/chat/usage.py` | ~340 | Token tracking, cost estimation, context budget |
| `hephaistos/chat/events.py` | ~80 | Typed turn event dataclasses |
| `hephaistos/observability.py` | ~320 | Tracing, metrics, crash reporting (no-op in source builds) |

## Entry points for modification

- **Add a new transient error type**: Edit `_get_retryable_types()` in `hephaistos/chat/engine.py`.
- **Change circuit breaker thresholds**: Edit `_circuit_breaker` defaults or create named instances in `hephaistos/chat/resilience.py`.
- **Add a new keyless endpoint**: Add to `_KEYLESS_ENDPOINTS` frozenset in `hephaistos/chat/engine.py`.
- **Change streaming chunk handling**: Modify the chunk-processing loop inside `stream_completion()`.
