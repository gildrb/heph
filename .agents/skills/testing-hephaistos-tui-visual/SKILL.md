---
name: testing-hephaistos-tui-visual
description: Test Hephaistos TUI visual transcript styling end-to-end. Use when verifying composer, transcript, or message background rendering changes.
---

# Hephaistos TUI Visual Testing

Use this for focused visual QA of the Textual TUI when the feature under test is transcript/composer rendering, colors, or background transparency.

## Devin Secrets Needed

- None for plain-session visual checks.
- For full model-backed chat/RAG testing, use whichever provider credential is available in this order: `OPENAI_API_KEY`, `HEPHAISTOS_API_KEY`, `OPENROUTER_API_KEY`, or interactive `/login` OpenAI Codex OAuth.

## Direct Plain-Session Launch

When no armory exists, `uv run heph` may show first-run `Module name:` onboarding before the TUI. To isolate composer/transcript rendering without onboarding or provider credentials, launch a plain local session directly:

```bash
uv run python -c "from hephaistos.chat.session import create_plain_session; from hephaistos.parameters.cli import load_config; from hephaistos.tui import run_tui; run_tui(create_plain_session(load_config()))"
```

This opens the Textual TUI with `armory_path=None`. Normal non-slash input is handled locally by the no-armory path, appending a user transcript entry followed by the deterministic reply that starts with `No armory is attached...`.

## Recording Checklist

1. Maximize the GUI terminal before recording.
2. Start recording only after setup is complete and the terminal is ready.
3. Annotate:
   - launch of the direct plain-session TUI,
   - pre-submit composer/transcript state,
   - submitted user-message row,
   - local no-armory assistant reply,
   - clean `/exit`.
4. Keep the run to one focused interaction unless testing a separate critical edge case.

## Core Assertions for Background/Transparency Changes

For transcript background changes, a strong single-flow test is:

1. Launch the direct plain-session TUI.
   - Pass: composer is focused and visible.
   - Pass: no `Module name:` onboarding prompt appears.
   - Pass: transcript area is not one continuous gray panel.
2. Type a short unique prompt such as `visual background test` and press Enter.
   - Pass: the exact user text appears as a transcript row.
   - Pass: the user row background matches the composer gray.
   - Pass: row background extends across the row, not only behind text cells.
3. Observe the no-armory reply.
   - Pass: reply includes `No armory is attached`.
   - Pass: reply is not painted with the user/composer gray background.
   - Pass: the main transcript does not become one large gray panel after the reply.
4. Type `/exit` and press Enter.
   - Pass: the shell prompt returns.

Use screenshots before and after submit in the report so reviewers can compare the transparent transcript area with the gray user/composer rows.
