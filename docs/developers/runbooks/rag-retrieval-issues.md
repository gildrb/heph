# RAG Retrieval Issues

When RAG search returns poor or missing results, follow this runbook.

## Symptoms

- "No relevant sources found" when asking about armory content
- Irrelevant or low-quality chunks retrieved
- RAG retrieval takes too long

## Diagnosis

1. **Verify armory structure** — the armory must have a valid marker:
   ```bash
   cat my-armory/.hephaion/armory.toml
   ```

2. **Check material files exist** — only `materials/` is indexed:
   ```bash
   ls my-armory/materials/
   ```
   Hidden files are skipped by the indexer.

3. **Check the RAG index** — it should exist and be recent:
   ```bash
   cat my-armory/.hephaion/rag_index.json | python -m json.tool | head
   ```

4. **Check trace logs** — each retrieval is logged with scores:
   ```
   type=rag_retrieve query="..." top_k=5 retrieved=3 scores=[0.82, 0.65, 0.41] latency_ms=120
   ```
   If `retrieved=0`, the query didn't match any chunks above the minimum
   score threshold (0.1).

5. **Check recent latency in logs** — compare `latency_ms` values across
   recent retrieval traces to spot regressions after a source or model change.

## Common Fixes

| Problem | Fix |
|---------|-----|
| Missing index | Run `heph index <path>` to rebuild |
| Stale index | Re-index after adding/modifying material files |
| Low scores | Improve source document quality; split large files into focused sections |
| No material files | Add documents to `materials/` |
| Hidden files indexed | Move them out of `materials/` or rename without leading dot |
| Memory not loaded | Check `my-armory/.hephaion/memory.json` exists and is valid |

## Rebuilding the Index

```bash
# From the armory directory
uv run heph index .

# Or with an explicit armory path
uv run heph index ~/.armories/my-armory
```

This rebuilds the RAG index from all files in `materials/`.
Large armories may take a few minutes.

## Embedding Model

Hephaion uses sentence-transformers for embeddings as part of the standard
Heph install.

If embeddings fail, check:
- The installation has not been externally modified; repair a user install with
  `uv tool install --force heph@latest`
- The model can be downloaded (network access)
- Sufficient RAM for the embedding model
