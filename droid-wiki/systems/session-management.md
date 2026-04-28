# Session management

The session management layer owns the lifecycle of a chat session: creation with armory attachment, message processing via the turn orchestrator, and persistence to the armory's `chats/` directory. It is the glue between the chat engine, the agent harness, and the UI.

## Purpose

- Create fresh or resume existing chat sessions scoped to an armory (or plain mode without one).
- Process user messages through the `TurnOrchestrator`, which handles RAG retrieval, study state, and tool dispatch.
- Persist conversations and session metadata to disk.
- Track token usage and cost per session.
- Manage per-session resources: RAG index, memory store, tool registry, steering queue, traces.

## Directory layout

```
hephaistos/chat/
├── session.py          # ChatSession, create_session(), send_user_message(), save_session()
├── storage.py          # File-based chat save/load/list in armory's chats/ directory
├── titles.py           # derive_title() — auto-generate session title from first user message
├── usage.py            # SessionUsage, TokenUsage, ContextBudget, cost estimation
├── orchestrator.py     # TurnOrchestrator — single-turn RAG + tool orchestration
├── engine.py           # ChatConfig, stream_completion() (see chat-engine.md)
├── events.py           # Typed turn events
└── _api_types.py       # Shared API message types
```

## Key abstractions

| Abstraction | File | Purpose |
|---|---|---|
| `ChatSession` | `hephaistos/chat/session.py` | Central dataclass: config, conversation, session ID, armory path, usage, study state, persona, steering, RAG index, memory, tool registry, trace writer |
| `TurnOrchestrator` | `hephaistos/chat/orchestrator.py` | Owns a single user turn: RAG retrieval, study plan, agent dispatch, memory extraction, citation verification |
| `SessionUsage` | `hephaistos/chat/usage.py` | Accumulated token counts and cost across all API calls in a session |
| `TokenUsage` | `hephaistos/chat/usage.py` | Token counts from a single API response |
| `ContextBudget` | `hephaistos/chat/usage.py` | Tracks context window consumption and compaction urgency |
| `SessionRecord` | `hephaistos/chat/storage.py` | Typed dict for session listing: ID, title, created/updated timestamps |

## How it works

### Session creation

There are three session creation paths:

1. **`create_session(config, armory_path)`**: Creates a session scoped to an armory.
   - Validates the armory via `validate_armory_path()`.
   - Scans source files via `_scan_source_files()`.
   - Builds a system prompt with armory context, source files, and memory.
   - Loads armory tool plugins into a child `ToolRegistry`.
   - Initializes the memory store (`MemoryStore`), RAG index (lazy), and trace writer.

2. **`create_plain_session(config)`**: Creates a session without an armory.
   - Uses a fallback system prompt that directs the user to create an armory.
   - No tools, no RAG, no memory.

3. **`resume_session(config, armory_path, session_id)`**: Loads a saved session from disk.
   - Restores conversation, title, and metadata (including study state).
   - Re-scans source files and reloads armory tools and memory.

### Message processing

`send_user_message(session, user_input)` is the main entry point for processing a user message:

1. Marks activity timestamp.
2. Creates a `TurnOrchestrator` for the session.
3. Iterates over `orchestrator.iter_events(user_input)`:
   - Renders each `TurnEvent` to a string via `render_turn_event()`.
   - Writes to `sys.stdout` or forwards to a custom `writer` callback.
4. Returns the final reply text.

### Turn orchestrator flow

`TurnOrchestrator.iter_events()` handles a single turn:

1. Saves original conversation and study state for rollback on error.
2. Adds the user message to the conversation.
3. If an armory is attached:
   - Plans the turn via `plan_turn()` (study controller).
   - Retrieves RAG evidence via `_resolve_turn_evidence()`.
   - Runs `iter_agent_events()` (agent harness) with the plan and evidence.
   - Applies study state changes and runs citation verification.
   - Extracts memory entries in a background thread.
4. If no armory (plain mode):
   - Streams a simple completion without tools or RAG.
5. On `StreamRecoveryError` or `EngineError`, rolls back the conversation and study state.

### Session persistence

- **`save_session(session)`**: Persists to `<armory>/chats/<session_id>.json`.
  - Derives a title from the first user message if not already set.
  - Saves study state and timestamps as metadata.
  - Marks the session as clean (`dirty = False`).

- **`chat_storage.save()`**: Serializes conversation messages, title, timestamps, and metadata to JSON.
- **`chat_storage.load()`**: Deserializes back into a `Conversation` + title.
- **`chat_storage.list_sessions()`**: Returns all saved sessions as `SessionRecord` dicts.

### Title derivation

`derive_title(conversation)` extracts the first user message (up to 60 chars). If the same message prefix appears multiple times, a count is appended (e.g. `"Explain photosynthesis (2)"`).

### Usage tracking

- `SessionUsage.record()` accumulates per-call token counts and estimates cost using a model pricing table.
- `SessionUsage.estimate_from_chars()` provides a fallback (4 chars ≈ 1 token) when the API doesn't report usage.
- `ContextBudget` computes remaining tokens and compaction urgency (`none`/`low`/`medium`/`high`).
- Usage is persisted to `<armory>/.hephaistos/usage/<session_id>.json` after each turn.

## Integration points

- **Chat engine** ([chat-engine.md](chat-engine.md)): `TurnOrchestrator` calls `stream_completion()` for LLM streaming.
- **Agent harness** ([agent-harness.md](agent-harness.md)): `TurnOrchestrator` calls `iter_agent_events()` for tool dispatch.
- **Provider config** ([provider-config.md](provider-config.md)): `ChatConfig` is populated by `ProviderConfig.apply_to_config()`.
- **Study controller** (`hephaistos/study/`): `plan_turn()` determines the turn's system prompt, tool access, and expected source refs.
- **Memory** (`hephaistos/memory/`): Memory context is included in the system prompt; extraction runs post-turn in a background thread.
- **RAG** (`hephaistos/harness/rag/`): Lazy-loaded `ArmoryIndex` used for evidence retrieval.

## Key source files

| File | Lines | Role |
|---|---|---|
| `hephaistos/chat/session.py` | ~430 | Session lifecycle, creation, message processing, persistence |
| `hephaistos/chat/orchestrator.py` | ~470 | Single-turn orchestration with RAG, study state, memory |
| `hephaistos/chat/storage.py` | ~200 | File-based chat save/load/list |
| `hephaistos/chat/titles.py` | ~25 | Session title derivation |
| `hephaistos/chat/usage.py` | ~340 | Token tracking, cost estimation, context budget |

## Entry points for modification

- **Add session-scoped state**: Add fields to `ChatSession` in `hephaistos/chat/session.py`.
- **Change turn orchestration**: Modify `TurnOrchestrator.iter_events()` in `hephaistos/chat/orchestrator.py`.
- **Change session persistence format**: Edit `save()` and `load()` in `hephaistos/chat/storage.py`.
- **Add new usage metrics**: Extend `SessionUsage` in `hephaistos/chat/usage.py`.
- **Change title derivation**: Edit `derive_title()` in `hephaistos/chat/titles.py`.
