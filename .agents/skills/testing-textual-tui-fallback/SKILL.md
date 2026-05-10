---
name: testing-textual-tui-fallback
description: Use Textual's runtime pilot to test Hephaistos TUI flows when tuistory cannot launch or when widget/state-level evidence is needed.
---

# Hephaistos Textual Pilot Fallback Testing

Use this skill when `.agents/skills/qa-cli/SKILL.md` is the right high-level QA path but `tuistory launch` fails, e.g. relay connection errors such as `Failed to connect to relay on port ...: fetch failed`.

This is a fallback for runtime TUI verification. Prefer `tuistory` for true terminal/PTY interaction when it works.

## Devin Secrets Needed

- None for local armory selector, startup, status, and materials-list flows.
- For chat/RAG flows, use existing Hephaistos OAuth or these secrets if available: `OPENAI_API_KEY`, `HEPHAISTOS_API_KEY`, or `OPENROUTER_API_KEY`. Never print token values.

## When This Fallback Is Appropriate

Use Textual pilot for:

- Slash-command flows that can be driven through the Textual composer.
- Inline widgets such as `/armory`, `/materials`, `/settings`, `/models`, and `/sessions`.
- Verifying rendered widget text, widget state, session state, transcript notices, and config persistence.
- Capturing `App.export_screenshot()` SVG evidence when terminal snapshots are unavailable.

Do not treat this as a full substitute for testing terminal-only behavior such as raw subprocess lifecycle, real PTY resize bugs, shell escape rendering, or external editor prompts. Mark those as untested or blocked if `tuistory` is unavailable.

## Pre-flight

From the repo root:

```bash
uv sync --frozen
uv run heph --help
tuistory --version
```

If `tuistory launch` fails, record the exact error in the test report and proceed with this fallback for flows that Textual pilot can cover.

## Runtime Pilot Pattern

Create a small script outside the repo working tree, e.g. under `~/heph-qa-artifacts/`, so it is not accidentally committed.

```python
from __future__ import annotations

import asyncio
from pathlib import Path

from hephaistos import tui
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession


def plain_session() -> ChatSession:
    conversation = Conversation()
    conversation.add("system", "test")
    return ChatSession(
        config=ChatConfig(base_url="https://example.test", model="test-model"),
        conversation=conversation,
        session_id="session-qa",
    )


def text_of(widget: object) -> str:
    rendered = widget.render()  # type: ignore[attr-defined]
    return str(getattr(rendered, "plain", rendered))


async def main() -> None:
    app = tui.HephaistosTui(
        plain_session(),
        tui._TuiRuntimeState(),  # type: ignore[attr-defined]
        tui.current_palette(),
    )
    async with app.run_test(size=(140, 36)) as pilot:
        composer = app.query_one("#composer", tui.Input)
        composer.value = "/armory"
        await pilot.press("enter")
        await pilot.pause()

        header = text_of(app.query_one("#armory-header", tui.Static))
        current = app.query_one("#armory-current-inline", tui.OptionList)
        labels = [str(getattr(option.prompt, "plain", option.prompt)) for option in current.options]
        Path("armory-selector.svg").write_text(
            app.export_screenshot(title="Armory selector"),
            encoding="utf-8",
        )
        print(header)
        print(labels)

asyncio.run(main())
```

Useful selectors and state:

- Composer: `#composer` (`tui.Input`)
- Status: `#status` (`tui.Static`)
- Transcript content: `app.state.transcript`
- Armory selector: `#armory-current-inline`, `#armory-header`, `#armory-mode-hint`, `#armory-current-label`, `#armory-preview-label`, `#armory-error-inline`
- Materials selector: `#materials-list`, `#materials-header`, `#materials-footer`
- Armory entries: `app._armory_entries` for path/section/recent metadata when needed
- Session state: `app.session.armory_path`, `app.session.source_file_count`, `app.session.source_files`

## Evidence Capture

- Save screenshots with `app.export_screenshot(title="...")`.
- Attach SVGs directly, or convert to PNG if `rsvg-convert` is available:

```bash
rsvg-convert armory-selector.svg -o armory-selector.png
```

- Save a JSON evidence file with the relevant rendered text, session state, and config values.
- If a PR is under test, post exactly one PR comment with concise pass/fail assertions and collapsed evidence sections.

## Config and Armory Cleanup

If a test manipulates `~/.config/hephaistos/config.json` or creates temporary armories:

1. Back up `~/.config/hephaistos/config.json` before writing.
2. Create QA armories only under `~/.armories/` with a unique prefix such as `heph-prNN-*` or `heph-qa-*`.
3. In a `finally` block, restore the config backup and delete only armories matching the test prefix.
4. Call `settings_store.invalidate_settings_cache()` after config writes/restores.

Never delete or overwrite arbitrary user armories or provider credentials.

## Armory Selector Assertions

For `/armory` changes, verify both UI and persistence:

- The selector opens from the composer with `/armory`.
- Recent armories are capped to the expected count and invalid/stale paths are hidden.
- `all armories` includes the target armory.
- Removed navigation affordances such as `parents`, `enter/right open`, `c choose`, or dot separators are absent when relevant.
- Highlighting an armory and pressing Enter closes the selector and updates `app.session.armory_path`.
- `app.session.source_file_count` and `app.session.source_files` match the target materials.
- `/materials` lists the target material files.
- Fresh startup discovery through `tui.create_startup_session(config)` resumes the expected last armory.
- Persisted `last_armory_path` and `recent_armories` in config match the expected MRU order and cap.
