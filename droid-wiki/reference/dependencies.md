# Dependencies

## Runtime dependencies

Listed in `pyproject.toml` under `[project.dependencies]`:

| Package | Purpose |
|---------|---------|
| `keyring` | OS-level credential storage for API keys |
| `openai` | OpenAI Python SDK — communicates with any OpenAI-compatible LLM endpoint |
| `pathspec` | Gitignore-style file pattern matching for armory source indexing |
| `prompt-toolkit` | Fallback shell interface (used when Textual is unavailable) |
| `rapidfuzz` | Fuzzy string matching for command completion and search |
| `rich` | Terminal formatting, markdown rendering, progress bars |
| `certifi` | SSL certificate bundle (used in OAuth fallback) |
| `supermemory` | Memory management utilities |
| `textual` | Terminal UI framework — the primary interface |

## Optional dependency groups

### `embeddings` (RAG enhancement)

| Package | Purpose |
|---------|---------|
| `sentence-transformers` | Local embedding generation for semantic search |
| `scikit-learn` | Vector similarity computations |

### `docling` (document conversion)

| Package | Purpose |
|---------|---------|
| `docling` | Convert PDF, DOCX, and other formats to markdown |

### `rag` (full RAG backend)

| Package | Purpose |
|---------|---------|
| `bm25s` | BM25 sparse retrieval |
| `sentence-transformers` | Dense embeddings |
| `scikit-learn` | Similarity search |

## Dev dependencies

Listed in `pyproject.toml` under `[dependency-groups.dev]`:

| Package | Purpose |
|---------|---------|
| `pytest` | Test framework |
| `pytest-cov` | Coverage reporting |
| `pytest-randomly` | Randomize test order |
| `pytest-rerunfailures` | Rerun flaky tests |
| `pytest-xdist` | Parallel test execution |
| `ruff` | Linting and formatting |
| `basedpyright` | Strict type checking |
| `vulture` | Dead code detection |
| `pylint` | Duplicate code detection |
| `import-linter` | Import boundary enforcement |
| `bandit` | Security scanning |
| `deptry` | Dependency validation |
| `radon` | Complexity analysis |
| `py-spy` | CPU profiling |

## Docs dependencies

Listed in `[dependency-groups.docs]`:

| Package | Purpose |
|---------|---------|
| `mkdocs` | Documentation site generator |
| `mkdocs-material` | Material theme for MkDocs |
| `mkdocstrings[python]` | Python API documentation from docstrings |
| `mkdocs-autorefs` | Automatic cross-references in docs |

## Build system

```toml
[build-system]
requires = ["uv_build>=0.10.1,<0.11.0"]
build-backend = "uv_build"
```

The project uses `uv_build` as its build backend. Build with `uv build` to produce sdist and wheel.
