# Debugging

## Logging

Hephaistos uses structured logging through `hephaistos/logging.py`. Every log message passes through secret redaction — API keys, Bearer tokens, and other sensitive values are scrubbed before output.

Control logging with environment variables:

| Variable | Values | Effect |
|----------|--------|--------|
| `HEPHAISTOS_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Verbosity. Default is `WARNING`. |
| `HEPHAISTOS_LOG_FILE` | file path | Write logs to a file instead of stderr. |
| `HEPHAISTOS_LOG_FORMAT` | `text`, `json` | Output format. `json` is structured and machine-readable. |

For verbose diagnostics:

```bash
HEPHAISTOS_LOG_LEVEL=DEBUG uv run heph
```

To capture logs to a file for later analysis:

```bash
HEPHAISTOS_LOG_LEVEL=DEBUG HEPHAISTOS_LOG_FILE=/tmp/heph-debug.log uv run heph
```

For structured output (useful with `jq` or log aggregation):

```bash
HEPHAISTOS_LOG_FORMAT=json HEPHAISTOS_LOG_LEVEL=DEBUG uv run heph
```

## Session traces

Every study session generates a JSONL trace file stored per-armory in `.hephaistos/traces/`. These are written by `TraceWriter` in `hephaistos/logging.py`.

Trace files contain:
- Timestamps for each turn
- LLM requests and responses (with secrets redacted)
- RAG retrieval results
- Tool invocations
- Citation verification outcomes

To inspect a trace:

```bash
cat .hephaistos/traces/<session-id>.jsonl | python -m json.tool
```

## CPU profiling

The `--profile` flag enables CPU profiling using `py-spy`. It writes a profile to `~/.cache/hephaistos/profiles/`:

```bash
uv run heph --profile
```

After the session ends, view the profile:

```bash
py-spy report --file ~/.cache/hephaistos/profiles/<latest-profile>
```

## Memory profiling

The `--profile-memory` flag enables `tracemalloc` and prints the top 20 allocations at exit:

```bash
uv run heph --profile-memory
```

This helps identify memory leaks, especially in long-running sessions with large RAG indexes.

## Runbooks

The project maintains operational runbooks in `docs/runbooks/`:

- **`docs/runbooks/ci-failure.md`** — triage CI failures. Covers each CI job, common failure modes, and how to re-run.
- **`docs/runbooks/slow-llm-response.md`** — debug slow LLM responses. Covers network latency, model selection, prompt size, and streaming configuration.
- **`docs/runbooks/deployment-rollback.md`** — revert a bad release. Covers PyPI yanking, GitHub release deletion, and edge deploy rollback.
- **`docs/runbooks/rag-retrieval-issues.md`** — debug RAG quality. Covers index freshness, chunk size tuning, retrieval scoring, and embedding model selection.

## Common issues

### Tests fail with "config already exists"

The autouse `_isolate_global_state` fixture in `tests/conftest.py` should prevent this. If it happens, make sure you're using `tmp_path` or `isolated_config_dir` instead of writing to the real config directory.

### Import boundary violations

If `lint-imports` fails, check that you're not importing `hephaistos.app` from a non-app package. See the boundary rules in [../overview/architecture.md](../overview/architecture.md).

### Type check errors

If `basedpyright` reports errors, check for:
- Implicit `Any` types — forbidden. Use concrete types or protocols.
- Missing return type annotations on public functions.
- Use of `typing.cast` where a runtime check would be safer.

### Coverage drops below 75%

Run `uv run pytest --cov --cov-report=term-missing` to see which lines are uncovered. Focus on new code you added — the CI gate will block the PR.
