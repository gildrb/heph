---
name: qa-cli-fallback
description: Fallback manual QA guidance for Hephaistos CLI/TUI when tuistory cannot launch or its relay cannot connect. Use after qa-cli setup when terminal harness issues block runtime TUI evidence.
---

# Hephaistos CLI/TUI QA fallback

Use this skill only after the primary `.agents/skills/qa-cli/SKILL.md` tuistory path fails for an environment/tooling reason, such as `Failed to connect to relay on port 19977: fetch failed`.

## Devin Secrets Needed

- None for local armory selector, startup, `/status`, or `/materials` verification.
- `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, or Hephaistos OpenAI Codex OAuth is only needed for full chat/RAG answer verification.

## When tuistory fails

1. Confirm the issue is harness-level, not app-level, by trying a minimal session:
   ```bash
   tuistory launch "bash -lc 'echo tuistory-smoke; sleep 1'" -s tuistory-smoke --cols 80 --rows 24 --timeout 5000
   tail -80 /tmp/tuistory/relay-server.log 2>/dev/null || true
   ```
2. If the smoke session also fails, report the tuistory relay issue as operational friction/blocker and continue with Textual's runtime pilot for app-level assertions.
3. State the harness limitation clearly in the test report and PR comment. Do not claim a tuistory/manual terminal recording was captured.

## Textual runtime-pilot fallback

For focused TUI flows, use the real `hephaistos.tui.HephaistosTui` app with `run_test(...)` rather than mocking the changed path. The fallback should still exercise user-facing routing where possible:

- Create a real disposable armory under `~/.armories/heph-qa-<run-id>`.
- Back up `~/.config/hephaistos/config.json` before the run and restore it afterward, because `known_armories` and `last_armory_path` are persisted there.
- Open the TUI with a plain `ChatSession` and `tui._TuiRuntimeState()`.
- Put `/armory` into `#composer` and press Enter with `pilot.press("enter")` to open the selector.
- Highlight the target `#armory-current-inline` entry and press Enter to exercise `_armory_open_highlighted()` through the TUI event path.
- Assert the selector closes, `session.armory_path` equals the test armory, and `session.source_file_count` matches the material fixture count.
- Open `/materials` through the composer and assert `_materials_entries` contains the fixture material paths.
- For MRU startup, invalidate the settings cache and call `create_startup_session(...)`; assert it returns the same last-opened armory and source count.

## Evidence capture

Textual apps can export SVG screenshots during `run_test`:

```python
path.write_text(app.export_screenshot(title="QA evidence"), encoding="utf-8")
```

Attach those SVGs and a JSON/text assertion log to the final test report. Keep screenshots full-frame; do not crop terminal evidence unless explicitly requested.

## Cleanup

- Restore the pre-test `~/.config/hephaistos/config.json` exactly.
- Remove only the disposable QA armory created for the run.
- Keep fallback scripts and assertion output outside the repo unless the user asks for them to be committed.
