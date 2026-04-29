---
name: qa-cli
description: >
  QA tests for the Hephaistos CLI/TUI app. Tests interactive Textual TUI flows
  covering every slash command, armory management, chat, provider switching,
  study features, and error handling. Uses tuistory for all TUI interactions.
  Run as a full regression suite -- the orchestrator executes ALL flows in sequence.
---

# QA Tests: Hephaistos CLI/TUI

## Testing Target

This is a local CLI tool. There is no remote deployment. The QA agent must:

1. **Build**: Run `uv sync --frozen` from the project root to ensure dependencies are installed
2. **Launch**: Use tuistory to launch the TUI binary: `env -u CI FACTORY_DISABLE_KEYRING=true ZAI_API_KEY=$ZAI_API_KEY tuistory launch "uv run heph" -s qa-test --cols 110 --rows 36`
3. **Test**: Interact with the running TUI by sending keystrokes and capturing snapshots
4. **Cleanup**: Exit the TUI cleanly, then delete any test armories

In CI, prefix launch with `env -u CI FACTORY_DISABLE_KEYRING=true` to avoid Ink CI detection issues.

Use session name `-s qa-test` with `--cols 110 --rows 36` for consistent output.

## Authentication

Hephaistos uses LLM provider API keys, not traditional auth. The primary test provider is Z.AI/GLM:

- **Env var**: `ZAI_API_KEY` -- provided by the CI workflow via GitHub secrets
- **How consumed**: The app reads it from the environment variable automatically, or via the OS keyring
- **Keyring**: Disable keyring in CI with `FACTORY_DISABLE_KEYRING=true` to avoid interactive prompts

For the `first_time_user` persona, NO API key is needed (tests read-only flows only).

## TUI Interaction Notes

- The TUI is a Textual app with a command input at the bottom and a chat log area above
- Slash commands are typed into the input field and submitted with Enter
- Autocomplete suggestions appear in a dropdown below the input
- The armory browser is a modal screen that overlays the main TUI
- Status information is shown in a status bar / info panel
- The banner/logo displays on startup
- Streaming responses appear incrementally in the chat area
- Some commands trigger interactive menus (select_option) -- these use arrow keys + Enter in the TUI
- Use the `tuistory` skill for all TUI interactions (snapshot, send_keys, wait_for_text, etc.)

## Pre-test Setup

Before launching the TUI, create the test armory with proper source files:

```bash
RUN_ID="qa-$(date +%s)"
TEST_ARMORY="/tmp/$RUN_ID/armory"
uv run heph armory init "$TEST_ARMORY"
mkdir -p "$TEST_ARMORY/source"
cat > "$TEST_ARMORY/source/test-notes.md" << 'EOF'
# Computer Science Basics

Machine learning is a subset of artificial intelligence that enables systems to learn from data.

| Term | Definition |
|------|------------|
| ML | Machine Learning -- systems that learn from data |
| AI | Artificial Intelligence -- machines that mimic cognition |
| Neural Network | Computing system inspired by biological neural networks |
| Deep Learning | ML using multi-layered neural networks |
| Algorithm | Step-by-step procedure for calculations |
EOF

cat > "$TEST_ARMORY/source/second-notes.md" << 'EOF'
# Data Structures

Binary search trees allow O(log n) lookup when balanced.

| Term | Definition |
|------|------------|
| BST | Binary Search Tree |
| Hash Table | Key-value store with O(1) average lookup |
| Linked List | Linear data structure with sequential access |
EOF
```

This ensures vocab and study tests have proper data.

## Full Regression Test Sequence

Execute ALL flows below in order as a single regression suite. Each flow tests one or more slash commands. Report each flow as a separate test case in the results table.

---

### Flow 1: TUI Launch and Banner

**Covers**: `tui.py`, `cli.py`, `banner.py`
**Tests**: TUI startup

**Steps**:
1. Launch TUI: `env -u CI FACTORY_DISABLE_KEYRING=true ZAI_API_KEY=$ZAI_API_KEY tuistory launch "uv run heph" -s qa-test --cols 110 --rows 36`
2. Wait for the banner/logo to appear (look for "Hephaistos" or ASCII art)
3. Take snapshot: `### Snapshot 1: TUI initial screen`
4. **VERIFY**: Banner text is visible, input prompt is present, no Python tracebacks or import errors

**Success**: TUI launches cleanly with banner visible.

---

### Flow 2: `/status` -- Session Status

**Covers**: `commands.py` (StatusCommand), `tui.py` (status display)
**Tests**: `/status`

**Steps**:
1. Type `/status` and press Enter
2. Wait for status output
3. Take snapshot: `### Snapshot 2: /status output`
4. **VERIFY**: Shows Model, API, Key status, Session ID. For default config: shows Pollinations or Z.AI provider info. "Messages: 0" (fresh session)

**Success**: Status displays all fields without errors.

---

### Flow 3: `/help` -- Command Reference

**Covers**: `commands.py` (HelpCommand), `autocomplete.py`
**Tests**: `/help`, `/h`, `/?`

**Steps**:
1. Type `/help` and press Enter
2. Wait for help text
3. Take snapshot: `### Snapshot 3: /help output`
4. **VERIFY**: Shows "Commands" section with at least: help, exit, status, clear, model, provider, settings, export, vocab, usage, sessions, new, save, history, evidence, tokens, cost, stats, persona, memory, api, login, logout, index, recommend, remind, compact, edit, import, armory, chats, resume
5. Type `/h` and press Enter (alias test)
6. **VERIFY**: Same help text appears
7. Type `/?` and press Enter (alias test)
8. **VERIFY**: Same help text appears

**Success**: All three invocations show the full command list.

---

### Flow 4: Autocomplete Dropdown

**Covers**: `autocomplete.py`, `tui.py` (suggester)
**Tests**: Slash command autocomplete

**Steps**:
1. Clear input, type just `/`
2. Wait for autocomplete dropdown
3. Take snapshot: `### Snapshot 4: Autocomplete dropdown`
4. **VERIFY**: Dropdown shows multiple slash command suggestions
5. Type `/st` to filter
6. Take snapshot: `### Snapshot 5: Filtered autocomplete /st`
7. **VERIFY**: Suggestions narrow to commands containing "st" (status, stats, study)
8. Press Escape to dismiss dropdown

**Success**: Autocomplete appears and filters correctly.

---

### Flow 5: `/provider` -- Provider Listing

**Covers**: `commands.py` (ProviderCommand), `providers/`
**Tests**: `/provider`

**Steps**:
1. Type `/provider` and press Enter
2. Wait for provider list
3. Take snapshot: `### Snapshot 6: /provider output`
4. **VERIFY**: Shows configured providers (pollinations, openrouter, openai-codex, zai, custom). Shows which is active with "active" marker. Shows model lists per provider.

**Success**: Provider list renders with all expected providers.

---

### Flow 6: `/provider use` -- Switch Provider

**Covers**: `commands.py` (ProviderCommand._use), `providers/config.py`
**Tests**: `/provider use <slug>`

**Steps**:
1. Type `/provider use zai glm-5` and press Enter
2. Wait for confirmation
3. Take snapshot: `### Snapshot 7: Provider switch`
4. **VERIFY**: Shows "Switched to Z.AI / GLM / glm-5" or similar
5. Type `/status` and press Enter
6. Take snapshot: `### Snapshot 8: Status after provider switch`
7. **VERIFY**: Status shows z.ai endpoint URL and glm-5 model

**Success**: Provider switches, status reflects the change.

---

### Flow 7: `/models` -- Model Catalog

**Covers**: `commands.py` (ModelsCommand), `providers/registry.py`
**Tests**: `/models`

**Steps**:
1. Type `/models` and press Enter
2. Wait for model list
3. Take snapshot: `### Snapshot 9: /models output`
4. **VERIFY**: Shows models grouped by provider with context window size, pricing, and tags. Shows at least Z.AI models (glm-5, glm-5-turbo, etc.)

**Success**: Model catalog renders with pricing and context info.

---

### Flow 8: `/recommend` -- Study Model Recommendations

**Covers**: `commands.py` (RecommendCommand)
**Tests**: `/recommend`

**Steps**:
1. Type `/recommend` and press Enter
2. Wait for recommendation output
3. Take snapshot: `### Snapshot 10: /recommend output`
4. **VERIFY**: Shows models filtered for study use. Shows info text about study model selection criteria.

**Success**: Study recommendations display with rationale.

---

### Flow 9: `/model` -- Model Switch

**Covers**: `commands.py` (ModelCommand)
**Tests**: `/model <name>`

**Steps**:
1. Type `/model glm-5-turbo` and press Enter
2. Wait for confirmation
3. Take snapshot: `### Snapshot 11: Model switch`
4. **VERIFY**: Shows "Model: glm-5 -> glm-5-turbo" or similar
5. Type `/status` and press Enter
6. **VERIFY**: Status shows glm-5-turbo as current model

**Success**: Model switches and status confirms it.

---

### Flow 10: `/api` -- API Key Status

**Covers**: `commands.py` (ApiCommand), `providers/keyring_store.py`
**Tests**: `/api`

**Steps**:
1. Type `/api` and press Enter
2. Wait for API info
3. Take snapshot: `### Snapshot 12: /api output`
4. **VERIFY**: Shows Base URL, API Key status (masked or "configured"), Source (env or keychain)

**Success**: API status displays key resolution info.

---

### Flow 11: `/memory status` -- Memory Backend Status

**Covers**: `commands.py` (MemoryCommand), `memory/`
**Tests**: `/memory status`

**Steps**:
1. Type `/memory status` and press Enter
2. Wait for memory info
3. Take snapshot: `### Snapshot 13: /memory status`
4. **VERIFY**: Shows Backend type, Supermemory enabled/disabled, Profile, Key status, Entries count

**Success**: Memory status displays backend info.

---

### Flow 12: `/persona` -- Persona Display

**Covers**: `commands.py` (PersonaCommand), `harness/persona.py`
**Tests**: `/persona`

**Steps**:
1. Type `/persona` and press Enter
2. Wait for persona menu/selection
3. Take snapshot: `### Snapshot 14: /persona output`
4. **VERIFY**: Shows available personas with descriptions, current one marked. Cancel/escape without selecting.

**Success**: Persona list renders with current marked.

---

### Flow 13: Chat -- Send Message and Receive Streaming Response

**Covers**: `chat/`, `tui.py` (chat display), `shell.py`
**Tests**: Core chat functionality

**Steps**:
1. Type "What is 2+2? Answer with just the number." and press Enter
2. Wait for streaming response to begin (watch for characters appearing)
3. Take snapshot: `### Snapshot 15: Streaming response in progress`
4. Wait for streaming to complete (at least 15 seconds, or until no new text for 5s)
5. Take snapshot: `### Snapshot 16: Completed response`
6. **VERIFY**: Response contains "4" or a reasonable answer. No error messages.

**Success**: Message sent, streaming works, response is sensible.

---

### Flow 14: `/tokens` -- Toggle Token Display

**Covers**: `commands.py` (TokensCommand)
**Tests**: `/tokens`

**Steps**:
1. Type `/tokens show` and press Enter
2. Wait for confirmation
3. Take snapshot: `### Snapshot 17: /tokens show`
4. **VERIFY**: Shows "Live tokens shown."
5. Type `/tokens hide` and press Enter
6. **VERIFY**: Shows "Live tokens hidden."
7. Type `/tokens` (toggle) and press Enter
8. **VERIFY**: Shows toggled state

**Success**: Token visibility toggles correctly.

---

### Flow 15: `/cost` -- Toggle Cost Display

**Covers**: `commands.py` (CostCommand)
**Tests**: `/cost`

**Steps**:
1. Type `/cost show` and press Enter
2. Wait for confirmation
3. Take snapshot: `### Snapshot 18: /cost show`
4. **VERIFY**: Shows "Live cost shown."
5. Type `/cost hide` and press Enter
6. **VERIFY**: Shows "Live cost hidden."

**Success**: Cost visibility toggles correctly.

---

### Flow 16: `/history` -- Conversation History

**Covers**: `commands.py` (HistoryCommand)
**Tests**: `/history`

**Steps**:
1. Type `/history` and press Enter
2. Wait for history output
3. Take snapshot: `### Snapshot 19: /history output`
4. **VERIFY**: Shows "Turns: 1" (from the chat in Flow 13), User/Assistant message counts, ~Tokens estimate, API calls >= 1

**Success**: History shows accurate turn and token counts.

---

### Flow 17: `/evidence` -- Source Evidence

**Covers**: `commands.py` (EvidenceCommand)
**Tests**: `/evidence`

**Steps**:
1. Type `/evidence` and press Enter
2. Wait for output
3. Take snapshot: `### Snapshot 20: /evidence output`
4. **VERIFY**: Either shows evidence items (if RAG was active) or shows "No evidence was retrieved" message. Either is acceptable.

**Success**: Command runs without error (evidence may or may not be present).

---

### Flow 18: `/usage` -- Token Usage

**Covers**: `commands.py` (UsageCommand), `chat/usage.py`
**Tests**: `/usage`

**Steps**:
1. Type `/usage` and press Enter
2. Wait for usage output
3. Take snapshot: `### Snapshot 21: /usage output`
4. **VERIFY**: Shows API calls >= 1, prompt tokens > 0, completion tokens > 0, total tokens > 0, estimated cost > $0

**Success**: Usage shows non-zero values after chat activity.

---

### Flow 19: `/save` -- Save Session

**Covers**: `commands.py` (SaveCommand), `chat/storage.py`
**Tests**: `/save`

**Steps**:
1. Type `/save` and press Enter
2. Wait for save confirmation
3. Take snapshot: `### Snapshot 22: /save output`
4. **VERIFY**: Shows "Saved to <path>" message

**Success**: Session saves successfully.

---

### Flow 20: `/export` -- Export Session to Markdown

**Covers**: `commands.py` (ExportCommand)
**Tests**: `/export <path>`

**Steps**:
1. Type `/export /tmp/qa-export-test.md` and press Enter
2. Wait for export confirmation
3. Take snapshot: `### Snapshot 23: /export output`
4. **VERIFY**: Shows "Session exported to /tmp/qa-export-test.md"
5. (Outside TUI) Verify file exists and contains user/assistant messages: `cat /tmp/qa-export-test.md`

**Success**: Export file created with conversation content.

---

### Flow 21: `/compact` -- Conversation Compaction

**Covers**: `commands.py` (CompactCommand), `harness/compact.py`
**Tests**: `/compact`

**Steps**:
1. Type `/compact` and press Enter
2. Wait for compaction to complete (may take 10-20 seconds as it calls the LLM)
3. Take snapshot: `### Snapshot 24: /compact output`
4. **VERIFY**: Shows "Compacting..." then a summary, then "Compacted." message

**Success**: Conversation is summarized and compacted without error.

---

### Flow 22: `/edit` -- Edit Last Message

**Covers**: `commands.py` (EditCommand)
**Tests**: `/edit`

**Steps**:
1. Type `/edit` and press Enter
2. Wait for "Last message:" prompt
3. Take snapshot: `### Snapshot 25: /edit prompt`
4. **VERIFY**: Shows the last user message content
5. Press Enter with empty input to cancel (do not resend)
6. **VERIFY**: Shows "Cancelled." message

**Success**: Edit shows last message and cancels cleanly on empty input.

---

### Flow 23: `/new` -- New Chat Session

**Covers**: `commands.py` (NewCommand)
**Tests**: `/new`

**Steps**:
1. Type `/new` and press Enter
2. Wait for confirmation
3. Take snapshot: `### Snapshot 26: /new output`
4. **VERIFY**: Shows "New chat started." or similar. Chat log should be cleared.

**Success**: New session created, previous session auto-saved.

---

### Flow 24: Chat in New Session

**Covers**: `chat/`, `tui.py`
**Tests**: Chat after session reset

**Steps**:
1. Type "Hello, what model are you?" and press Enter
2. Wait for response (15+ seconds)
3. Take snapshot: `### Snapshot 27: Chat in new session`
4. **VERIFY**: Response mentions a model name or LLM identity

**Success**: Chat works in new session.

---

### Flow 25: `/sessions` -- List Saved Sessions

**Covers**: `commands.py` (SessionsCommand), `chat/storage.py`
**Tests**: `/sessions`

**Steps**:
1. Type `/sessions` and press Enter
2. Wait for session list
3. Take snapshot: `### Snapshot 28: /sessions output`
4. **VERIFY**: Shows at least one saved session (from Flow 19 save). Shows session ID, title, date.

**Success**: Session list shows previously saved session.

---

### Flow 26: `/chats` -- List Saved Chats

**Covers**: `commands.py` (ChatsCommand)
**Tests**: `/chats`

**Steps**:
1. Type `/chats` and press Enter
2. Wait for output
3. Take snapshot: `### Snapshot 29: /chats output`
4. **VERIFY**: Shows saved chats list or appropriate message. No error.

**Success**: Command executes without error.

---

### Flow 27: Armory-Attached Session

**Covers**: `armory_browser.py`, `armory/`, `tui.py` (browser screen)
**Tests**: Armory attachment, `/armory`

**Steps**:
1. Exit current TUI: type `/exit` and press Enter
2. Relaunch TUI with test armory: `env -u CI FACTORY_DISABLE_KEYRING=true ZAI_API_KEY=$ZAI_API_KEY tuistory launch "uv run heph $TEST_ARMORY" -s qa-test --cols 110 --rows 36`
3. Wait for TUI to load
4. Take snapshot: `### Snapshot 30: TUI with armory attached`
5. Type `/status` and press Enter
6. Take snapshot: `### Snapshot 31: Status with armory`
7. **VERIFY**: Shows armory path, "Mode: agent (tools)", source file count = 2, Tools: 7

**Success**: TUI launches with armory, status shows armory details.

---

### Flow 28: Chat with Armory (RAG-Enhanced)

**Covers**: `chat/`, `harness/rag/`
**Tests**: Source-informed chat

**Steps**:
1. Type "What is machine learning? Use the source files." and press Enter
2. Wait for response (15+ seconds)
3. Take snapshot: `### Snapshot 32: RAG-enhanced response`
4. **VERIFY**: Response references concepts from the source files (ML, AI, etc.)

**Success**: Response includes source-informed content.

---

### Flow 29: `/evidence` -- Evidence After RAG Query

**Covers**: `commands.py` (EvidenceCommand)
**Tests**: `/evidence` after RAG retrieval

**Steps**:
1. Type `/evidence` and press Enter
2. Wait for output
3. Take snapshot: `### Snapshot 33: Evidence after RAG`
4. **VERIFY**: Shows retrieved evidence items with source, chunk index, score. Items reference source files.

**Success**: Evidence shows retrieved chunks from source files.

---

### Flow 30: `/vocab status` -- Vocabulary Status

**Covers**: `commands.py` (VocabCommand), `vocab/`
**Tests**: `/vocab status`

**Steps**:
1. Type `/vocab status` and press Enter
2. Wait for output
3. Take snapshot: `### Snapshot 34: /vocab status`
4. **VERIFY**: Shows Total cards > 0 (should find cards from markdown tables), New count, Due now, Source files listed

**Success**: Vocab cards detected from source file tables.

---

### Flow 31: `/vocab` -- Vocabulary Drill

**Covers**: `commands.py` (VocabCommand), `vocab/drill.py`, `vocab/scheduler.py`
**Tests**: `/vocab` (interactive drill)

**Steps**:
1. Type `/vocab` and press Enter
2. Wait for drill prompt (first card)
3. Take snapshot: `### Snapshot 35: Vocab drill prompt`
4. **VERIFY**: Shows a vocabulary question/prompt from the source material
5. Type a brief answer and press Enter
6. Wait for feedback
7. Take snapshot: `### Snapshot 36: Vocab drill feedback`
8. **VERIFY**: Shows feedback on the answer (quality rating or next card)

**Success**: Vocab drill starts, accepts answers, provides feedback.

---

### Flow 32: `/remind` -- Study Reminders

**Covers**: `commands.py` (RemindCommand)
**Tests**: `/remind`

**Steps**:
1. Type `/remind` and press Enter
2. Wait for output
3. Take snapshot: `### Snapshot 37: /remind output`
4. **VERIFY**: Shows due cards count, next review timing, or "All caught up!" message

**Success**: Reminder information displays without error.

---

### Flow 33: `/stats` -- Full Statistics

**Covers**: `commands.py` (StatsCommand)
**Tests**: `/stats`

**Steps**:
1. Type `/stats` and press Enter
2. Wait for stats output
3. Take snapshot: `### Snapshot 38: /stats output`
4. **VERIFY**: Shows session stats (Session ID, Runtime, Turns, API calls, Tokens, Cost). Shows armory stats (Path, Saved sessions, totals). Shows vocabulary stats (Total cards, New, Due now, Mastered).

**Success**: Full stats display with session, armory, and vocab sections.

---

### Flow 34: `/import` -- Import Files

**Covers**: `commands.py` (ImportCommand)
**Tests**: `/import <path>`

**Steps**:
1. Create a temp file outside TUI: `echo "# Imported Notes\n\nSome content here." > /tmp/qa-import-test.md`
2. Type `/import /tmp/qa-import-test.md` and press Enter
3. Wait for output
4. Take snapshot: `### Snapshot 39: /import output`
5. **VERIFY**: Shows "Imported 1 file: qa-import-test.md" or similar

**Success**: File imported into armory source directory.

---

### Flow 35: `/index` -- Cross-Armory Index

**Covers**: `commands.py` (IndexCommand)
**Tests**: `/index list`, `/index add`, `/index remove`

**Steps**:
1. Type `/index list` and press Enter
2. Take snapshot: `### Snapshot 40: /index list`
3. **VERIFY**: Shows indexed armories list (may be empty or show current armory)
4. Type `/index add $TEST_ARMORY` and press Enter
5. Take snapshot: `### Snapshot 41: /index add`
6. **VERIFY**: Shows "Added <path>. N armory/armories indexed."
7. Type `/index list` and press Enter
8. **VERIFY**: Now shows the added armory
9. Type `/index remove $TEST_ARMORY` and press Enter
10. **VERIFY**: Shows "Removed <path>."

**Success**: Index add/list/remove cycle works correctly.

---

### Flow 36: `/settings` -- Settings Menu

**Covers**: `commands.py` (SettingsCommand), `parameters/`
**Tests**: `/settings`

**Steps**:
1. Type `/settings` and press Enter
2. Wait for settings menu to appear
3. Take snapshot: `### Snapshot 42: /settings menu`
4. **VERIFY**: Shows menu options: Interface, Telemetry, Appearance, Startup, Default model, Study memory, Provider & credentials, Back
5. Cancel/escape back to chat

**Success**: Settings menu renders with all expected options.

---

### Flow 37: `/clear` -- Clear Conversation

**Covers**: `commands.py` (ClearCommand)
**Tests**: `/clear`

**Steps**:
1. Type `/clear` and press Enter
2. If prompted to confirm, press Enter for "No" (cancel) to test the confirmation dialog
3. Take snapshot: `### Snapshot 43: /clear cancelled`
4. **VERIFY**: Shows "Cancelled." or chat is preserved
5. Type `/clear` and press Enter again
6. If prompted, confirm (press Enter for "Yes")
7. Take snapshot: `### Snapshot 44: /clear confirmed`
8. **VERIFY**: Shows "Started fresh session." Chat log is cleared

**Success**: Clear with cancel preserves chat, clear with confirm resets.

---

### Flow 38: `/resume` -- Resume Session

**Covers**: `commands.py` (ResumeCommand)
**Tests**: `/resume`

**Steps**:
1. Type `/resume` and press Enter
2. Wait for output (may show session list or resume latest)
3. Take snapshot: `### Snapshot 45: /resume output`
4. **VERIFY**: Either resumes the latest session or shows available sessions. No crash.

**Success**: Resume command executes without error.

---

### Flow 39: Error Handling -- Invalid Commands

**Covers**: `commands.py`, `tui.py`, `chat/resilience.py`
**Tests**: Error boundaries

**Steps**:
1. Type `/nonexistent_command` and press Enter
2. Take snapshot: `### Snapshot 46: Unknown command error`
3. **VERIFY**: Shows "Unknown command" or similar error, NOT a Python traceback
4. Type `/model totally_invalid_model_xyz123` and press Enter
5. Take snapshot: `### Snapshot 47: Invalid model error`
6. **VERIFY**: Shows "Model unavailable" or error, NOT a crash
7. Type `/api key` and press Enter (missing key value)
8. Take snapshot: `### Snapshot 48: Missing argument error`
9. **VERIFY**: Shows usage hint, NOT a crash
10. Type `/vocab reset` and press Enter (if armory attached, may prompt -- cancel)
11. **VERIFY**: Prompts for confirmation or shows usage, NOT a crash

**Success**: All invalid inputs produce user-friendly errors, never crashes.

---

### Flow 40: `/exit` -- Clean Exit

**Covers**: `commands.py` (ExitCommand, QuitCommand)
**Tests**: `/exit`, `/quit`

**Steps**:
1. Type `/quit` and press Enter
2. Take snapshot: `### Snapshot 49: /quit output`
3. **VERIFY**: Shows "Exiting... (/quit -> /exit)" then exits
4. If TUI doesn't exit, type `/exit` and press Enter
5. **VERIFY**: TUI terminates cleanly

**Success**: TUI exits cleanly via slash command.

---

## Post-test Verification

After all flows, run these checks outside the TUI:

1. Verify export file exists: `test -f /tmp/qa-export-test.md && echo "Export OK"`
2. Verify imported file is in armory: `ls $TEST_ARMORY/source/`
3. Verify saved sessions: `ls $TEST_ARMORY/.hephaistos/sessions/`

## Cleanup

After all tests complete:

1. TUI should already be exited from Flow 40
2. Remove test armories: `rm -rf /tmp/qa-*/tmp/qa-export-test.md /tmp/qa-import-test.md`
3. Remove any test config: `rm -f ~/.config/hephaistos/providers.toml` (only if created during test)

## Known Failure Modes

1. **TUI fails to launch without terminal.** Textual requires a real or emulated terminal. In CI, tuistory provides a virtual terminal. If Textual fails to start, ensure `env -u CI` is set to suppress CI detection.

2. **Keyring prompts block the TUI.** Always use `FACTORY_DISABLE_KEYRING=true` in CI and testing environments to prevent interactive keyring prompts.

3. **Z.AI API rate limits or errors.** The Z.AI API may return 429 errors under heavy use. If chat flows fail with rate-limit errors, report as BLOCKED and retry after 30 seconds. The free Pollinations provider is even more rate-limited.

4. **Streaming response timing.** Streaming responses may take 5-30 seconds depending on model load. Wait at least 15 seconds for a response before timing out. Use tuistory's `wait_for_text` with a 30-second timeout.

5. **Interactive menus (select_option).** Commands like `/model`, `/provider`, `/persona`, `/settings` launch interactive menus with arrow-key navigation. In tuistory, use arrow keys to navigate and Enter to select. If the menu doesn't render, the command may still work with direct arguments (e.g., `/model glm-5`).

6. **/vocab requires markdown tables.** The vocab parser looks for markdown tables with specific column headers (Term | Definition). Pre-test setup creates these files. If /vocab reports 0 cards, check that the source files were created correctly.

7. **/compact requires LLM call.** The compact command calls the LLM to summarize, so it needs a working API key and may take 15-30 seconds. Report as BLOCKED if the API key is missing.

8. **/edit waits for input.** The /edit command prompts for a new message. Always send empty input (just Enter) to cancel, otherwise it will resend a message and change the conversation state.

9. **/clear confirmation dialog.** The /clear command asks "Clear conversation?" when there are messages. In tuistory, handle this with Enter for default (No) or type "y" and Enter for Yes.

10. **/vocab drill is interactive.** The vocab drill shows cards one at a time and waits for answers. Each card requires typing an answer and pressing Enter. The drill ends when all due cards are reviewed or the user cancels.
