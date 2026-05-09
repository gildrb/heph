---
name: qa-cli
description: >
  Manual/functional QA for the Hephaistos CLI/TUI app. Uses tuistory to test
  the current slash-command surface, onboarding, model/auth flows, chat,
  source-grounded RAG, materials controls, armory management, sessions,
  vocabulary/study features, settings, and error handling.
---

# QA Tests: Hephaistos CLI/TUI

## Testing Target

This is a local CLI tool. There is no remote deployment. The QA agent must:

1. **Build**: Run `uv sync --frozen` from the project root to ensure dependencies are installed.
2. **Prepare**: Create a named QA armory under `~/.armories/<qa-run-id>` with study materials in `materials/`.
3. **Authenticate**: Prefer existing Hephaistos OpenAI Codex/ChatGPT auth, `OPENAI_API_KEY`, or `OPENROUTER_API_KEY`. Use `/login` -> `OpenAI Codex` if subscription auth is missing and the user can complete browser auth.
4. **Launch**: Use tuistory to launch the TUI with a stable terminal size.
5. **Test**: Interact with the running TUI by sending keystrokes and capturing text snapshots.
6. **Cleanup**: Exit TUI sessions cleanly, remove only the named QA armory created by this run, and preserve all pre-existing user config/credentials.

Use session names such as `qa-plain`, `qa-armory`, and `qa-interactive` with `--cols 110 --rows 36` for consistent output.

## Authentication

Hephaistos uses LLM provider access, not traditional app auth. Full chat/RAG QA should use subscription-backed or API-key-backed auth whenever available.

Preferred order:

1. **Hephaistos OpenAI Codex OAuth**: `/login` -> `OpenAI Codex` (ChatGPT Plus/Pro subscription). Credentials are stored in `~/.config/hephaistos/auth.json`; never print token values.
2. **OpenAI API key**: `OPENAI_API_KEY` or `HEPHAISTOS_API_KEY`, if already present.
3. **OpenRouter API key**: `OPENROUTER_API_KEY`, if already present.
4. **Custom OpenAI-compatible endpoint**: only when the user provides endpoint/model/key for the run.
5. **Pollinations keyless**: acceptable only for lightweight smoke chat; do not treat it as sufficient for full chat/RAG if unstable or rate-limited.

Z.AI is no longer the default QA provider. Do not require `ZAI_API_KEY` for QA, and do not fail QA solely because Z.AI has no balance.

## Current Slash Command Surface

The current TUI command surface is:

`/help`, `/exit`, `/login`, `/logout`, `/status`, `/new`, `/armory`, `/compact`, `/evidence`, `/tokens`, `/cost`, `/stats`, `/export`, `/import`, `/remind`, `/edit`, `/models`, `/recommend`, `/memory`, `/persona`, `/settings`, `/sessions`, `/index`, `/usage`, `/vocab`.

The TUI also exposes `/materials` as an inline materials/retrieval-source browser even though it is not part of the shared terminal command registry.

Aliases:

- `/help`: `/h`, `/?`
- `/exit`: `/quit`, `/q`
- `/vocab`: `/v`

Do not test removed/stale commands (`/provider`, `/model`, `/history`, `/clear`, `/resume`, `/chats`) unless the application reintroduces them.

## TUI Interaction Notes

- The TUI is a Textual app with a command composer at the bottom and transcript/log area above.
- Slash commands are typed into the composer and submitted with Enter.
- Autocomplete suggestions appear when typing `/` or partial slash commands.
- Inline menus are used for `/login`, `/logout`, `/settings`, `/models`, `/sessions`, `/materials`, and the armory browser.
- Terminal-interactive flows such as `/edit`, `/persona` without args, and `/vocab` must be completed or cancelled before the next slash command.
- After autocomplete or any inline menu, press Escape until the normal composer returns before continuing.
- Avoid command batching. Type one command, wait for visible state/output, snapshot, and only then continue.

## Pre-test Setup

Before launching the TUI, create the test armory with material files under `~/.armories`:

```bash
RUN_ID="heph-qa-$(date +%s)"
TEST_ARMORY="$HOME/.armories/$RUN_ID"
uv run heph armory init "$TEST_ARMORY"
mkdir -p "$TEST_ARMORY/materials"
cat > "$TEST_ARMORY/materials/test-notes.md" << 'EOF'
# Computer Science Basics

Machine learning is a subset of artificial intelligence that enables systems to learn from data.
A neural network is a computing system inspired by biological neural networks.

| Term | Definition |
|------|------------|
| ML | Machine Learning -- systems that learn from data |
| AI | Artificial Intelligence -- machines that mimic cognition |
| Neural Network | Computing system inspired by biological neural networks |
| Deep Learning | ML using multi-layered neural networks |
| Algorithm | Step-by-step procedure for calculations |
EOF

cat > "$TEST_ARMORY/materials/second-notes.md" << 'EOF'
# Data Structures

Binary search trees allow O(log n) lookup when balanced.
Hash tables provide O(1) average lookup for key-value data.

| Term | Definition |
|------|------------|
| BST | Binary Search Tree |
| Hash Table | Key-value store with O(1) average lookup |
| Linked List | Linear data structure with sequential access |
EOF

cat > "$TEST_ARMORY/materials/rag-target.md" << 'EOF'
# Retrieval QA Target

The QA sentinel fact is: Hephaistos retrieval should mention the phrase amber forge when asked about the sentinel.
Only this file contains the exact phrase amber forge.
EOF
```

This setup supports RAG, materials filtering, vocab, reminders, import, index, and session persistence tests.

## Launch Commands

Plain/no-armory session:

```bash
env -u CI tuistory launch "uv run heph" -s qa-plain --cols 110 --rows 36 --cwd "$PWD"
```

Armory session:

```bash
env -u CI tuistory launch "uv run heph $TEST_ARMORY" -s qa-armory --cols 110 --rows 36 --cwd "$PWD"
```

If the first-time launch prompts for a module name, type `q` and press Enter to reach plain chat without creating an armory. Do not type `skip` at the module-name prompt; `skip` is treated as an armory name there.

## Full Current Regression Matrix

Execute ALL flows below in order. Report each flow as a separate test case in the results table.

---

### Flow 1: First-time TUI launch / onboarding skip

**Tests**: startup, onboarding, no-armory home

1. Launch `qa-plain` with `uv run heph`.
2. If prompted for module name, type `q` and press Enter.
3. Snapshot initial TUI.
4. VERIFY: Hephaistos status/header or no-armory home appears; composer is visible; no Python traceback.

---

### Flow 2: `/help`, `/h`, and `/?`

**Tests**: command reference and aliases

1. Type `/help` and press Enter.
2. Snapshot help output.
3. VERIFY: Help lists the current command surface above and does NOT list stale commands (`/provider`, `/model`, `/history`, `/clear`, `/resume`, `/chats`).
4. Type `/h`, press Enter, verify help appears.
5. Type `/?`, press Enter, verify help appears.

---

### Flow 3: Slash autocomplete and filtering

**Tests**: autocomplete dropdown

1. Type `/` and wait for suggestions.
2. Snapshot dropdown.
3. VERIFY: suggestions include multiple current commands.
4. Press Escape to close.
5. Type `/st` and wait for filtered suggestions.
6. Snapshot filtered dropdown.
7. VERIFY: suggestions include `/status` and `/stats`.
8. Press Escape until normal composer returns.

---

### Flow 4: `/status` in plain chat

**Tests**: session status

1. Type `/status`, press Enter.
2. Snapshot status output.
3. VERIFY: shows Session, Model, API, Key, Mode, Tools, Messages, Tokens, Cost, Dirty.

---

### Flow 5: Command palette (`ctrl+p`)

**Tests**: keyboard command palette

1. Press `ctrl+p`.
2. Snapshot command palette/suggestions.
3. VERIFY: current slash commands are offered.
4. Press Escape to close.

---

### Flow 6: Armory browser from plain chat

**Tests**: `ctrl+a`, `/armory` browser entry/cancel

1. Press `ctrl+a`.
2. Snapshot armory browser.
3. VERIFY: armory browser/home opens and lists known armories or creation/open options.
4. Press Escape to return.
5. Type `/armory`, press Enter.
6. Snapshot browser again, then Escape.

---

### Flow 7: `/login` and `/logout` menus with safe cancel

**Tests**: provider auth menu

1. Type `/login`, press Enter.
2. Snapshot login menu.
3. VERIFY: options include OpenAI Codex, OpenRouter, Z.AI, Custom endpoint.
4. Press Escape to cancel; do not enter or print secrets.
5. Type `/logout`, press Enter.
6. Snapshot logout menu or empty-state notice.
7. VERIFY: stored credentials are listed or a friendly no-credentials message appears.
8. Press Escape to cancel if a logout menu is open. Do not confirm logout or clear user credentials.

---

### Flow 8: OpenAI Codex availability / login if needed

**Tests**: ChatGPT/OpenAI Codex auth readiness

1. If Hephaistos OpenAI Codex auth or `OPENAI_API_KEY`/`HEPHAISTOS_API_KEY` is already available, continue.
2. Otherwise open `/login`, choose `OpenAI Codex`, and ask the user to complete browser auth.
3. Snapshot resulting notice/status.
4. VERIFY: status or notice indicates OpenAI Codex/provider configured. If user/browser auth cannot complete, mark chat/RAG dependent flows BLOCKED.

---

### Flow 9: `/models` menu and selection

**Tests**: model picker

1. Type `/models`, press Enter.
2. Snapshot model picker.
3. VERIFY: models are listed with current/source/free markers as applicable.
4. Filter for `gpt` if OpenAI Codex is available; otherwise choose an accessible non-Z.AI model.
5. Select a model and snapshot confirmation.
6. Type `/status`; VERIFY model/provider reflect the selected model.

---

### Flow 10: `/recommend`

**Tests**: study model recommendations

1. Type `/recommend`, press Enter.
2. Snapshot output.
3. VERIFY: study recommendations render with context/pricing/tags and no traceback.

---

### Flow 11: `/settings` root menu

**Tests**: settings menu

1. Type `/settings`, press Enter.
2. Snapshot root menu.
3. VERIFY: shows Privacy & Diagnostics, Appearance, Login, Logout.
4. Press Escape to close.

---

### Flow 12: Settings -> Privacy & Diagnostics

**Tests**: privacy settings submenu

1. Open `/settings`.
2. Select Privacy & Diagnostics.
3. Snapshot submenu.
4. VERIFY: Usage analytics and Crash reports options show enabled/disabled and availability.
5. Press Escape back to root, then Escape to close.

---

### Flow 13: Settings -> Appearance

**Tests**: theme selector

1. Open `/settings`.
2. Select Appearance.
3. Snapshot theme list.
4. VERIFY: available theme presets are listed and current theme is marked.
5. Press Escape back to root, then Escape to close.

---

### Flow 14: `/memory status`

**Tests**: memory status

1. Type `/memory status`, press Enter.
2. Snapshot output.
3. VERIFY: Backend, Supermemory status, Profile, Key, Key source, URL env, Entries render.

---

### Flow 15: `/memory profile`

**Tests**: memory profile display

1. Type `/memory profile`, press Enter.
2. Snapshot output.
3. VERIFY: current memory profile is displayed.

---

### Flow 16: `/tokens` controls

**Tests**: token display toggles

1. Type `/tokens show`; VERIFY "Live tokens shown."
2. Type `/tokens hide`; VERIFY "Live tokens hidden."
3. Type `/tokens`; VERIFY state toggles without error.
4. Snapshot one toggle result.

---

### Flow 17: `/cost` controls

**Tests**: cost display toggles

1. Type `/cost show`; VERIFY "Live cost shown."
2. Type `/cost hide`; VERIFY "Live cost hidden."
3. Type `/cost`; VERIFY state toggles without error.
4. Snapshot one toggle result.

---

### Flow 18: No-armory chat guidance

**Tests**: plain/no-armory chat guardrail

1. Type `What is 2+2? Answer with just the number.` and press Enter.
2. Wait for response completion.
3. Snapshot response.
4. VERIFY: with no armory attached, the assistant tells the user to create/open an armory instead of answering from outside study materials; no provider balance/rate-limit error.

---

### Flow 19: `/usage` after no-armory chat

**Tests**: usage accounting

1. Type `/usage`, press Enter.
2. Snapshot output.
3. VERIFY: usage fields render. A guarded no-armory reply may be local and therefore may legitimately show zero API calls/tokens.

---

### Flow 20: `/stats` after no-armory chat

**Tests**: plain session stats

1. Type `/stats`, press Enter.
2. Snapshot output.
3. VERIFY: Turns >= 1, Assistant messages >= 1, and tokens/cost fields render.

---

### Flow 21: `/export` after chat

**Tests**: session export

1. Type `/export /tmp/heph-qa-export.md`, press Enter.
2. Snapshot confirmation.
3. Outside TUI, verify the file exists and contains the user prompt and assistant response.

---

### Flow 22: `/compact` with history

**Tests**: conversation compaction

1. Type `/compact`, press Enter.
2. Wait for summary/compaction to complete.
3. Snapshot output.
4. VERIFY: compaction completes without error. If LLM auth is unavailable, mark BLOCKED.

---

### Flow 23: `/edit` cancel path

**Tests**: terminal-interactive edit prompt

1. Use a separate `qa-interactive` session with at least one user message, or continue if safe.
2. Type `/edit`, press Enter.
3. Snapshot prompt showing last user message.
4. Press Enter with empty input.
5. VERIFY: "Cancelled." appears and no resend occurs.

---

### Flow 24: `/new` starts a fresh chat

**Tests**: session replacement/autosave

1. Type `/new`, press Enter.
2. Snapshot result.
3. VERIFY: "New chat started." and visible transcript is cleared/reset.

---

### Flow 25: CLI armory commands

**Tests**: `heph armory init/open`

1. Outside TUI, run `uv run heph armory init "$TEST_ARMORY"` during setup if not already done.
2. Run `uv run heph armory open "$TEST_ARMORY"`.
3. VERIFY: command validates/opens the armory without error.

---

### Flow 26: CLI materials commands

**Tests**: `heph materials list/count/index`

1. Outside TUI, run `uv run heph materials list "$TEST_ARMORY"`.
2. Run `uv run heph materials count "$TEST_ARMORY"`.
3. Run `uv run heph materials index "$TEST_ARMORY"`.
4. VERIFY: materials are listed/counted and index build completes.

---

### Flow 27: CLI source alias commands

**Tests**: `heph source list/count/index`

1. Outside TUI, run `uv run heph source list "$TEST_ARMORY"`.
2. Run `uv run heph source count "$TEST_ARMORY"`.
3. Run `uv run heph source index "$TEST_ARMORY"`.
4. VERIFY: source alias behaves like materials commands.

---

### Flow 28: Armory-attached TUI launch

**Tests**: armory mode startup

1. Launch `qa-armory` with `uv run heph "$TEST_ARMORY"`.
2. Snapshot initial screen.
3. VERIFY: status/header shows armory path/name and materials count.

---

### Flow 29: `/status` with armory

**Tests**: armory status details

1. Type `/status`, press Enter.
2. Snapshot output.
3. VERIFY: armory path, Mode `agent (tools)`, Tools count, Messages, and materials/source count render.

---

### Flow 30: `/materials` inline browser

**Tests**: materials selector

1. Type `/materials`, press Enter.
2. Snapshot materials list.
3. VERIFY: `test-notes.md`, `second-notes.md`, and `rag-target.md` appear.
4. Press Escape to close.

---

### Flow 31: `/materials` filter

**Tests**: materials filtering

1. Type `/materials rag`, press Enter.
2. Snapshot filtered materials list.
3. VERIFY: `rag-target.md` is shown and unrelated files are filtered out.
4. Press Escape to close.

---

### Flow 32: Material enable/disable toggle

**Tests**: retrieval source selection

1. Open `/materials`.
2. Toggle one highlighted material with Space or Enter.
3. Snapshot active count/changed styling.
4. Toggle it back on.
5. Snapshot restored active count.
6. Press Escape to close.

---

### Flow 33: RAG chat with source-grounded answer

**Tests**: retrieval-augmented chat

1. Type `Using the source files, what is the QA sentinel phrase? Answer with the exact phrase.` and press Enter.
2. Wait for response completion.
3. Snapshot response.
4. VERIFY: response includes `amber forge`. If subscription auth is unavailable, mark BLOCKED.

---

### Flow 34: `/evidence` after RAG

**Tests**: retrieved evidence display

1. Type `/evidence`, press Enter.
2. Snapshot output.
3. VERIFY: evidence items include source/chunk/score and reference `rag-target.md` or relevant materials.

---

### Flow 35: RAG with material selection

**Tests**: disabled material exclusion

1. Disable `rag-target.md` from `/materials`.
2. Ask the sentinel phrase question again.
3. Snapshot response/evidence.
4. VERIFY: answer should not rely on disabled `rag-target.md`, or evidence excludes disabled source.
5. Re-enable `rag-target.md` before continuing.

---

### Flow 36: `/vocab status`

**Tests**: vocabulary card extraction

1. Type `/vocab status`, press Enter.
2. Snapshot output.
3. VERIFY: total cards > 0; source material files listed.

---

### Flow 37: `/vocab` drill

**Tests**: interactive vocabulary drill

1. Type `/vocab`, press Enter.
2. Snapshot first card.
3. Type a short answer, press Enter.
4. Snapshot feedback/correct answer/rating prompt.
5. Select or type `q` to stop cleanly.
6. VERIFY: no stuck prompt remains.

---

### Flow 38: `/vocab reset` cancel path

**Tests**: destructive confirmation cancel

1. Type `/vocab reset`, press Enter.
2. Snapshot confirmation prompt.
3. Choose No or type `q`.
4. VERIFY: "Cancelled." and schedule is not reset.

---

### Flow 39: `/remind`

**Tests**: study reminders

1. Type `/remind`, press Enter.
2. Snapshot output.
3. VERIFY: due cards count or "All caught up!" renders without error.

---

### Flow 40: `/stats` with armory/vocab

**Tests**: full stats

1. Type `/stats`, press Enter.
2. Snapshot output.
3. VERIFY: Current session, Armory, Vocabulary sections render.

---

### Flow 41: `/import`

**Tests**: material import

1. Outside TUI, create `/tmp/heph-qa-import.md` with markdown content.
2. Type `/import /tmp/heph-qa-import.md`, press Enter.
3. Snapshot output.
4. VERIFY: import reports 1 file and file appears under `$TEST_ARMORY/materials/`.

---

### Flow 42: `/index` list/add/remove

**Tests**: cross-armory index command

1. Type `/index list`, press Enter; snapshot list/empty state.
2. Type `/index add $TEST_ARMORY`, press Enter; verify added message.
3. Type `/index list`, press Enter; verify armory appears.
4. Type `/index remove $TEST_ARMORY`, press Enter; verify removed message.

---

### Flow 43: `/sessions list`

**Tests**: saved sessions listing

1. Ensure there has been at least one successful chat in the armory session, then type `/new` to trigger autosave.
2. Type `/sessions list`, press Enter.
3. Snapshot output.
4. VERIFY: saved session list appears, or a clear "No saved chats found" if no successful chat was possible.

---

### Flow 44: `/sessions browse`

**Tests**: sessions inline browse

1. Type `/sessions browse`, press Enter.
2. Snapshot sessions menu or empty-state notice.
3. VERIFY: no crash; if sessions exist, menu can be cancelled with Escape.

---

### Flow 45: `/sessions resume`

**Tests**: resume latest saved chat through current sessions command

1. Type `/sessions resume`, press Enter.
2. Snapshot result.
3. VERIFY: latest session resumes or a friendly empty-state message appears; no traceback.

---

### Flow 46: `/persona tutor`

**Tests**: direct persona switch

1. Type `/persona tutor`, press Enter.
2. Snapshot confirmation.
3. VERIFY: persona switches from current persona to Tutor or reports already/current state without error.
4. Type `/status` and verify Persona reflects the selected persona.

---

### Flow 47: `/persona` invalid slug

**Tests**: persona error handling

1. Type `/persona definitely-not-a-persona`, press Enter.
2. Snapshot output.
3. VERIFY: friendly unknown persona error and available persona list; no traceback.

---

### Flow 48: Shell escape

**Tests**: `!command` input

1. Type `!echo heph-qa-shell-ok`, press Enter.
2. Snapshot output.
3. VERIFY: output includes `heph-qa-shell-ok`.

---

### Flow 49: Negative command/subcommand handling

**Tests**: error boundaries

1. Type `/nonexistent_command`, press Enter; verify unknown command error.
2. Type `/memory nonsense`, press Enter; verify usage hint.
3. Type `/import /path/that/does/not/exist`, press Enter; verify path-not-found error.
4. Type `/index nonsense`, press Enter; verify usage hint.
5. Snapshot errors.
6. VERIFY: no Python traceback or crash.

---

### Flow 50: Clean exit

**Tests**: `/quit`, `/exit`

1. Type `/quit`, press Enter.
2. Snapshot final output if visible.
3. VERIFY: TUI terminates cleanly.
4. If still running, type `/exit`, press Enter, and verify termination.

## Diff-Targeted Extra Tests

After the matrix, inspect `git diff` and add focused manual flows for changed behavior not covered above. Current examples:

- If `hephaistos/parameters/cli.py` changed: exercise `uv run heph config list` manually and verify configurable settings render.
- If TUI styling/widgets/materials changed: capture an additional `/materials` and resize/reflow snapshot.
- If chat evidence/orchestrator changed: add one extra RAG prompt that requires citing a specific material and verify `/evidence`.
- If study controller changed: ask a study-style question and verify the response follows the current tutor/persona behavior.

## Post-test Verification

Outside the TUI, verify artifacts created by manual flows:

```bash
test -f /tmp/heph-qa-export.md && echo "Export OK"
test -f "$TEST_ARMORY/materials/heph-qa-import.md" && echo "Import OK"
ls "$TEST_ARMORY/.hephaistos" >/dev/null && echo "Armory metadata OK"
```

## Cleanup

After all tests complete:

1. Ensure all tuistory sessions have exited.
2. Delete only the QA armory created for this run, after confirming it is under `~/.armories/` and its basename starts with `heph-qa-`.
3. Delete only temporary files created by this run (`/tmp/heph-qa-export.md`, `/tmp/heph-qa-import.md`).
4. Preserve all pre-existing `~/.config/hephaistos/` files and provider credentials. Do not run `/logout all` as part of QA.

## Known Failure Modes

1. **TUI fails to launch without terminal.** Textual requires a real or emulated terminal. Use tuistory with `env -u CI`.
2. **First-time launch prompts for module name.** Type `q` and press Enter to reach plain chat. Typing `skip` at the module-name prompt creates an armory named `skip`.
3. **Armory creation under `/tmp` fails.** Armories must be created under `~/.armories/<name>`; materials belong in `materials/`.
4. **OpenAI Codex OAuth not yet configured.** Use `/login` -> `OpenAI Codex` and ask the user to complete the browser flow. Do not inspect or print token values.
5. **Keyring prompts or hangs.** Avoid direct keychain probes in shell scripts. Prefer environment checks, Hephaistos OAuth provider presence, or the in-app `/login` flow.
6. **Streaming response timing.** Wait 5-30 seconds depending on model load. Use snapshots and visible text changes rather than fixed sleeps alone.
7. **Interactive menus.** Use arrow keys + Enter or type-to-filter + Enter. Always press Escape to close before the next command.
8. **/vocab drill is interactive.** Answer, then rate or type `q` to stop. Do not send slash commands while the rating prompt is active.
9. **/edit waits for input.** Send empty input to cancel unless specifically testing resend.
10. **/compact requires LLM auth.** Mark BLOCKED if subscription/API auth is unavailable.
11. **Pollinations is keyless but unreliable.** It can be used for smoke tests only; full chat/RAG should use OpenAI Codex/OpenAI/OpenRouter/custom auth.
