# Cleanup opportunities

This page tracks complexity hotspots and maintenance opportunities in the codebase. These are areas where refactoring would improve maintainability — not active bugs.

## Largest source files

These files dominate the codebase and would benefit from splitting:

| File | Lines | Notes |
|------|-------|-------|
| `hephaistos/app/commands.py` | 1,765 | All slash commands in one file. Could split into per-command modules. |
| `hephaistos/app/tui.py` | 1,408 | Largest single file. TUI widget composition and event handling could extract into separate widget modules. |
| `hephaistos/app/shell.py` | 1,000 | prompt-toolkit shell. Smaller than the other two but still substantial. |
| `hephaistos/harness/rag/retrieve.py` | 931 | Retrieval logic with multiple strategies. The different retrieval methods could be extracted. |
| `hephaistos/harness/tools.py` | 795 | Tool definitions and handlers. Each tool could be its own module. |

The three `app` files (`commands.py` + `tui.py` + `shell.py`) total 4,173 lines — more than 20% of the source code.

## Largest test files

| File | Lines |
|------|-------|
| `tests/test_app_tui.py` | 1,409 |
| `tests/test_rag_retrieve.py` | 1,132 |
| `tests/test_app_shell.py` | 1,001 |
| `tests/test_rag_chunker.py` | 485 |

Large test files tend to mirror large source files. Splitting source files would naturally split the tests.

## Suggested refactorings

### Split `commands.py` into per-command modules

`hephaistos/app/commands.py` at 1,765 lines handles all slash commands (`/model`, `/armory`, `/study`, `/vocab`, etc.). Each command is a self-contained function or class. Moving each command into its own module under `hephaistos/app/commands/` would make the code easier to navigate and test independently.

Current structure:
```
hephaistos/app/commands.py  (1,765 lines, all commands)
```

Possible structure:
```
hephaistos/app/commands/
    __init__.py       (registry and dispatch)
    model.py          (/model command)
    armory.py         (/armory command)
    study.py          (/study command)
    vocab.py          (/vocab command)
    ...
```

### Extract TUI widgets from `tui.py`

`hephaistos/app/tui.py` at 1,408 lines contains the full Textual app class, all widget compositions, event handlers, and styling. The widget tree and event handling could be extracted into separate widget modules:

```
hephaistos/app/tui/
    __init__.py
    app.py            (HephaistosApp class)
    composer.py       (input composer widget)
    messages.py       (message list widget)
    sidebar.py        (sidebar widget)
    ...
```

### Split RAG retrieval strategies

`hephaistos/harness/rag/retrieve.py` at 931 lines contains multiple retrieval strategies (BM25, semantic, hybrid). Each strategy could be a separate module with a common interface.

## Complexity metrics

Run complexity analysis with:

```bash
uv run radon cc hephaistos -a -nc --total-average
```

The CI runs this check on every PR via `.github/workflows/ci.yml`.
