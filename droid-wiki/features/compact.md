# Context compaction

Context compaction is a three-layer compression system that keeps chat sessions running indefinitely within token budgets. It operates silently during normal operation and can also be triggered explicitly by the user or the agent.

## Purpose

Prevent context window overflow by compressing conversation history while preserving the most recent exchanges verbatim. Nothing is truly lost — full transcripts are saved to disk before any compaction.

## Directory layout

```
hephaistos/harness/
├── compact.py              # micro_compact(), auto_compact(), estimate_messages_tokens()
└── dispatch.py             # agent loop that triggers compaction
hephaistos/chat/
├── usage.py                # ContextBudget, SessionUsage, TokenUsage
└── events.py               # CompactRequestEvent
```

## Key abstractions

| Abstraction | Source file | Purpose |
|---|---|---|
| `estimate_messages_tokens()` | `hephaistos/harness/compact.py` | Rough token count for a message list (4 chars ≈ 1 token) |
| `micro_compact()` | `hephaistos/harness/compact.py` | Replace old tool results with placeholders (no LLM call) |
| `auto_compact()` | `hephaistos/harness/compact.py` | LLM-based summarization of older turns, preserving recent ones |
| `ContextBudget` | `hephaistos/chat/usage.py` | Tracks context window consumption and compaction urgency |
| `SessionUsage` | `hephaistos/chat/usage.py` | Accumulated token usage and cost across the session |
| `TokenUsage` | `hephaistos/chat/usage.py` | Token counts from a single API response |
| `CompactRequestEvent` | `hephaistos/chat/events.py` | Steering-queue event for model-requested compaction |

## How it works

### Layer 1: Micro-compaction

`micro_compact()` runs silently before every LLM turn in the agent loop. It:

1. Identifies all messages with `role == "tool"` (tool call results).
2. Leaves the most recent 3 tool results untouched.
3. Replaces older tool results that exceed 100 characters with a short placeholder: `[Previous: used <tool_name>]`.

This is a pure string replacement — no LLM call required. It operates in-place on the message list.

### Layer 2: Auto-compaction

`auto_compact()` triggers when the estimated token count exceeds 75% of the prompt budget. In `hephaistos/harness/dispatch.py`, the agent loop checks:

```python
compaction_threshold = int(budget.prompt_budget * 0.75)
if estimate_messages_tokens(llm_messages) > compaction_threshold:
    api_messages[:] = auto_compact(api_messages, config, workspace)
```

The auto-compaction process:

1. **Save transcript**: Full message history is persisted as JSONL to `.hephaistos/transcripts/transcript_<timestamp>.jsonl`.
2. **Split messages**: System messages are preserved. Non-system messages are split into old (to summarize) and recent (to keep verbatim). The most recent 2 complete exchanges are kept intact.
3. **Summarize**: Old messages are serialized (truncated at 80KB if needed) and sent to the LLM with a summarization prompt asking to preserve key facts, decisions, file paths, and code changes.
4. **Reassemble**: The compressed message list is `[system_msgs, summary_message, recent_messages]`.

If summarization fails (network error, etc.), the original messages are returned unchanged and the error is logged.

### Layer 3: Manual compaction

Two triggers:

- **`/compact` command**: The user types `/compact` in the shell. `CompactCommand` in `hephaistos/app/commands.py` handles it directly by summarizing the conversation.
- **Agent tool call**: When the agent calls the `compact` control tool, the dispatch loop detects it and runs `auto_compact()`.

Both approaches persist the full transcript before summarizing.

### Token estimation

`estimate_messages_tokens()` counts tokens across all message types:
- String `content` fields: `len(content) // 4`.
- Multi-part content (vision, etc.): sums text parts.
- Tool call names and arguments: estimated separately.

The 4-chars-per-token heuristic provides a fast, allocation-free approximation.

### Context budget tracking

`ContextBudget` in `hephaistos/chat/usage.py` tracks:

| Field | Description |
|---|---|
| `model` | The model name (used to determine max context) |
| `prompt_budget` | Maximum tokens for the prompt |
| `remaining()` | How much budget is left |

`compaction_urgency()` returns one of `"none"`, `"low"`, `"medium"`, or `"high"` based on current consumption.

### CompactRequestEvent

`CompactRequestEvent` in `hephaistos/chat/events.py` is a steering-queue event that the model can emit to request compaction. It carries a `call_id`, `name`, and `arguments` dict. The dispatch loop processes it by triggering `auto_compact()`.

## Integration points

- **Agent loop**: `hephaistos/harness/dispatch.py` runs `micro_compact()` before every LLM turn and `auto_compact()` when the threshold is exceeded.
- **Shell commands**: `hephaistos/app/commands.py` registers the `/compact` command.
- **Usage tracking**: `hephaistos/chat/usage.py` provides `ContextBudget` and `SessionUsage` for budget decisions.
- **Session persistence**: Transcripts are saved to `.hephaistos/transcripts/` within the armory.

## Key source files

| File | Responsibility |
|---|---|
| `hephaistos/harness/compact.py` | `micro_compact()`, `auto_compact()`, `estimate_messages_tokens()`, transcript persistence |
| `hephaistos/harness/dispatch.py` | Agent loop — triggers compaction at 75% threshold and on control tool calls |
| `hephaistos/chat/usage.py` | `ContextBudget`, `SessionUsage`, `TokenUsage`, `compaction_urgency()` |
| `hephaistos/chat/events.py` | `CompactRequestEvent` — steering-queue event |
| `hephaistos/app/commands.py` | `CompactCommand` — `/compact` shell command handler |

## Entry points for modification

- Change the micro-compaction threshold: adjust `PLACEHOLDER_THRESHOLD` or `KEEP_RECENT` in `hephaistos/harness/compact.py`.
- Change the auto-compaction trigger point: adjust the `0.75` factor in `hephaistos/harness/dispatch.py`.
- Change how many recent exchanges are preserved: adjust `KEEP_RECENT_EXCHANGES` in `hephaistos/harness/compact.py`.
- Change the summarization prompt: update the `summary_prompt` string in `auto_compact()`.
