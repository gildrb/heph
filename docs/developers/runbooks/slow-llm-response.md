# Debugging Slow LLM Responses

When LLM interactions are slow or unresponsive, use this runbook to
identify the bottleneck.

## Quick Diagnosis

1. **Check provider status** - visit the provider's status page:
   - OpenRouter: https://openrouter.ai/status
   - OpenAI: https://status.openai.com
   - Z.AI: check their dashboard

2. **Check recent logs and traces** - look for `latency_ms` in your structured
   logs or the active armory trace file.

3. **Check logs** - each LLM request logs latency:
   ```
   ai.runtime.engine: stream_completion complete  model=gpt-5.4 latency_ms=1234
   ```

## Profiling

### CPU Profiling with cProfile

Run the CLI with the `--profile` flag to generate a CPU profile:

```bash
uv run heph --profile
# ... interact with the CLI ...
# Profile saved to ~/.cache/harness/profiles/<timestamp>.prof on exit
```

Analyze the profile:
```bash
python -m pstats ~/.cache/harness/profiles/<timestamp>.prof
```

### Memory Profiling with tracemalloc

Run with `--profile-memory` to track allocations:

```bash
uv run heph --profile-memory
# Top 20 allocations printed on exit
```

### External Profiling with py-spy

For flame graphs without modifying the runtime:

```bash
# Install py-spy (already in dev dependencies)
uv run py-spy record -o profile.svg -- heph
```

## Common Causes

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| High first-token latency | Cold start or provider queue | Try a different model or provider |
| Slow RAG retrieval | Large index, no caching | Rebuild index: `heph index <path>` |
| High memory usage | Large conversation context | Start a new session or reduce context |
| Timeout errors | Network or provider overload | Check `RetryConfig` settings; increase `max_delay` |

## Local Trace Files

If the session is attached to an armory, inspect
`<armory>/.harness/traces/<session_id>.jsonl` for:
- request timing and retrieval latency
- tool-call timing
- the sequence of user and assistant turns leading up to the slowdown
