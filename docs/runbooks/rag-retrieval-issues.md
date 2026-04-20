# RAG Retrieval Issues

When RAG search returns poor or missing results, follow this runbook.

## Symptoms

- "No relevant sources found" when asking about armory content
- Irrelevant or low-quality chunks retrieved
- RAG retrieval takes too long

## Diagnosis

1. **Verify armory structure** — the armory must have a valid marker:
   ```bash
   cat my-armory/.hephaistos/armory.toml
   ```

2. **Check source files exist** — only `source/` and `library/` are indexed:
   ```bash
   ls my-armory/source/
   ls my-armory/library/
   ```
   Hidden files are skipped by the indexer.

3. **Check the RAG index** — it should exist and be recent:
   ```bash
   cat my-armory/.hephaistos/rag_index.json | python -m json.tool | head
   ```

4. **Check trace logs** — each retrieval is logged with scores:
   ```
   type=rag_retrieve query="..." top_k=5 retrieved=3 scores=[0.82, 0.65, 0.41] latency_ms=120
   ```
   If `retrieved=0`, the query didn't match any chunks above the minimum
   score threshold (0.1).

5. **Check OpenTelemetry metrics** — if configured, query the
   `rag.retrieval.duration` histogram for latency trends.

## Common Fixes

| Problem | Fix |
|---------|-----|
| Missing index | Run `heph source reindex` to rebuild |
| Stale index | Re-index after adding/modifying source files |
| Low scores | Improve source document quality; split large files into focused sections |
| No source files | Add documents to `source/` or `library/` directories |
| Hidden files indexed | Move them out of `source/` or rename without leading dot |
| Memory not loaded | Check `my-armory/.hephaistos/memory.json` exists and is valid |

## Rebuilding the Index

```bash
# From the armory directory
uv run heph source reindex

# Or from any directory
uv run heph source reindex --armory /path/to/armory
```

This rebuilds the RAG index from all files in `source/` and `library/`.
Large armories may take a few minutes.

## Embedding Model

Hephaistos uses sentence-transformers for embeddings (optional dependency):
```bash
uv sync --extra embeddings
```

If embeddings fail, check:
- The `sentence-transformers` package is installed
- The model can be downloaded (network access)
- Sufficient RAM for the embedding model
