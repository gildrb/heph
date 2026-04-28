## QA Report

| #   | Test Case | App | Persona | Result | Notes |
| --- | --------- | --- | ------- | ------ | ----- |
| 1 | TUI Launch and Banner | cli | configured_user | :white_check_mark: PASS | TUI launched, banner visible, status bar shows provider |
| 2 | /status | cli | configured_user | :white_check_mark: PASS | All fields present: Model, Session, API, Key, Mode, Tools, Messages |
| 3 | /help + aliases | cli | configured_user | :white_check_mark: PASS | /help, /h, /? all show full command list |
| 4 | Autocomplete dropdown | cli | configured_user | :white_check_mark: PASS | Dropdown appears on `/`, filters on `/st` showing status/stats |
| 5 | /provider listing | cli | configured_user | :white_check_mark: PASS | Shows pollinations, openrouter, openai-codex, zai, custom |
| 6 | /provider use zai glm-5 | cli | configured_user | :white_check_mark: PASS | Switched to Z.AI/GLM, status bar updated |
| 7 | /models catalog | cli | configured_user | :white_check_mark: PASS | Models grouped by provider with context/pricing/tags |
| 8 | /recommend | cli | configured_user | :white_check_mark: PASS | Study-filtered model recommendations with rationale |
| 9 | /model glm-5-turbo | cli | configured_user | :white_check_mark: PASS | Model switched, status bar confirmed |
| 10 | /api status | cli | configured_user | :white_check_mark: PASS | Shows Base URL, masked API key, source (env ZAI_API_KEY) |
| 11 | /memory status | cli | configured_user | :white_check_mark: PASS | Shows backend, Supermemory disabled, profile, entries |
| 12 | /persona | cli | configured_user | :white_check_mark: PASS | 5 personas listed, Drill Engine marked current |
| 13 | Chat streaming response | cli | configured_user | :white_check_mark: PASS | Message sent, thinking indicator shown, response received |
| 14 | /tokens show/hide | cli | configured_user | :white_check_mark: PASS | Toggles between shown/hidden states |
| 15 | /cost show/hide | cli | configured_user | :white_check_mark: PASS | Toggles between shown/hidden states |
| 16 | /history | cli | configured_user | :white_check_mark: PASS | Shows Turns: 1, message counts, char/token estimates |
| 17 | /evidence (no RAG) | cli | configured_user | :white_check_mark: PASS | "No evidence was retrieved" message shown |
| 18 | /usage | cli | configured_user | :white_check_mark: PASS | Shows API calls, tokens, cost |
| 19 | /save (no armory) | cli | configured_user | :white_check_mark: PASS | Correct error: "cannot save chat without an active armory" |
| 20 | /export | cli | configured_user | :white_check_mark: PASS | Exported to /tmp/qa-export-test.md, file contains conversation |
| 21 | /compact | cli | configured_user | :white_check_mark: PASS | Summarized conversation, "Compacted." confirmed |
| 22 | /edit (cancel) | cli | configured_user | :white_check_mark: PASS | Shows last message prompt, empty input cancels |
| 23 | /new | cli | configured_user | :white_check_mark: PASS | "New chat started." confirmed |
| 24 | Chat in new session | cli | configured_user | :white_check_mark: PASS | Message sent and response received in new session |
| 25 | /sessions (no armory) | cli | configured_user | :white_check_mark: PASS | Prompts for armory path when none attached |
| 26 | /chats (no armory) | cli | configured_user | :white_check_mark: PASS | Prompts for armory path when none attached |
| 27 | Armory attachment | cli | armory_user | :white_check_mark: PASS | TUI relaunches with armory, status shows armory/sources/tools |
| 28 | Chat with RAG | cli | armory_user | :white_check_mark: PASS | Response references source material with evidence |
| 29 | /evidence after RAG | cli | armory_user | :white_check_mark: PASS | Shows E1 with source, chunk=0, score=0.411 |
| 30 | /vocab status | cli | armory_user | :white_check_mark: PASS | 8 cards detected from 2 source files, 8 due |
| 31 | /vocab drill | cli | armory_user | :white_check_mark: PASS | Card 1/8 shown, answer evaluated, feedback given |
| 32 | /remind | cli | armory_user | :white_check_mark: PASS | 7 due cards, 1 scheduled for 23h, due cards listed |
| 33 | /stats | cli | armory_user | :white_check_mark: PASS | Full stats: session + armory + vocab + study mode |
| 34 | /import | cli | armory_user | :white_check_mark: PASS | Imported 1 file, confirmed in output |
| 35 | /index | cli | armory_user | :no_entry: BLOCKED | IndexCommand class exists but is NOT registered in CommandRegistry |
| 36 | /settings menu | cli | armory_user | :white_check_mark: PASS | All 7 menu options visible, escape cancels |
| 37 | /clear | cli | armory_user | :white_check_mark: PASS | Confirmation dialog, cancel works, confirm clears chat |
| 38 | /resume | cli | armory_user | :white_check_mark: PASS | Command executes without error (no sessions to resume) |
| 39 | Error handling | cli | all | :white_check_mark: PASS | Unknown cmd, invalid model, missing args all produce user-friendly errors |
| 40 | /quit and /exit | cli | all | :white_check_mark: PASS | /quit exits TUI cleanly, session status: dead |

Result values: :white_check_mark: PASS, :x: FAIL, :no_entry: BLOCKED, :warning: FLAKY, :grey_question: INCONCLUSIVE

### Action Required

1. **BUG: IndexCommand not registered** -- The `IndexCommand` class exists in `hephaistos/app/commands.py` (line 1615) but is not included in the `get_registry()` function's command list (lines 1731-1764). Add `IndexCommand` to the registration tuple to wire up `/index`.

<details>
<summary>Screenshots & Evidence</summary>

### Snapshot 1: TUI initial screen

```
Hephaistos v0.1.0  armory none  model openai  api free  source none
                                                                                
Ask anything... "What do I need to study next?"
enter send  tab complete  /help commands  ctrl+d exit
```

### Snapshot 2: /status output

```
Armory:    none
  Session:   530b1b5b78bb
  Title:     (untitled)
  Model:     openai
  Persona:   Drill Engine
  API:       https://text.pollinations.ai/openai
  Key:       not needed (free provider)
  Mode:      plain chat
  Tools:     0
  Messages:  0
```

### Snapshot 3: /help output

```
Commands
  /persona    Show or switch the agent persona
  /provider   Show or switch LLM provider and model
  /recommend  Recommend models for study sessions
  /remind     Show upcoming study reminders and due cards
  /save       Save current chat to armory
  /sessions   List or resume saved sessions
  /settings   Manage cross-session preferences
  /vocab      Vocabulary drill with spaced repetition
```

### Snapshot 4: Autocomplete dropdown

```
/help                  Show available commands
/exit                  Leave the shell
/login                 Authenticate via OAuth
/logout                Clear stored OAuth credentials
/status                Show armory, session, and model info
```

### Snapshot 5: Provider switch

```
Switched to Z.AI / GLM / glm-5
Status bar: model glm-5  api configured
```

### Snapshot 6: /models output

```
zai
  glm-4.5-flash    128k ctx  $0.0001/$0.0001 [study]
  glm-5             128k ctx  $0.0010/$0.0010
  glm-5-turbo       128k ctx  $0.0001/$0.0001
```

### Snapshot 7: Chat with RAG response

```
You: What is machine learning?

According to source/test-notes.md, machine learning is a subset of artificial
intelligence that enables systems to learn from data.

evidence: E1 source/test-notes.md#chunk=0 score=0.411
```

### Snapshot 8: /vocab drill

```
-- Card 1/8 --
Word:   BST
Type translation: Binary Search Tree

Your answer:    Binary Search Tree
Correct answer: Binary Search Tree
-> Next review in 1 day
```

### Snapshot 9: /stats output

```
Armory:
  Path:       /private/tmp/qa-1777372534/armory
  Saved:      0 sessions
  API calls:  1
  Tokens:     2771
  Cost:       $0.0001

Vocabulary:
  Total cards:  8
  New:          7
  Due now:      7
  Mastered:     0 (0%)

Study mode:
  Phase:     waiting_for_ready
  Item:      What is machine learning?
```

### Snapshot 10: /index error

```
You: /index list
error: Unknown command: /index list
```

### Snapshot 11: Error handling

```
error: Unknown command: /nonexistent_command
error: Model unavailable.
error: Usage: /api key <your-api-key>
```

</details>
