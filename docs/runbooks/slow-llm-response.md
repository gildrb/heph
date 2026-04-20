# Debugging Slow LLM Responses

When LLM interactions are slow or unresponsive, use this runbook to
identify the bottleneck.

## Quick Diagnosis

1. **Check provider status** — visit the provider's status page:
   - OpenRouter: https://openrouter.ai/status
   - OpenAI: https://status.openai.com
   - Z.AI: check their dashboard

2. **Check recent latency metrics** — if OpenTelemetry is configured,
   query the `llm.request.duration` histogram in your OTel backend
   filtered by model name.

3. **Check logs** — each LLM request logs latency:
   ```
   hephaistos.chat.engine: stream_completion complete  model=gpt-5.4 latency_ms=1234
   ```

## Profiling

### CPU Profiling with cProfile

Run the CLI with the `--profile` flag to generate a CPU profile:

```bash
uv run heph --profile chat
# ... interact with the CLI ...
# Profile saved to .hephaistos/profile/<timestamp>.prof on exit
```

Analyze the profile:
```bash
uv run python -c "
import pstats
p = pstats.Stats('.hephaistos/profile/latest.prof')
p.sort_stats('cumulative').print_stats(20)
"
```

### Memory Profiling with tracemalloc

Run with `--profile-memory` to track allocations:

```bash
uv run heph --profile-memory chat
# Top 20 allocations printed on exit
```

### External Profiling with py-spy

For flame graphs without modifying the runtime:

```bash
# Install py-spy (already in dev dependencies)
uv run py-spy record -o profile.svg -- python -m hephaistos chat
```

## Common Causes

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| High first-token latency | Cold start or provider queue | Try a different model or provider |
| Slow RAG retrieval | Large index, no caching | Rebuild index: `heph source reindex` |
| High memory usage | Large conversation context | Start a new session or reduce context |
| Timeout errors | Network or provider overload | Check `RetryConfig` settings; increase `max_delay` |

## OpenTelemetry Traces

If configured, inspect the `llm.completion` span for:
- `gen_ai.request.model` — which model was called
- `gen_ai.request.max_tokens` — token budget
- `gen_ai.response.prompt_tokens` / `gen_ai.response.completion_tokens` — actual usage
- `gen_ai.response.latency_ms` — measured latency

Correlate slow requests across traces using the `trace_id` in logs.
