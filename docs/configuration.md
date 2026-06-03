# Configuration

Hephaion can be configured through environment variables, TUI settings, and armory-specific configuration.

## Environment Variables

### Model Configuration

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `ZAI_API_KEY` | Z.AI API key |
| `CUSTOM_API_KEY` | Custom endpoint API key |
| `HEPHAION_BASE_URL` | Custom base URL for OpenAI-compatible endpoints |
| `HEPHAION_MODEL` | Default model name |

### Privacy and Diagnostics

| Variable | Purpose |
|----------|---------|
| `HEPHAION_LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `HEPHAION_LOG_FILE` | Path to log file |
| `HEPHAION_LOG_FORMAT` | Log format (`text` or `json`) |

## TUI Settings

Access settings via the `/settings` command in Heph:

### Privacy

- **Analytics**: Anonymous usage analytics (opt-in)
- **Crash Reporting**: Anonymous crash reports (opt-in)
- **Telemetry**: Performance and usage metrics (opt-in)

Note: Source and Git installs do not enable hosted diagnostics by default.

### Model Settings

- **Default Model**: Choose your preferred model
- **Temperature**: Control response randomness (0.0-1.0)
- **Max Tokens**: Limit response length

### Retrieval Settings

- **Chunk Size**: Document chunking size for retrieval
- **Chunk Overlap**: Overlap between chunks
- **Top K**: Number of chunks to retrieve

## Armory Configuration

Each armory can have specific configuration in `.hephaion/config.json`:

```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "retrieval": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "top_k": 5
  },
  "memory": {
    "enabled": true
  }
}
```

## Model Providers

### OpenAI

```bash
export OPENAI_API_KEY="sk-..."
```

Or use `/login` with your OpenAI account.

### OpenRouter

```bash
export OPENROUTER_API_KEY="sk-..."
```

### Pollinations AI

No configuration required - free and open.

### Z.AI

```bash
export ZAI_API_KEY="sk-..."
```

### Custom Endpoint

```bash
export CUSTOM_API_KEY="your-key"
export HEPHAION_BASE_URL="https://your-endpoint.com/v1"
export HEPHAION_MODEL="your-model-name"
```

## File Ignore Patterns

Create `.hephaion/ignore` in your armory to exclude files from indexing:

```
# Ignore patterns (similar to .gitignore)
*.tmp
draft-*
old/
```

## Memory Configuration

Memory is scoped per-armory and can be configured:

```json
{
  "memory": {
    "enabled": true,
    "retention_days": 30,
    "max_entries": 1000
  }
}
```

## Advanced Configuration

### Custom Retrieval Backend

For advanced users, you can configure custom retrieval backends through optional dependencies:

```bash
uv sync --frozen --group rag  # Install BM25, embeddings, reranking
# Docling document extraction is part of the core install.
```

### Profiling

Enable CPU or memory profiling:

```bash
heph --profile
heph --profile-memory
```

This will generate profiling reports in `.hephaion/profile/`.