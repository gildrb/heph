# Glossary

Terms used throughout the Hephaistos codebase and documentation.

| Term | Definition |
|------|-----------|
| **Armory** | A directory on disk that serves as a portable study workspace. Contains source files, a RAG index, saved chats, study memory, and notes. Marked by `.hephaistos/armory.toml`. |
| **Evidence** | Retrieved chunks from source documents, labeled with IDs like `[E1]`, `[E2]` that the LLM uses to cite its answers. |
| **Citation verification** | The process of checking that every `[E#]` reference in an LLM answer matches evidence actually retrieved in that turn. Implemented in `hephaistos/harness/citation.py`. |
| **Compact** | Context compaction: summarizing earlier conversation turns to reduce token usage while preserving key information. See `hephaistos/harness/compact.py`. |
| **Conversation** | The message history sent to the LLM. Stored as a list of `Message` objects with roles (system, user, assistant, tool). |
| **Dispatch** | The agent loop in `hephaistos/harness/dispatch.py` that handles tool calls, RAG retrieval, and multi-turn reasoning within a single user question. |
| **Harness** | The agent infrastructure layer: prompt building, persona management, citation checking, tool registry, RAG, and compact. Lives in `hephaistos/harness/`. |
| **Keyless endpoint** | An LLM endpoint that does not require an API key (e.g., Pollinations AI). Detected by `is_keyless_endpoint()` in `hephaistos/chat/engine.py`. |
| **Memory** | Per-armory learned concepts stored in `.hephaistos/memory.json`. Extracted after exchanges, injected into future prompts. |
| **Micro compact** | A lightweight compaction that strips old messages without LLM summarization. Used when token budgets are tight. |
| **Orchestrator** | `hephaistos/chat/orchestrator.py` — coordinates a single turn: RAG retrieval, dispatch, citation verification, memory extraction, and usage tracking. |
| **Persona** | The agent's personality and behavior mode. Configurable per session. Defined in `hephaistos/harness/persona.py`. |
| **Provider** | An LLM backend configuration (endpoint URL, API key source, model list). Stored in `~/.config/hephaistos/providers.toml`. |
| **RAG** | Retrieval-Augmented Generation. Indexes armory source files, retrieves relevant chunks per query, and injects them as evidence into the LLM prompt. |
| **Session** | A single chat interaction from opening the TUI to closing it. Has a UUID, conversation history, and usage stats. |
| **Steering** | Real-time control signals (e.g., compact requests, persona changes) sent to the dispatch loop via `SteeringQueue`. |
| **Study loop** | The recall-first study workflow: present material, ask user to recall, assess the attempt, give hints. Controlled by `hephaistos/study/controller.py`. |
| **Supermemory** | Optional cloud-based study memory integration via the `supermemory` SDK. |
| **Tool registry** | The set of tools the agent can call (file read/write, bash, web fetch). Extensible via plugins in `.hephaistos/tools/`. |
| **Turn** | One cycle of user question → retrieval → dispatch → LLM answer → citation check → memory extraction. |
