---
version: "0.0.49"
name: "Heph CLI"
description: "Terminal and Textual design specification for the Heph local document harness."
source_of_truth:
  - "packages/interfaces/src/interfaces/palette/__init__.py"
  - "packages/interfaces/src/interfaces/terminal/__init__.py"
  - "packages/interfaces/src/interfaces/tui/style.py"
  - "packages/interfaces/src/interfaces/tui/display_text.py"
  - "packages/interfaces/src/interfaces/tui/transcript.py"
default_theme: "dark"
theme_presets:
  - "dark"
  - "light"
---

# Heph CLI Design

Heph CLI is a quiet, local-first terminal workspace for accurate, cited answers. The
interface should feel like a focused reading and thinking instrument: sparse chrome, strong
text hierarchy, exact evidence labels, and no decorative color.

This file documents the CLI and TUI only. It is not the website system. Terminal cells,
Textual CSS, ANSI styles, one-line status bars, and fixed-width side panels belong here.
Website layout, responsive spacing, radius, media, and native browser interaction rules
belong in `design.md`.

The CLI source of truth is the current repository. Concrete color values live in
`packages/interfaces/src/interfaces/palette/__init__.py`; terminal ANSI style names are
defined in `packages/interfaces/src/interfaces/terminal/__init__.py`; Textual CSS consumes
the same palette through `packages/interfaces/src/interfaces/tui/style.py`.

## Core Rules

- Default theme is `dark`; valid presets are `dark` and `light`.
- `interfaces.palette.Theme` is the canonical CLI color contract.
- Concrete colors must stay centralized in `interfaces.palette`.
- TUI and terminal code should use semantic roles such as `text_primary`,
  `text_secondary`, and `action_primary_bg`; do not add ad hoc hex values in render code.
- Labels are uppercase; values are lowercase.
- Preserve literal user, model, file, and path values when correctness requires it. For
  example, status currently preserves a model name such as `Test-MODEL`.
- Do not use color alone to communicate state. Pair state with text such as `STATE
  current`, `api missing`, `error:`, evidence IDs, or material enablement.
- The dark theme is intentionally transparent for root/background surfaces so the terminal
  owns the base canvas.
- The CLI has no radius, shadows, or web line-height. Use terminal cells, padding columns,
  and Textual heights instead.

## CLI Theme Tokens

The TOML block below is the agent-readable contract. It must match
`interfaces.palette.Theme` exactly after normalizing hex case.

```toml
[cli_theme_tokens.bg_app]
dark = "transparent"
light = "#fafafa"
intent = "Root app and screen background. Dark mode lets the terminal background show through."

[cli_theme_tokens.bg_surface]
dark = "transparent"
light = "#ffffff"
intent = "Primary shell, transcript, lists, status, footer, and side-panel surface."

[cli_theme_tokens.bg_raised]
dark = "#161616"
light = "#f2f2f2"
intent = "Raised user/composer panels and user transcript blocks."

[cli_theme_tokens.text_primary]
dark = "#cfcfcf"
light = "#000000"
intent = "Main transcript text, composer input, selected content text, and primary readable text."

[cli_theme_tokens.text_secondary]
dark = "#8f8f8f"
light = "#404040"
intent = "Chrome labels, shortcuts, metadata labels, and quiet selected labels."

[cli_theme_tokens.text_muted]
dark = "#6f6f6f"
light = "#666666"
intent = "Values, footer body text, disabled items, activity, notice, and secondary detail."

[cli_theme_tokens.text_inverse]
dark = "#000000"
light = "#ffffff"
intent = "Inverse text role for solid action fills."

[cli_theme_tokens.border_subtle]
dark = "#3d3d3d"
light = "#d9d9d9"
intent = "Reserved subtle border role; current TUI avoids visible borders."

[cli_theme_tokens.brand_primary]
dark = "#ffffff"
light = "#000000"
intent = "Heph title, brand emphasis, selected quiet highlights, and focused list labels."

[cli_theme_tokens.action_primary_bg]
dark = "#d06a4a"
light = "#0f7a3a"
intent = "Solid selection/action fill for generic OptionList and accent/warning ANSI styles."

[cli_theme_tokens.action_primary_text]
dark = "#000000"
light = "#ffffff"
intent = "Text on action_primary_bg."

[cli_theme_tokens.status_success_text]
dark = "#57c785"
light = "#006b32"
intent = "Success messages and successful terminal output."

[cli_theme_tokens.status_error_text]
dark = "#ff6b5a"
light = "#b00020"
intent = "Error messages, auth/config warnings, and hidden armory errors."
```

## Terminal ANSI Roles

Terminal command output uses `_StyleToken` values from `interfaces.terminal`.

- `STYLE_PROMPT`
  - semantic role: prompt
  - color source: `text_primary`
  - weight: bold
  - current use: Menu titles, section labels, current state badges.
- `STYLE_BRAND`
  - semantic role: brand
  - color source: `brand_primary`
  - weight: bold
  - current use: Brand emphasis.
- `STYLE_ACCENT`
  - semantic role: accent
  - color source: `action_primary_bg`
  - weight: bold
  - current use: Accent and warning emphasis.
- `STYLE_WARNING`
  - semantic role: warning
  - color source: `action_primary_bg`
  - weight: bold
  - current use: Warning-style terminal text.
- `STYLE_SUCCESS`
  - semantic role: success
  - color source: `status_success_text`
  - weight: bold
  - current use: `print_success()` and success output.
- `STYLE_ERROR`
  - semantic role: error
  - color source: `status_error_text`
  - weight: bold
  - current use: `print_error()` and `error:` prefixes.
- `STYLE_CHROME_LABEL`
  - semantic role: chrome label
  - color source: `text_secondary`
  - weight: regular
  - current use: Labels and metadata labels.
- `STYLE_SHORTCUT`
  - semantic role: shortcut
  - color source: `text_secondary`
  - weight: regular
  - current use: Shortcut labels.
- `STYLE_METADATA`
  - semantic role: metadata
  - color source: `text_secondary`
  - weight: regular
  - current use: Metadata labels.
- `STYLE_CHROME_DETAIL`
  - semantic role: chrome detail
  - color source: `text_muted`
  - weight: regular
  - current use: Secondary details.
- `STYLE_DIM`
  - semantic role: dim
  - color source: `text_muted`
  - weight: dim
  - current use: `info:`, notices, inactive details, cancel rows.
- `STYLE_EMPHASIS`
  - semantic role: emphasis
  - color source: `text_primary`
  - weight: bold
  - current use: Inline emphasis.
- `STYLE_ASSISTANT`
  - semantic role: assistant
  - color source: `text_primary`
  - weight: bold
  - current use: Assistant role emphasis.
- `STYLE_EMBER`
  - semantic role: ember
  - color source: `brand_primary`
  - weight: bold
  - current use: Brand-adjacent emphasis.

`print_error(msg)` renders `error:` in `STYLE_ERROR`, then the message. `print_info(msg)`
renders `info:` in `STYLE_DIM`, then the message. `print_success(msg)` renders the full
message in `STYLE_SUCCESS`.

## Label And Value System

The CLI treats short metadata as a two-part grammar:

```text
LABEL value
```

The label is always uppercase. Menu metadata values are lowercased with `casefold()`.
Plain label/value lines keep the supplied value because paths, model IDs, commands, and
evidence IDs can be case-sensitive. This is why the shared rule is:

```text
Labels are uppercase; values are lowercase when the value is UI-owned metadata.
Values that are user-owned identifiers, provider IDs, paths, or evidence IDs are preserved.
```

Canonical helpers:

- `interfaces.terminal.menu_label_value(label, value)` uppercases labels and casefolds values.
- `interfaces.tui.display_text.menu_label_value(label, value)` uppercases labels and casefolds menu values.
- `interfaces.tui.display_text.label_value_line(label, value)` uppercases labels and preserves value text.
- `interfaces.tui.status.status_lines()` renders status fields as uppercase labels.

Examples:

```text
ARMORY none
MODEL gpt-5.5
REASONING low
SCOPE 3/8
EVIDENCE none yet
STATE current
```

## Textual Layout Contract

The TUI is a full-height vertical shell with a fixed side panel:

- `#main-layout`: horizontal root.
- `#shell`: vertical main column.
- `#status`: one terminal cell high.
- `#transcript-spacer`: one terminal cell high unless an inline browser is active.
- `#transcript`: flexible transcript log.
- `#thinking-indicator`: one cell, visible only while active.
- `#composer-frame`: raised user block, 3 to 8 cells high; compact mode is 1 cell.
- `#completion-stack`: suggestions, position, and footer, up to 9 cells.
- `#info-panel`: fixed 38-column side panel.

Use terminal cells and content width rules rather than web spacing units. The current
important dimensions are:

Each entry uses `value` and `source` fields so this remains readable in narrow editors:

- `info_panel_width`
  - value: 38 columns
  - source: `#info-panel` CSS and display text truncation
- `composer_min_height`
  - value: 3 cells
  - source: `#composer-frame`
- `composer_max_height`
  - value: 8 cells
  - source: `#composer-frame`
- `composer_compact_height`
  - value: 1 cell
  - source: `#composer-frame.compact`
- `completion_stack_height`
  - value: 9 cells
  - source: `#completion-stack`
- `suggestions_max_height`
  - value: 7 cells
  - source: `#suggestions`
- `model_picker_max_height`
  - value: 20 cells
  - source: `#suggestions.model-picker`
- `transcript_horizontal_padding`
  - value: 0 cells
  - source: `interfaces.tui.transcript`
- `reply_horizontal_padding`
  - value: 2 cells
  - source: assistant replies
- `user_horizontal_padding`
  - value: 2 cells
  - source: user transcript blocks
- `user_vertical_padding`
  - value: 1 cell
  - source: user transcript blocks
- `material_two_column_min_width`
  - value: 72 columns
  - source: materials browser

## TUI Component Tokens

Component entries use the same `background`, `text`, and `notes` fields everywhere.
This makes the section easier to scan by eye while keeping token names easy for agents
and scripts to extract.

### App And Screen

- `App`
  - background: `bg_app`
  - text: `text_primary`
  - notes: Root Textual app.
- `Screen`
  - background: `bg_app`
  - text: `text_primary`
  - notes: Vertical layout with `base` and `suggestions` layers.
- `Screen .screen--selection`
  - background: `bg_app`
  - text: reverse video
  - notes: Selection uses reverse video, not accent fill.
- `Horizontal`, `Vertical`, `Static`, `RichLog`
  - background: `bg_surface`
  - text: inherited
  - notes: Transparent tint prevents opaque stripes.

### Shell And Transcript

- `#main-layout`
  - background: `bg_app`
  - text: `text_primary`
  - notes: Horizontal root layout.
- `#shell`
  - background: `bg_surface`
  - text: `text_primary`
  - notes: Main vertical column.
- `#transcript`
  - background: `bg_surface`
  - text: `text_primary`
  - notes: Wraps markdown, hides scrollbars.
- Assistant markdown
  - background: inherited
  - text: `text_primary`
  - notes: Markdown is rendered through Rich/Textual.
- Evidence citations
  - background: inherited
  - text: `text_muted`
  - notes: Citation badges and source footers are dimmed.
- Startup card
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Uses label/value guidance lines.
- Notice/activity
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Activity is clipped to one visible row per event line.
- User transcript block
  - background: `bg_raised`
  - text: `text_primary`
  - notes: Bold user text with 2-column horizontal padding and 1-row vertical padding.

### Status

- `#status`
  - background: `bg_surface`
  - text: `text_muted`
  - notes: One-cell top status line.
- Status title
  - background: `bg_surface`
  - text: `brand_primary`
  - notes: Bold; normally `Heph`, changes to active menu title.
- Status labels
  - background: `bg_surface`
  - text: `text_secondary`
  - notes: `ARMORY`, `MODEL`, `REASONING`, `TOKENS`, `COST`.
- Status values
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Preserve provider/model casing when needed.

### Composer

- `#composer-frame`
  - background: `bg_raised`
  - text: `text_primary`
  - notes: Raised input block.
- `#composer-prompt`
  - background: `bg_raised`
  - text: `text_primary`
  - notes: Fixed 2-column prompt cell, currently `->` in docs and `→` in app.
- `#composer`
  - background: `bg_raised`
  - text: `text_primary`
  - notes: Input widget.
- Placeholder/suggestion
  - background: `bg_raised`
  - text: `text_secondary`
  - notes: Placeholder: `Ask a cited question about your materials...`.
- Cursor
  - background: `text_primary`
  - text: `bg_raised`
  - notes: Cursor background is primary text color.
- Input selection
  - background: `bg_surface`
  - text: reverse video
  - notes: Selection uses reverse video.

### Suggestions And Inline Menus

- Default `OptionList` row
  - background: `bg_surface`
  - text: `text_primary`
  - notes: Regular list option.
- Default `OptionList` highlighted
  - background: `action_primary_bg`
  - text: `action_primary_text`
  - notes: Solid selection for generic lists.
- Completion/suggestion highlighted
  - background: `bg_surface`
  - text: `brand_primary`
  - notes: Quiet selection, not bold.
- Inline-menu selected prefix
  - background: `bg_surface`
  - text: `brand_primary`
  - notes: Prefix is `->` in docs and `→` in app.
- Inline-menu selected label
  - background: `bg_surface`
  - text: `brand_primary`
  - notes: No accent stripe.
- Inline-menu unselected label
  - background: `bg_surface`
  - text: `text_secondary`
  - notes: Quiet scan color.
- Inline-menu description
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Four-column gap after label.
- Completion position
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Renders `(n/total)` when visible.

### Footer

- `#footer-hints`
  - background: `bg_surface`
  - text: `text_muted`
  - notes: One-cell footer hint line.
- Footer labels
  - background: `bg_surface`
  - text: `text_secondary`
  - notes: Uppercase action labels.
- Footer keys
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Key names stay lowercase.
- `api missing`
  - background: `bg_surface`
  - text: `status_error_text`
  - notes: Error state paired with text.

### Info Panel

- `#info-panel`
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Fixed 38-column side panel.
- Panel labels
  - background: `bg_surface`
  - text: `text_secondary`
  - notes: Uppercase labels such as `SCOPE`, `EVIDENCE`, `MODEL`.
- Active material token
  - background: `bg_surface`
  - text: `text_primary`
  - notes: Material entries render as `@name`.
- Disabled material token
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Disabled materials lose primary emphasis.
- Hidden counts
  - background: `bg_surface`
  - text: `text_muted`
  - notes: `MORE +n`.
- Focused message title
  - background: `bg_surface`
  - text: `text_primary`
  - notes: Bold title.
- Focused message labels
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Dim uppercase labels.

### Armory Browser

- `#armory-inline`
  - background: `bg_surface`
  - text: `text_primary`
  - notes: Replaces transcript while active.
- Armory header/hints
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Header starts with `ITEMS n`.
- Armory selected prefix
  - background: `bg_surface`
  - text: `brand_primary`
  - notes: Quiet selected row.
- Armory selected label
  - background: `bg_surface`
  - text: `brand_primary`
  - notes: No accent fill.
- Armory unselected label
  - background: `bg_surface`
  - text: `text_primary`
  - notes: Regular row.
- Armory section label
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Dim section heading.
- Armory description
  - background: `bg_surface`
  - text: `text_muted`
  - notes: `FILES n`, `STATE empty`, etc.
- Armory error
  - background: `bg_surface`
  - text: `status_error_text`
  - notes: One-cell hidden error row.

### Materials Browser

- `#materials-inline`
  - background: `bg_surface`
  - text: `text_primary`
  - notes: Replaces transcript while active.
- Materials header/gaps
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Header starts with `SCOPE materials`.
- Materials highlighted row
  - background: `bg_surface`
  - text: `brand_primary`
  - notes: Neutral selected color for enabled and disabled rows.
- Enabled material
  - background: `bg_surface`
  - text: `text_primary`
  - notes: `@` marker muted when unselected.
- Disabled material
  - background: `bg_surface`
  - text: `text_muted`
  - notes: No red/error state.
- Materials footer
  - background: `bg_surface`
  - text: `text_muted`
  - notes: Hidden in CSS for the inline list footer; footer hints carry actions.

## Voice

Heph should speak like a private, evidence-first study and work companion. The copy already
in the CLI is the source:

- Practical and direct: `Use /login, then /models.`
- Local-first: `Armories are saved locally in ~/.armories/`.
- Grounded: `No evidence was retrieved for the last turn.`
- Actionable: `Add files to: ...`, `Then start working with your documents: heph <name>`.
- Calm under error: `No model configured. Use /models to select one.`
- Specific, not ornamental: `Index refreshed: 3 sources, 42 chunks`.
- Learning-oriented where relevant: `Type your answer, then rate your recall.`

Do not use marketing copy in the terminal. Prefer short sentences that name the state and
the next available action. Use `error:` and `info:` prefixes for terminal command output.
Avoid `successfully`; use the concrete result instead.

## Agent Usage Guide

When changing CLI/TUI design:

1. Read `interfaces.palette.Theme` before changing any color.
2. Update `cli-design.md` in the same change as any palette or semantic styling change.
3. Use semantic roles in code. Do not add a hex value to TUI render code.
4. Keep `labels uppercase, values lowercase` unless the value is a user-owned identifier,
   model name, path, command, or evidence ID that must preserve case.
5. Run `uv run python -m scripts.check_design_docs`.
6. Run the focused TUI/palette tests touched by the change.

If `cli-design.md` and the running app disagree, the code and tests are the immediate
source of truth. Fix the drift by updating either the implementation or this file so the
documented semantic role and the rendered role match again.
