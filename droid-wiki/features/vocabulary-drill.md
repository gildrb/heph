# Vocabulary drill

Hephaistos includes an interactive, zero-LLM vocabulary drill system based on Anki-style spaced repetition. Vocabulary tables are embedded directly in armory Markdown files, and the drill runs entirely in the TUI without any API calls.

## Purpose

Enable spaced-repetition review of vocabulary extracted from study materials. Cards are parsed from Markdown tables in armory files, scheduled with SM-2, and drilled interactively.

## Directory layout

```
hephaistos/vocab/
├── __init__.py
├── parser.py             # scan_armory(), parse_vocab_file()
├── scheduler.py          # schedule_card(), select_due_cards()
├── drill.py              # run_drill() — interactive TUI session
└── state.py              # VocabCardState, VocabScheduleStore
```

## Key abstractions

| Abstraction | Source file | Purpose |
|---|---|---|
| `VocabCard` | `hephaistos/vocab/parser.py` | Frozen card: `front`, `back`, `source_file` |
| `VocabDeck` | `hephaistos/vocab/parser.py` | Collection of cards from an armory scan |
| `VocabCardState` | `hephaistos/vocab/state.py` | Persistent scheduling state: repetitions, easiness, interval, timestamps |
| `VocabScheduleStore` | `hephaistos/vocab/state.py` | Per-armory JSON store for card scheduling state |
| `Rating` | `hephaistos/vocab/scheduler.py` | IntEnum: `HARD` (3), `GOOD` (4), `EASY` (5) — SM-2 quality levels |
| `ScheduleResult` | `hephaistos/vocab/scheduler.py` | Computed next state: repetitions, easiness, interval_days |
| `DrillResult` | `hephaistos/vocab/drill.py` | Session summary: cards reviewed, counts per rating |

## How it works

### Parsing vocabulary tables

`scan_armory()` in `hephaistos/vocab/parser.py` recursively searches `source/` and `library/` directories for `*.md` files. `parse_vocab_file()` detects Markdown tables whose headers match recognized column aliases:

**Front column aliases**: `word`, `front`, `term`, `source`, `foreign`, `question`, `prompt`, `l1`, `source_word`

**Back column aliases**: `translation`, `back`, `definition`, `target`, `answer`, `meaning`, `l2`, `target_word`

Example table:

```markdown
| word | translation |
|------|-------------|
| chat | cat         |
| chien | dog        |
```

Each row becomes a `VocabCard`. The parser validates that both the separator row and data rows conform to Markdown table syntax.

### SM-2 scheduling

`schedule_card()` in `hephaistos/vocab/scheduler.py` implements Anki's modified SM-2 algorithm:

- **Hard** (quality 3): Easiness decreases, short interval.
- **Good** (quality 4): Easiness unchanged, standard interval progression (1 day → 6 days → then scaled by easiness).
- **Easy** (quality 5): Easiness increases, interval boosted.

Easiness has a floor of 1.3 and intervals are capped at 365 days.

### Card selection

`select_due_cards()` returns cards that are due for review, sorted by priority:
1. **Overdue cards** — most overdue first.
2. **New cards** — never reviewed.

An optional `limit` parameter caps the number of cards returned.

### Interactive drill session

`run_drill()` in `hephaistos/vocab/drill.py` is a zero-LLM TUI flow:

1. Scan the armory for vocab cards (`scan_armory()`).
2. Load or create the schedule store (`load_schedule()`).
3. Sync the deck with the store — new cards are added, removed cards are pruned, existing scheduling is preserved.
4. Select due cards and present them one at a time.
5. For each card:
   - Display the front (the word to translate).
   - Collect the user's typed answer.
   - Show a comparison (user answer vs. correct answer) with fuzzy matching.
   - Ask for a rating (Hard / Good / Easy) via a menu.
   - Apply SM-2 scheduling and show the next review interval.
6. Persist all changes and display a session summary.

Users can stop early with `Ctrl+C`. The drill tracks hard/good/easy counts and estimates when the next session will be needed.

### State persistence

`VocabScheduleStore` persists to `.hephaistos/vocab_schedule.json` per armory. Cards are keyed by `source_file:front`. The store supports:
- **`sync_with_deck()`**: Reconcile with the latest deck — adds new cards, removes deleted ones, preserves scheduling progress, updates changed answers.
- **`reset_all()`**: Reset all cards to unscheduled state.
- **`stats()`**: Returns counts for total, new, due, and mastered cards.

### Integration with `/vocab`

The TUI detects vocabulary tables when loading an armory and displays a hint: *"Use /vocab to start a drill."* The `/vocab` shell command invokes `run_drill()`.

## Integration points

- **Armory system**: Vocabulary tables live in armory `source/` and `library/` directories.
- **TUI shell**: `hephaistos/app/shell.py` detects vocab decks on armory load and shows a hint.
- **Commands**: `hephaistos/app/commands.py` likely registers the `/vocab` command that triggers `run_drill()`.

## Key source files

| File | Responsibility |
|---|---|
| `hephaistos/vocab/drill.py` | Interactive drill session, TUI I/O, session summary |
| `hephaistos/vocab/parser.py` | Markdown table parsing, armory scanning |
| `hephaistos/vocab/scheduler.py` | SM-2 algorithm, due card selection |
| `hephaistos/vocab/state.py` | `VocabCardState`, `VocabScheduleStore`, JSON persistence |

## Entry points for modification

- Add new column aliases: update `_FRONT_ALIASES` or `_BACK_ALIASES` in `hephaistos/vocab/parser.py`.
- Change the SM-2 parameters: adjust `_MIN_EASINESS`, `_DEFAULT_EASINESS`, or `_MAX_INTERVAL_DAYS` in `hephaistos/vocab/scheduler.py`.
- Change the drill flow: modify `run_drill()` in `hephaistos/vocab/drill.py` — it is self-contained TUI logic.
- Add a new rating level: extend the `Rating` enum and adjust `schedule_card()`.
