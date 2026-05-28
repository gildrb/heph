# TUI Resize Smoke Test

Use this runbook when changing the Textual TUI layout, composer, completion menu,
transcript rendering, or side panel behavior.

1. Run the pseudo-terminal resize smoke:

   ```bash
   uv run python -m scripts.tui_resize_smoke
   ```

2. Launch a real armory in a normal terminal:

   ```bash
   uv run heph PATH_TO_ARMORY
   ```

   Repeat the same check inside a tmux split, because pane PTYs can expose stale
   terminal-size reads that ordinary terminal windows hide.

3. Repeat the resize check in each of these visible states:
   - empty composer with the placeholder visible
   - `/` typed so the slash-command completion menu is visible
   - `/settings` open as an inline menu
   - `/materials` open with the materials list focused
   - `/armory` open as an inline browser
4. Drag the terminal repeatedly across these transitions for each state:
   - wide to narrow and back, crossing the side-panel threshold
   - tall to short and back, crossing the compact composer threshold
   - quick diagonal resizes that change width and height together
5. Confirm the screen remains clean after every resize:
   - exactly one composer is visible
   - no stale composer placeholder, completion row, inline menu, transcript line, footer, or side panel
     remains painted in old positions
   - transcript text reflows or clips cleanly
   - focus remains in the composer unless an intentional inline flow owns focus
   - repeated resize spam does not produce visible lag or repaint storms

The headless regression tests cover the structural invariants, but this smoke test is still
required for terminal-cell artifacts that only appear in a real terminal emulator.
