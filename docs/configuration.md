# Configuration

Hephaion can be configured through provider credentials, environment variables,
the `/settings` TUI, and `heph config`. Armories keep their own materials,
memory, chats, traces, indexes, and learning data, but model/provider preferences
are machine-local user settings unless overridden by environment variables.

## Environment Variables

### Model Configuration

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `ZAI_API_KEY` | Z.AI API key |
| `CUSTOM_API_KEY` | Custom endpoint API key |
| `HEPHAION_BASE_URL` | Custom base URL for OpenAI-compatible endpoints |
| `HEPHAION_MODEL` | Default model name |

### Runtime and Retrieval

| Variable | Purpose |
|----------|---------|
| `HEPHAION_MAX_TOKENS` | Max output tokens per response |
| `HEPHAION_TEMPERATURE` | Model sampling temperature |
| `HEPHAION_RAG_CONTEXT_BUDGET` | Token budget for retrieved context |
| `HEPHAION_FEATURE_FLAGS` | Comma-separated feature flags |
| `HEPHAION_PRIORITY_WEB_PREREQS` | Enable optional web-backed prerequisite hints in priority reports |
| `HEPHAION_EMBED_MODEL` | Embedding model override |
| `HEPHAION_RERANK_MODEL` | Reranker model override |
| `HEPHAION_EXTRACTION_MODEL` | Background memory extraction model override |

### Privacy and Diagnostics

| Variable | Purpose |
|----------|---------|
| `HEPHAION_LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `HEPHAION_LOG_FILE` | Path to log file |
| `HEPHAION_LOG_FORMAT` | Log format (`text` or `json`) |
| `HEPHAION_ANALYTICS_ENABLED` | Override saved analytics opt-in (`true`/`false`) |
| `HEPHAION_CRASH_REPORTS_ENABLED` | Override saved crash-report opt-in (`true`/`false`) |

## TUI Settings

Access settings via the `/settings` command in Heph:

- **Privacy and diagnostics**: anonymous analytics and redacted crash reports,
  both opt-in
- **Appearance**: saved TUI theme preference; press Enter to cycle themes
- **Activity trace**: local session trace visibility; defaults to minimal tool
  calls
- **Model thinking**: provider-exposed thinking visibility (`off`, `minimal`,
  or `all`), defaulting to `minimal`; hidden model reasoning is not exposed by
  providers that keep it private
- **Live tokens**: show or hide token estimates in the TUI status bar; press
  Enter to toggle
- **Live cost**: show or hide cost estimates in the TUI status bar; press
  Enter to toggle
- **Vocabulary practice**: learning/practice preferences; press Enter to cycle
  modes
- **Login / Logout**: provider authentication flow

Source and Git installs do not enable hosted diagnostics by default.

## User Configuration

Use `/models` or provider login for normal model selection. Advanced users can
persist machine-local overrides with `heph config`:

```bash
heph config show
heph config set model <model-id>
heph config set temperature 0.2
heph config set rag_context_budget 6000
heph config set thinking_visibility minimal
heph config set live_tokens_visible true
heph config set live_cost_visible true
```

These preferences are stored in the user config directory, not inside
`.armories`. Provider credentials stay in the OS keyring, environment variables,
or session memory fallback; they are never written into armory folders.
The `/settings` TUI controls and direct status-bar toggles such as `/cost`
update the same config file, so model-thinking and status-bar usage visibility
are remembered across TUI restarts.

Use `heph local` or `/local` for private local llama.cpp models from the curated
catalog:

```bash
heph local search gemma
heph local install <owner>/<repo>:Q4_K_M
heph local status
heph local revalidate llama-cpp/<owner>/<repo>:Q4_K_M
heph local stop
```

The guided `/local` list only shows publisher-owned GGUF releases selected for
laptops and capped at 16 GB recommended RAM. Each entry shows the download size
and RAM guidance before loading, and Heph asks for confirmation before it
downloads or starts a model. Heph downloads the managed `llama-server` binary
into `~/.cache/hephaion/llama.cpp/bin/`, stores GGUF cache under
`~/.cache/hephaion/llama.cpp/models`, and persists local model validation state
in the user config directory. Local models appear in `/models` only after the
tool-call probe passes.

## Model Providers

### OpenAI

```bash
export OPENAI_API_KEY="sk-..."
```

Or use `/login` with your OpenAI account.

### DeepSeek

```bash
export DEEPSEEK_API_KEY="sk-..."
```

DeepSeek uses Heph's provider profile adapter: reasoning models enable DeepSeek
thinking mode and use DeepSeek's native reasoning effort values.

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

### Local llama.cpp

No API key is required. Use `/local` for a guided install or `heph local` for
CLI management. The built-in catalog is limited to low-footprint publisher GGUF
releases, while advanced users can still install a local `.gguf` file by path.
Heph binds the managed server to `127.0.0.1` and never falls back to a hosted
provider for a local model.

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

## Armory State

Each armory stores local state under `.hephaion/`, including retrieval indexes,
memory, chats, traces, and learning attempt logs. Index files are rebuildable
machine-local state; source materials plus armory metadata are enough for Heph to
open a copied or synced armory and rebuild what it needs.

## Advanced Configuration

### Retrieval Backends

Heph ships its document extraction and retrieval stack with the normal install.
That includes BM25, TF-IDF, embedding retrieval, and reranking support, so users
do not need to install a separate RAG extra.

### Profiling

Enable CPU or memory profiling:

```bash
heph --profile
heph --profile-memory
```

This will generate profiling reports in `.hephaion/profile/`.
