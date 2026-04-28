# Memory system

The memory system tracks what the user has already learned or discussed within an armory. It extracts concepts from conversation turns, deduplicates against existing memory, and injects a summary into the system prompt so the agent avoids repeating material.

## Purpose

Ensure the study agent knows what the user already understands. This is not a vector store — it is a structured knowledge base optimized for a study agent that must track topic coverage across sessions.

## Directory layout

```
hephaistos/memory/
├── __init__.py            # MemoryStore, load_memory(), save_memory()
├── extract.py             # extract_and_store() — LLM-based concept extraction
└── supermemory.py         # Optional Supermemory cloud backend
```

## Key abstractions

| Abstraction | Source file | Purpose |
|---|---|---|
| `MemoryEntry` | `hephaistos/memory/__init__.py` | A learned concept: `topic`, `content`, `source`, `confidence`, `created_at`, `access_count`, `tags` |
| `MemoryStore` | `hephaistos/memory/__init__.py` | Per-armory JSON store: load, save, add, deduplicate, build system context |
| `SupermemoryStore` | `hephaistos/memory/supermemory.py` | Cloud-backed `MemoryStore` using the Supermemory SDK |
| `load_memory()` | `hephaistos/memory/__init__.py` | Factory: returns `SupermemoryStore` if API key available, else `MemoryStore` |
| `extract_and_store()` | `hephaistos/memory/extract.py` | Extracts concepts from a conversation exchange and stores them |
| `MemoryEntryPayload` | `hephaistos/memory/__init__.py` | TypedDict for serialized memory entries |

## How it works

### Memory entries

Each `MemoryEntry` carries:

| Field | Type | Description |
|---|---|---|
| `topic` | `str` | Short label for the concept |
| `content` | `str` | The learned fact or definition |
| `source` | `str` | Where it came from (document name, "conversation") |
| `confidence` | `str` | `"extracted"` (from docs), `"discussed"` (from conversation), or `"verified"` (confirmed by user) |
| `created_at` | `float` | Unix timestamp |
| `access_count` | `int` | How many times it has been referenced |
| `tags` | `list[str]` | Optional classification tags |

### Concept extraction

`extract_and_store()` in `hephaistos/memory/extract.py` runs after each assistant turn (when the response is ≥100 characters):

1. Sends the user message, assistant reply, and source references to a dedicated extraction prompt.
2. The extraction LLM returns a JSON array of `{topic, content, source}` objects.
3. Each extracted concept is deduplicated against existing memory by topic (case-insensitive match).
4. If a topic already exists with lower confidence, its confidence is upgraded.
5. New entries are persisted to the armory's memory store.

Extraction is deliberately conservative — only concrete facts and concepts are extracted, not opinions or guesses. The extraction uses a low temperature (0.1) for deterministic output.

### Local persistence

`MemoryStore` saves to `.hephaistos/memory.json` per armory. The format is:

```json
{
  "version": 1,
  "updated_at": 1714000000.0,
  "entries": [
    {
      "topic": "TCP handshake",
      "content": "TCP uses a 3-way handshake: SYN, SYN-ACK, ACK",
      "source": "networking_notes.md",
      "confidence": "extracted",
      "created_at": 1714000000.0,
      "access_count": 0,
      "tags": []
    }
  ]
}
```

### Supermemory cloud backend

When a Supermemory API key is configured (via keychain, environment variable, or volatile store), `load_memory()` returns a `SupermemoryStore` instead of the local JSON store. The cloud backend:

- Stores entries remotely via the Supermemory SDK using container tags (`heph:armory:<hash>` for per-armory, `heph:profile:<name>` for cross-armory).
- Supports cross-armory study profiles — concepts learned in one armory can be searched across all armories.
- Falls back to the local JSON store when the API is unreachable.

### Memory injection into the system prompt

`build_system_context()` produces a system-prompt section like:

```
The user has already studied these topics (do NOT repeat this material unless asked):
- [verified] TCP handshake: TCP uses a 3-way handshake
- [discussed] DNS resolution
- [extracted] OSI model layers
```

Entries are prioritized by confidence (`verified` > `discussed` > `extracted`) and recency. The output is capped at 20 entries and 3000 characters.

### Deduplication

When adding a new entry, `MemoryStore.add()` checks for existing entries with the same topic (case-insensitive). If a match is found:
- The confidence is upgraded if the new entry has higher confidence.
- Otherwise, the entry is skipped (returns `None`).

This prevents the memory from bloating with repeated discussions of the same concept.

### The `/memory` command

The `/memory` shell command provides management operations. The TUI also suggests `/memory setup` when a Supermemory API key is detected, enabling cross-armory semantic study memory.

## Integration points

- **Orchestrator**: `hephaistos/chat/orchestrator.py` calls `extract_and_store()` in a background thread after each turn with a substantive reply.
- **RAG pipeline**: Source references from retrieved evidence are passed as context to the extraction prompt. See [RAG retrieval](rag-retrieval.md).
- **System prompt**: `build_system_context()` is called when building the system prompt for each LLM turn.
- **Study loop**: Memory is updated during study sessions as the user learns new material. See [study loop](study-loop.md).

## Key source files

| File | Responsibility |
|---|---|
| `hephaistos/memory/__init__.py` | `MemoryStore`, `MemoryEntry`, `load_memory()`, `save_memory()`, system context builder |
| `hephaistos/memory/extract.py` | `extract_and_store()`, LLM-based concept extraction |
| `hephaistos/memory/supermemory.py` | `SupermemoryStore`, SDK integration, profile-based storage |

## Entry points for modification

- Add a new confidence level: update the `confidence_order` dict in `MemoryStore.add()` and `build_system_context()` in `hephaistos/memory/__init__.py`.
- Change extraction behavior: adjust `_EXTRACTION_SYSTEM_PROMPT` or `_MIN_CONTENT_LENGTH` in `hephaistos/memory/extract.py`.
- Change system context formatting: update `build_system_context()` in `hephaistos/memory/__init__.py`.
- Add a new cloud backend: subclass `MemoryStore` and wire it into `load_memory()`.
