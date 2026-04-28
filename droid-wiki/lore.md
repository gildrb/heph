# Lore

A timeline history of the Hephaistos codebase.

## Eras

### 1. Foundation (Feb 2026)

19 commits. The core ideas landed in this first month:

- Basic shell with prompt-toolkit for interactive input
- The armory concept — a per-project study workspace backed by local storage
- Chat engine wired to OpenAI-compatible LLMs
- RAG indexing with a chunker that splits source files into searchable segments

Everything after this is built on these four pillars.

### 2. Growth and features (Mar 2026)

13 commits. The surface area expanded without fundamentally changing the architecture:

- **Memory system** — persistent conversation memory per armory
- **Study controller** — structured study sessions that leverage RAG
- **Vocabulary drill** — flashcard-style vocab practice
- **Compaction** — automatic summarization of long conversations to keep context windows manageable
- **Provider config expansion** — more LLM providers and cleaner configuration

### 3. The TUI migration (Apr 2026)

171 commits. This is where the codebase tripled in size.

- **Textual TUI introduced** as the primary interface, replacing the prompt-toolkit-only shell
- **Shell refactored** from a simple input loop into a fullscreen prompt-toolkit `Application`
- **Pollinations AI added** as a zero-config default provider — no API key required
- **Supermemory integration** for external memory backends
- **OAuth authentication** for provider login flows
- **Armory browser** — visual navigation of armories and their contents
- **Search index** — fast full-text search across indexed files
- **QA workflows** — automated testing infrastructure
- **CI/CD setup** with a release pipeline (`.github/workflows/release.yml`)

### 4. Polish and stability (late Apr 2026)

The final stretch before the current state:

- Focus handling fixes for the TUI
- Autocomplete refinement for slash commands
- Banner branding and persona rewrites
- Performance improvements — deferred imports cut startup time by ~3×

## Longest-standing features

These three modules have been part of the codebase since Feb 2026. They've changed significantly but retain the same fundamental design:

- **`hephaistos/armory/storage.py`** — the armory persistence layer
- **`hephaistos/chat/engine.py`** — the LLM chat engine
- **`hephaistos/harness/rag/chunker.py`** — the RAG chunker that splits files into indexed segments

## Major rewrites

| Date | Commit | What changed |
|---|---|---|
| Apr 23, 2026 | `518cf46` | Prompt-toolkit shell refactored from a simple input loop to a fullscreen `Application` |
| Apr 25, 2026 | `71ba672` | TUI made the default interface; classic shell demoted to `--shell` flag |
| Apr 26, 2026 | `68af2b8` | Default provider changed from OpenRouter to Pollinations AI for zero-config onboarding |

## Growth trajectory

| Period | Source files | Test files |
|---|---|---|
| Feb 2026 | ~5 | 0 |
| Mar 2026 | ~15 | a few |
| Apr 2026 | 78 | 61 |

The test suite grew from nothing to 61 files covering 77% of the codebase. Most of that test coverage was written alongside the April TUI migration rather than retrofitted afterward.
