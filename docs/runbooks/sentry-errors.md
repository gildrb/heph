# Sentry Error Investigation

When Sentry reports an error from Hephaistos, follow these steps to
diagnose and resolve it.

## Prerequisites

- Sentry project configured with `SENTRY_DSN` environment variable
- Optional: `ALERT_WEBHOOK_URL` for push notifications on errors

## Investigation Steps

1. **Open the Sentry issue** — the alert (webhook or email) links directly
   to the issue page.

2. **Check breadcrumbs** — Sentry records breadcrumbs for each session.
   Look for the sequence of events leading to the error:
   - LLM requests (model, provider, latency)
   - Armory operations (index builds, file reads)
   - Session events (start, user messages)

3. **Check trace context** — if OpenTelemetry is configured, the error
   will include a `trace_id`. Use it to correlate with spans in your
   OTel backend (Jaeger, Tempo, etc.).

4. **Check tags** — key tags include:
   - `session_id` — which chat session
   - `armory` — which armory was active
   - `provider` / `model` — which LLM was in use
   - `platform` — always `cli` for the terminal app

5. **Reproduce locally** — use the same armory and provider:
   ```bash
   uv run heph
   # Then issue the same commands visible in breadcrumbs
   ```

6. **Check if it's a provider error** — many errors come from LLM API
   failures (rate limits, auth errors, timeouts). These are transient
   and may not require code changes. Look for `EngineError` or
   `StreamRecoveryError` in the exception type.

## Common Error Patterns

| Exception | Meaning | Action |
|-----------|---------|--------|
| `EngineError` | LLM request failed | Check provider status, API key validity |
| `StreamRecoveryError` | Stream interrupted mid-response | Usually transient; check provider stability |
| `ArmoryError` | Armory operation failed | Check armory directory structure |
| `SessionError` | Session setup failed | Verify armory path and config |

## Redaction

All Sentry events pass through `_redact_event` hook which scrubs:
- API keys (OpenAI, Anthropic patterns)
- Bearer tokens
- Sensitive dict keys (api_key, secret, token, password, etc.)

If sensitive data still appears in Sentry, update the patterns in
`hephaistos/observability.py` and `hephaistos/logging.py`.
