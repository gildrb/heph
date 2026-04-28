# Data models

Key data structures used across the codebase, grouped by subsystem. Each entry links to its source file.

## Chat

### `ChatConfig`

**`hephaistos/chat/engine.py`**

Configuration for a single chat session. Fields: `model`, `base_url`, `api_key`, `temperature`, retry config, feature flags. Passed to the engine for every LLM call.

### `Conversation`

**`hephaistos/chat/engine.py`**

A list of `Message` objects with roles (`system`, `user`, `assistant`, `tool`). Represents the full conversation history sent to the LLM. Manages context window sizing and message truncation.

### `Message`

**`hephaistos/chat/engine.py`**

A single message in the conversation. Fields: `role`, `content`, `tool_calls`. Maps directly to the OpenAI chat completion message format.

### `ChatSession`

**`hephaistos/chat/session.py`**

Top-level session object. Holds a `ChatConfig`, `Conversation`, `session_id`, `title`, and `SessionUsage`. Created per armory session; persisted between turns.

### `SessionUsage`, `TokenUsage`, `ContextBudget`

**`hephaistos/chat/usage.py`**

Token tracking structures:
- `SessionUsage` — cumulative token counts for a session
- `TokenUsage` — per-turn input/output token counts
- `ContextBudget` — remaining context window capacity

## RAG and retrieval

### `ArmoryIndex`

**`hephaistos/harness/rag/index.py`**

The RAG index for an armory. Contains: documents (file paths and metadata), chunks (text segments with embeddings), and index statistics. Serialized to `.hephaistos/rag_index.json`.

### `TurnEvidence`

**`hephaistos/harness/rag/context.py`**

Evidence chunks retrieved for a single turn. Contains the ranked list of chunks with relevance scores, used for citation verification and context injection.

## Agent loop

### `ToolRegistry`

**`hephaistos/harness/tools.py`**

Registry of available tools and their handlers. Each entry is a `ToolSpec` (schema + handler function). The agent loop consults this registry when the LLM requests a tool call.

### `Persona`

**`hephaistos/harness/persona.py`**

Agent personality configuration. Defines the system prompt template, behavior guidelines, and response style. Used to construct the system message for each session.

## Study

### `StudyState`

**`hephaistos/study/state.py`**

Current state of a study session. Tracks: study phase (e.g., reading, reviewing, drilling), current action, and user feedback. Drives the study state machine.

### `StudyTurnPlan`

**`hephaistos/study/controller.py`**

The planned action for the next turn. Produced by the study controller after analyzing the current `StudyState` and conversation context. Determines whether to ask a question, provide an explanation, run a drill, or wrap up.

## Memory

### `MemoryStore`

**`hephaistos/memory/__init__.py`**

Per-armory memory entries. Stores extracted concepts and key facts from past sessions. Serialized to `.hephaistos/memory.json`. Read at session start, updated after substantive exchanges.

## Vocabulary

### `VocabCard`, `VocabDeck`, `VocabCardState`

**`hephaistos/vocab/`**

Vocabulary drill structures:
- `VocabCard` — a single term with definition, context, and spaced repetition state
- `VocabDeck` — collection of cards for an armory
- `VocabCardState` — learning state (new, learning, reviewing, mastered) with next review time

## Providers

### `ProviderConfig`

**`hephaistos/providers/config.py`**

Provider definition parsed from `~/.config/hephaistos/providers.toml`. Each entry maps to a single `[provider_name]` section with endpoint, API key env var, model list, and active flag.

### `ModelInfo`

**`hephaistos/providers/registry.py`**

Model metadata: display name, context window size, pricing, capabilities (streaming, tool use, vision). Used by the model selection UI and cost estimation.

## Settings

### `AppSettings`

**`hephaistos/parameters/settings.py`**

Typed settings dataclass representing `~/.config/hephaistos/config.json`. Fields include theme, interface mode, telemetry preferences, default armory/model, and feature flags. Loaded with caching; invalidated on write.
