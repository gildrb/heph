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
Website layout, responsive spacing, radius, and shadcn component composition belong in
`design.md`.

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

This table must match `interfaces.palette.Theme` exactly after normalizing hex case.

| role | dark | light | intent |
|---|---|---|---|
| bg_app | transparent | #fafafa | Root app and screen background. Dark mode lets the terminal background show through. |
| bg_surface | transparent | #ffffff | Primary shell, transcript, lists, status, footer, and side-panel surface. |
| bg_raised | #161616 | #f2f2f2 | Raised user/composer panels and user transcript blocks. |
| text_primary | #cfcfcf | #000000 | Main transcript text, composer input, selected content text, and primary readable text. |
| text_secondary | #8f8f8f | #404040 | Chrome labels, shortcuts, metadata labels, and quiet selected labels. |
| text_muted | #6f6f6f | #666666 | Values, footer body text, disabled items, activity, notice, and secondary detail. |
| text_inverse | #000000 | #ffffff | Inverse text role for solid action fills. |
| border_subtle | #3d3d3d | #d9d9d9 | Reserved subtle border role; current TUI avoids visible borders. |
| brand_primary | #ffffff | #000000 | Heph title, brand emphasis, selected quiet highlights, and focused list labels. |
| action_primary_bg | #d06a4a | #0f7a3a | Solid selection/action fill for generic `OptionList` and accent/warning ANSI styles. |
| action_primary_text | #000000 | #ffffff | Text on `action_primary_bg`. |
| status_success_text | #57c785 | #006b32 | Success messages and successful terminal output. |
| status_error_text | #ff6b5a | #b00020 | Error messages, auth/config warnings, and hidden armory errors. |

## Terminal ANSI Roles

Terminal command output uses `_StyleToken` values from `interfaces.terminal`.

| style token | semantic role | color source | weight | current use |
|---|---|---|---|---|
| `STYLE_PROMPT` | prompt | `text_primary` | bold | Menu titles, section labels, current state badges. |
| `STYLE_BRAND` | brand | `brand_primary` | bold | Brand emphasis. |
| `STYLE_ACCENT` | accent | `action_primary_bg` | bold | Accent and warning emphasis. |
| `STYLE_WARNING` | warning | `action_primary_bg` | bold | Warning-style terminal text. |
| `STYLE_SUCCESS` | success | `status_success_text` | bold | `print_success()` and success output. |
| `STYLE_ERROR` | error | `status_error_text` | bold | `print_error()` and `error:` prefixes. |
| `STYLE_CHROME_LABEL` | chrome label | `text_secondary` | regular | Labels and metadata labels. |
| `STYLE_SHORTCUT` | shortcut | `text_secondary` | regular | Shortcut labels. |
| `STYLE_METADATA` | metadata | `text_secondary` | regular | Metadata labels. |
| `STYLE_CHROME_DETAIL` | chrome detail | `text_muted` | regular | Secondary details. |
| `STYLE_DIM` | dim | `text_muted` | dim | `info:`, notices, inactive details, cancel rows. |
| `STYLE_EMPHASIS` | emphasis | `text_primary` | bold | Inline emphasis. |
| `STYLE_ASSISTANT` | assistant | `text_primary` | bold | Assistant role emphasis. |
| `STYLE_EMBER` | ember | `brand_primary` | bold | Brand-adjacent emphasis. |

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

| token | value | source |
|---|---:|---|
| `info_panel_width` | 38 columns | `#info-panel` CSS and display text truncation |
| `composer_min_height` | 3 cells | `#composer-frame` |
| `composer_max_height` | 8 cells | `#composer-frame` |
| `composer_compact_height` | 1 cell | `#composer-frame.compact` |
| `completion_stack_height` | 9 cells | `#completion-stack` |
| `suggestions_max_height` | 7 cells | `#suggestions` |
| `model_picker_max_height` | 20 cells | `#suggestions.model-picker` |
| `transcript_horizontal_padding` | 0 cells | `interfaces.tui.transcript` |
| `reply_horizontal_padding` | 2 cells | assistant replies |
| `user_horizontal_padding` | 2 cells | user transcript blocks |
| `user_vertical_padding` | 1 cell | user transcript blocks |
| `material_two_column_min_width` | 72 columns | materials browser |

## TUI Component Tokens

### App And Screen

| component | background | text | notes |
|---|---|---|---|
| `App` | `bg_app` | `text_primary` | Root Textual app. |
| `Screen` | `bg_app` | `text_primary` | Vertical layout with `base` and `suggestions` layers. |
| `Screen .screen--selection` | `bg_app` | reverse video | Selection uses reverse video, not accent fill. |
| `Horizontal`, `Vertical`, `Static`, `RichLog` | `bg_surface` | inherited | Transparent tint prevents opaque stripes. |

### Shell And Transcript

| component | background | text | notes |
|---|---|---|---|
| `#main-layout` | `bg_app` | `text_primary` | Horizontal root layout. |
| `#shell` | `bg_surface` | `text_primary` | Main vertical column. |
| `#transcript` | `bg_surface` | `text_primary` | Wraps markdown, hides scrollbars. |
| Assistant markdown | inherited | `text_primary` | Markdown is rendered through Rich/Textual. |
| Evidence citations | inherited | `text_muted` | Citation badges and source footers are dimmed. |
| Startup card | `bg_surface` | `text_muted` | Uses label/value guidance lines. |
| Notice/activity | `bg_surface` | `text_muted` | Activity is clipped to one visible row per event line. |
| User transcript block | `bg_raised` | `text_primary` | Bold user text with 2-column horizontal padding and 1-row vertical padding. |

### Status

| component | background | text | notes |
|---|---|---|---|
| `#status` | `bg_surface` | `text_muted` | One-cell top status line. |
| Status title | `bg_surface` | `brand_primary` | Bold; normally `Heph`, changes to active menu title. |
| Status labels | `bg_surface` | `text_secondary` | `ARMORY`, `MODEL`, `REASONING`, `TOKENS`, `COST`. |
| Status values | `bg_surface` | `text_muted` | Preserve provider/model casing when needed. |

### Composer

| component | background | text | notes |
|---|---|---|---|
| `#composer-frame` | `bg_raised` | `text_primary` | Raised input block. |
| `#composer-prompt` | `bg_raised` | `text_primary` | Fixed 2-column prompt cell, currently `->` in docs and `→` in app. |
| `#composer` | `bg_raised` | `text_primary` | Input widget. |
| Placeholder/suggestion | `bg_raised` | `text_secondary` | Placeholder: `Ask a cited question about your materials...`. |
| Cursor | `text_primary` | `bg_raised` | Cursor background is primary text color. |
| Input selection | `bg_surface` | reverse video | Selection uses reverse video. |

### Suggestions And Inline Menus

| component | background | text | notes |
|---|---|---|---|
| Default `OptionList` row | `bg_surface` | `text_primary` | Regular list option. |
| Default `OptionList` highlighted | `action_primary_bg` | `action_primary_text` | Solid selection for generic lists. |
| Completion/suggestion highlighted | `bg_surface` | `brand_primary` | Quiet selection, not bold. |
| Inline-menu selected prefix | `bg_surface` | `brand_primary` | Prefix is `->` in docs and `→` in app. |
| Inline-menu selected label | `bg_surface` | `brand_primary` | No accent stripe. |
| Inline-menu unselected label | `bg_surface` | `text_secondary` | Quiet scan color. |
| Inline-menu description | `bg_surface` | `text_muted` | Four-column gap after label. |
| Completion position | `bg_surface` | `text_muted` | Renders `(n/total)` when visible. |

### Footer

| component | background | text | notes |
|---|---|---|---|
| `#footer-hints` | `bg_surface` | `text_muted` | One-cell footer hint line. |
| Footer labels | `bg_surface` | `text_secondary` | Uppercase action labels. |
| Footer keys | `bg_surface` | `text_muted` | Key names stay lowercase. |
| `api missing` | `bg_surface` | `status_error_text` | Error state paired with text. |

### Info Panel

| component | background | text | notes |
|---|---|---|---|
| `#info-panel` | `bg_surface` | `text_muted` | Fixed 38-column side panel. |
| Panel labels | `bg_surface` | `text_secondary` | Uppercase labels such as `SCOPE`, `EVIDENCE`, `MODEL`. |
| Active material token | `bg_surface` | `text_primary` | Material entries render as `@name`. |
| Disabled material token | `bg_surface` | `text_muted` | Disabled materials lose primary emphasis. |
| Hidden counts | `bg_surface` | `text_muted` | `MORE +n`. |
| Focused message title | `bg_surface` | `text_primary` | Bold title. |
| Focused message labels | `bg_surface` | `text_muted` | Dim uppercase labels. |

### Armory Browser

| component | background | text | notes |
|---|---|---|---|
| `#armory-inline` | `bg_surface` | `text_primary` | Replaces transcript while active. |
| Armory header/hints | `bg_surface` | `text_muted` | Header starts with `ITEMS n`. |
| Armory selected prefix | `bg_surface` | `brand_primary` | Quiet selected row. |
| Armory selected label | `bg_surface` | `brand_primary` | No accent fill. |
| Armory unselected label | `bg_surface` | `text_primary` | Regular row. |
| Armory section label | `bg_surface` | `text_muted` | Dim section heading. |
| Armory description | `bg_surface` | `text_muted` | `FILES n`, `STATE empty`, etc. |
| Armory error | `bg_surface` | `status_error_text` | One-cell hidden error row. |

### Materials Browser

| component | background | text | notes |
|---|---|---|---|
| `#materials-inline` | `bg_surface` | `text_primary` | Replaces transcript while active. |
| Materials header/gaps | `bg_surface` | `text_muted` | Header starts with `SCOPE materials`. |
| Materials highlighted row | `bg_surface` | `brand_primary` | Neutral selected color for enabled and disabled rows. |
| Enabled material | `bg_surface` | `text_primary` | `@` marker muted when unselected. |
| Disabled material | `bg_surface` | `text_muted` | No red/error state. |
| Materials footer | `bg_surface` | `text_muted` | Hidden in CSS for the inline list footer; footer hints carry actions. |

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
