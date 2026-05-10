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

## Devin Secrets Needed

No secrets are required for layout-only or slash-command QA. For full chat/RAG QA:

- `OPENAI_API_KEY` — for OpenAI-backed chat and RAG testing
- `OPENROUTER_API_KEY` — fallback for chat testing via OpenRouter

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

## tuistory Installation Notes

`tuistory@latest` might fail to install due to unavailable npm dependencies (e.g. `ghostty-opentui@^1.4.13`). If this happens, fall back to an older version:

```bash
npm install -g tuistory@0.0.16
```

Version 0.0.16 provides all needed commands: `launch`, `snapshot`, `screenshot`, `type`, `press`, `scroll`, `resize`, `wait`, `close`.

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
```

## TUI Layout Stress Testing

When testing layout fixes or changes to `hephaistos/tui/style.py`, always include a small-terminal stress test:

### Small terminal (80×8) — composer reachability

This tests that the composer and footer remain visible when the transcript overflows in a constrained terminal.

```bash
# Launch in a very small terminal
env -u CI tuistory launch "uv run heph $TEST_ARMORY" -s qa-small --cols 80 --rows 8 --cwd "$PWD"

# Generate long output through the real composer path (no LLM auth needed)
tuistory type -s qa-small "!seq -f 'layout stress line %02g' 0 79"
tuistory press -s qa-small enter
tuistory wait -s qa-small "layout stress line 79" --timeout 10000

# Verify composer is still visible
tuistory snapshot -s qa-small --trim
tuistory screenshot -s qa-small -o small-after-stress.png --format png --pixel-ratio 2
# VERIFY: snapshot shows composer placeholder AND footer hints on the last 2 lines

# Test scrolling
tuistory scroll -s qa-small up 8 --x 40 --y 3
tuistory snapshot -s qa-small --trim
# VERIFY: earlier transcript lines visible, composer still pinned at bottom

tuistory scroll -s qa-small down 8 --x 40 --y 3
tuistory snapshot -s qa-small --trim
# VERIFY: latest transcript line visible again, composer still pinned

# Test composer still accepts input
tuistory type -s qa-small "/help"
tuistory press -s qa-small enter
tuistory snapshot -s qa-small --trim
# VERIFY: help output appears in transcript, composer functional

tuistory close -s qa-small
```

### Pass/fail criteria

- **PASS**: Every snapshot shows the composer placeholder text AND footer hints within the terminal rows
- **FAIL**: Any snapshot shows the composer or footer missing/cut off, or the transcript pushing content below the viewport

### Key layout details

- `#transcript` uses `height: 1fr` to stay bounded within `#shell` vertical space
- `#composer-frame` uses `height: auto` and sits below transcript
- RichLog handles internal transcript scrolling; the outer shell does NOT scroll
- The bug pattern to watch for: `height: auto` on transcript causes it to auto-size to content, pushing composer below viewport in small terminals

## Session Launch Commands

Plain chat (no armory):

```bash
env -u CI tuistory launch "uv run heph" -s qa-plain --cols 110 --rows 36 --cwd "$PWD"
```

Armory-attached:

```bash
env -u CI tuistory launch "uv run heph $TEST_ARMORY" -s qa-armory --cols 110 --rows 36 --cwd "$PWD"
```

## Cleanup

After testing, always close tuistory sessions and remove only the QA armory:

```bash
tuistory close -s qa-small 2>/dev/null || true
tuistory close -s qa-plain 2>/dev/null || true
tuistory close -s qa-armory 2>/dev/null || true
rm -rf "$TEST_ARMORY"
```

Never remove pre-existing armories or user config files.
