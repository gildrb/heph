---
version: "0.0.49"
name: "Heph"
description: "Website and brand design specification for the Heph local document harness."
source_of_truth:
  - "cli-design.md"
  - "packages/interfaces/src/interfaces/palette/__init__.py"
  - "README.md"
default_theme: "dark"
recommended_stack:
  framework: "Next.js"
  components: "shadcn/ui new-york"
  primitives: "Radix UI"
  fonts:
    - "Geist Sans"
    - "Geist Mono"
---

# Heph Design

Heph is the public-facing expression of a local document harness for accurate, cited
answers. The website and brand should feel thematically aligned with the CLI: private,
precise, quiet, local-first, evidence-forward, and easy to scan.

This file is for browser and brand surfaces. The CLI is specified separately in
`cli-design.md`. Keep the two systems semantically aligned, but do not copy terminal-only
rules into the web. The web needs responsive layout, radius, focus rings, form states, and
browser typography; the CLI needs terminal cells and Textual selectors.

## Core Rules

- The default brand theme is dark.
- The website should use shadcn/ui `new-york` composition for product surfaces.
- Use Geist Sans for interface, headings, and prose.
- Use Geist Mono for code, command examples, metrics, paths, evidence IDs, and timestamps.
- Labels are uppercase; values are lowercase.
- Preserve real identifiers exactly when changing case would reduce correctness.
- Use color sparingly. Most hierarchy comes from neutral text roles, whitespace, and borders.
- Accent color is for primary action, warning emphasis, and selected action affordances.
- Do not use gradients, glassmorphism, or decorative color fields as brand shortcuts.
- Use tokens, not ad hoc Tailwind palette classes, for foundational surfaces.

## Source Mapping

The web system inherits meaning from CLI roles, then adapts them to browser constraints.

| web token | value | CLI source | use |
|---|---|---|---|
| `colors.primary` | #ffffff | `dark.brand_primary` | Brand text and highest-emphasis foreground on dark. |
| `colors.secondary` | #8f8f8f | `dark.text_secondary` | Labels, quiet icons, and metadata labels. |
| `colors.tertiary` | #6f6f6f | `dark.text_muted` | Muted values, helper copy, disabled affordances. |
| `colors.accent` | #d06a4a | `dark.action_primary_bg` | Primary action, warning accent, focused command action. |
| `colors.accent-foreground` | #000000 | `dark.action_primary_text` | Text on accent. |
| `colors.background-100` | #000000 | `dark.text_inverse` | Opaque web root replacing CLI transparent terminal background. |
| `colors.background-200` | #161616 | `dark.bg_raised` | Cards, raised panels, user-message-like surfaces. |
| `colors.background-300` | transparent | `dark.bg_surface` | Transparent overlays inside controlled shells. |
| `colors.border` | #3d3d3d | `dark.border_subtle` | Subtle borders and separators. |
| `colors.success` | #57c785 | `dark.status_success_text` | Success text and badges. |
| `colors.error` | #ff6b5a | `dark.status_error_text` | Error text, destructive warnings, validation errors. |
| `colors.light.background-100` | #fafafa | `light.bg_app` | Light root background. |
| `colors.light.background-200` | #ffffff | `light.bg_surface` | Light cards and primary surfaces. |
| `colors.light.background-300` | #f2f2f2 | `light.bg_raised` | Light raised panels. |
| `colors.light.primary` | #000000 | `light.brand_primary` | Light highest-emphasis foreground. |
| `colors.light.secondary` | #404040 | `light.text_secondary` | Light labels and metadata. |
| `colors.light.tertiary` | #666666 | `light.text_muted` | Light muted values and helper copy. |
| `colors.light.accent` | #0f7a3a | `light.action_primary_bg` | Light primary action. |
| `colors.light.accent-foreground` | #ffffff | `light.action_primary_text` | Light action text. |
| `colors.light.border` | #d9d9d9 | `light.border_subtle` | Light subtle borders. |
| `colors.light.success` | #006b32 | `light.status_success_text` | Light success text. |
| `colors.light.error` | #b00020 | `light.status_error_text` | Light error text. |

The only web-only interpretation above is `colors.background-100` for dark mode: the CLI
uses `transparent` because the terminal owns the canvas. A website needs an opaque root, so
use the existing `#000000` value already present in the CLI palette as inverse/action text.

## shadcn Token Mapping

Use CSS variables so future changes can flow from this document into implementation.

```css
@theme inline {
  --font-sans: "Geist", "Geist Fallback", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "Geist Mono", "Geist Mono Fallback", ui-monospace, monospace;

  --color-background: #000000;
  --color-foreground: #ffffff;
  --color-card: #161616;
  --color-card-foreground: #cfcfcf;
  --color-popover: #161616;
  --color-popover-foreground: #cfcfcf;
  --color-primary: #ffffff;
  --color-primary-foreground: #000000;
  --color-secondary: #161616;
  --color-secondary-foreground: #cfcfcf;
  --color-muted: #161616;
  --color-muted-foreground: #6f6f6f;
  --color-accent: #d06a4a;
  --color-accent-foreground: #000000;
  --color-destructive: #ff6b5a;
  --color-border: #3d3d3d;
  --color-input: #3d3d3d;
  --color-ring: #d06a4a;

  --radius: 0.375rem;
  --radius-xs: 0.1875rem;
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
}
```

Use the `dark` class by default. A light theme may redefine the same names from the light
tokens above.

## Typography

The type system has three roles, using two Geist families:

| role | family | weights | use |
|---|---|---|---|
| `font.display` | Geist Sans | 600 | Product name, major headings, high-level page titles. |
| `font.body` | Geist Sans | 400, 500, 600 | Interface labels, prose, controls, docs, tables. |
| `font.mono` | Geist Mono | 400, 500 | Commands, code, paths, IDs, metrics, timestamps. |

Letter spacing is `0` for every token. Do not use negative letter spacing.

| token | family | size | weight | line height | letter spacing | use |
|---|---|---:|---:|---:|---:|---|
| `typography.heading-72` | Geist Sans | 72px | 600 | 72px | 0 | Rare hero display. |
| `typography.heading-64` | Geist Sans | 64px | 600 | 64px | 0 | Large launch page title. |
| `typography.heading-56` | Geist Sans | 56px | 600 | 64px | 0 | Product overview title. |
| `typography.heading-48` | Geist Sans | 48px | 600 | 56px | 0 | First-viewport heading. |
| `typography.heading-40` | Geist Sans | 40px | 600 | 48px | 0 | Section opener. |
| `typography.heading-32` | Geist Sans | 32px | 600 | 40px | 0 | Major section heading. |
| `typography.heading-24` | Geist Sans | 24px | 600 | 32px | 0 | Card and detail page heading. |
| `typography.heading-20` | Geist Sans | 20px | 600 | 28px | 0 | Compact panel heading. |
| `typography.heading-16` | Geist Sans | 16px | 600 | 24px | 0 | Dense section title. |
| `typography.label-16` | Geist Sans | 16px | 500 | 20px | 0 | Prominent labels and large controls. |
| `typography.label-14` | Geist Sans | 14px | 500 | 20px | 0 | Default labels, tabs, buttons. |
| `typography.label-12` | Geist Sans | 12px | 500 | 16px | 0 | Metadata labels and badges. |
| `typography.copy-20` | Geist Sans | 20px | 400 | 32px | 0 | Intro copy. |
| `typography.copy-16` | Geist Sans | 16px | 400 | 24px | 0 | Default prose. |
| `typography.copy-14` | Geist Sans | 14px | 400 | 20px | 0 | Product UI copy. |
| `typography.copy-13` | Geist Sans | 13px | 400 | 18px | 0 | Dense helper text. |
| `typography.mono-14` | Geist Mono | 14px | 400 | 20px | 0 | Commands, paths, evidence IDs. |
| `typography.mono-13` | Geist Mono | 13px | 400 | 18px | 0 | Dense data and table cells. |
| `typography.mono-12` | Geist Mono | 12px | 400 | 16px | 0 | Badges, timestamps, tiny metrics. |

## Spacing And Layout

Use a 4px spacing base.

| token | value |
|---|---:|
| `spacing.1` | 4px |
| `spacing.2` | 8px |
| `spacing.3` | 12px |
| `spacing.4` | 16px |
| `spacing.6` | 24px |
| `spacing.8` | 32px |
| `spacing.10` | 40px |
| `spacing.16` | 64px |
| `spacing.24` | 96px |

Use 8px inside compact groups, 16px between related groups, and 32-40px between major
sections. Product app surfaces should be dense and scannable; marketing pages can breathe
more, but still avoid oversized empty decoration.

Recommended breakpoints:

| token | value |
|---|---:|
| `breakpoint.sm` | 401px |
| `breakpoint.md` | 601px |
| `breakpoint.lg` | 961px |
| `breakpoint.xl` | 1200px |
| `breakpoint.2xl` | 1400px |

## Radius

The CLI has no roundedness. The website needs a restrained radius system:

| token | value | use |
|---|---:|---|
| `radius.xs` | 3px | Fine separators, compact inner controls. |
| `radius.sm` | 6px | Buttons, inputs, badges. |
| `radius.md` | 8px | Cards and repeated items. |
| `radius.lg` | 8px | Dialogs and sheets unless the component needs more. |
| `radius.xl` | 12px | Large modal surfaces only. |
| `radius.full` | 9999px | Pills, avatars, circular controls. |

Cards should stay at 8px or less.

## Elevation

Hierarchy comes from surfaces and borders first. Use shadows only when a component floats
over content.

| token | value | use |
|---|---|---|
| `shadow.card` | `0 2px 2px rgb(0 0 0 / 0.18)` | Raised cards on dark backgrounds. |
| `shadow.popover` | `0 1px 1px rgb(0 0 0 / 0.18), 0 8px 16px -8px rgb(0 0 0 / 0.42)` | Popovers, menus, tooltips. |
| `shadow.dialog` | `0 1px 1px rgb(0 0 0 / 0.18), 0 16px 32px -12px rgb(0 0 0 / 0.55)` | Dialogs and sheets. |

## Motion

Most interactions should feel instant. Use `0ms` when no motion is needed. If motion
clarifies state, use:

| token | value | use |
|---|---:|---|
| `motion.fast` | 150ms | Hover and small state transitions. |
| `motion.base` | 200ms | Popovers, menus, disclosure. |
| `motion.slow` | 300ms | Dialog and sheet entrance. |
| `motion.ease` | `cubic-bezier(0.175, 0.885, 0.32, 1.1)` | Short physical reveal. |

Honor `prefers-reduced-motion`.

## Components

### Button

| variant | background | text | border | typography | radius | height |
|---|---|---|---|---|---|---:|
| `button.primary` | `colors.accent` | `colors.accent-foreground` | none | `typography.label-14` | `radius.sm` | 40px |
| `button.secondary` | `colors.background-200` | `colors.primary` | `colors.border` | `typography.label-14` | `radius.sm` | 40px |
| `button.tertiary` | transparent | `colors.primary` | transparent | `typography.label-14` | `radius.sm` | 40px |
| `button.error` | transparent | `colors.error` | `colors.error` | `typography.label-14` | `radius.sm` | 40px |
| `button.small` | variant-defined | variant-defined | variant-defined | `typography.label-12` | `radius.sm` | 32px |
| `button.large` | variant-defined | variant-defined | variant-defined | `typography.label-16` | `radius.sm` | 48px |

Use icons in buttons when the action has a familiar icon. Keep Lucide icons at 16px or
20px.

### Input And Textarea

| part | color |
|---|---|
| background | `colors.background-200` |
| text | `colors.primary` |
| placeholder | `colors.tertiary` |
| border | `colors.border` |
| focus ring | `colors.accent` |
| error text | `colors.error` |

Use `typography.copy-14` for entered text and `typography.label-12` for labels. Labels are
uppercase; values are lowercase when UI-owned.

### Card

Cards are for repeated items, settings groups, detail panels, and tool surfaces. Do not put
cards inside cards.

| part | token |
|---|---|
| background | `colors.background-200` |
| foreground | `colors.primary` |
| secondary text | `colors.secondary` |
| muted values | `colors.tertiary` |
| border | `colors.border` |
| radius | `radius.md` |
| padding | `spacing.4` compact, `spacing.6` comfortable |

### Badge

| variant | background | text | border |
|---|---|---|---|
| `badge.neutral` | `colors.background-200` | `colors.secondary` | `colors.border` |
| `badge.success` | transparent | `colors.success` | `colors.success` |
| `badge.error` | transparent | `colors.error` | `colors.error` |
| `badge.accent` | transparent | `colors.accent` | `colors.accent` |

Badges should carry text, not color alone.

### Command Palette

The command palette is the web cousin of the CLI command and inline menu surfaces.

| part | token |
|---|---|
| dialog background | `colors.background-200` |
| input text | `colors.primary` |
| placeholder | `colors.tertiary` |
| selected row background | transparent or `colors.background-200` |
| selected row text | `colors.primary` |
| command label | uppercase `colors.secondary` |
| command value | lowercase `colors.tertiary` |

Use shadcn `Command` inside `Dialog`.

### Table

Tables should feel like dense evidence and material indexes.

| part | token |
|---|---|
| header labels | uppercase `colors.secondary`, `typography.label-12` |
| values | lowercase where UI-owned, `colors.primary`, `typography.copy-14` |
| metadata | `colors.tertiary`, `typography.mono-13` |
| row border | `colors.border` |
| hover | `colors.background-200` |

### Tabs

| part | token |
|---|---|
| active label | `colors.primary` |
| inactive label | `colors.secondary` |
| active indicator | `colors.accent` |
| panel background | transparent or `colors.background-100` |

### Dialog And Sheet

Use `Dialog` for reversible flows and `AlertDialog` for destructive confirmation.

| part | token |
|---|---|
| background | `colors.background-200` |
| title | `colors.primary`, `typography.heading-20` |
| description | `colors.tertiary`, `typography.copy-14` |
| border | `colors.border` |
| radius | `radius.lg` |
| shadow | `shadow.dialog` |

### Alert

| variant | border | title | body |
|---|---|---|---|
| `alert.info` | `colors.border` | `colors.primary` | `colors.tertiary` |
| `alert.success` | `colors.success` | `colors.success` | `colors.tertiary` |
| `alert.error` | `colors.error` | `colors.error` | `colors.tertiary` |

### Evidence Panel

The evidence panel is a first-class web component because citations are core to Heph.

| part | token |
|---|---|
| panel background | `colors.background-200` |
| evidence ID | `colors.primary`, `typography.mono-13` |
| source path | `colors.tertiary`, `typography.mono-13` |
| label | uppercase `colors.secondary`, `typography.label-12` |
| excerpt | `colors.primary`, `typography.copy-14` |
| missing/unverified state | `colors.error` plus text |

### Material Item

| state | label | metadata | marker |
|---|---|---|---|
| active | `colors.primary` | `colors.tertiary` | `colors.tertiary` |
| disabled | `colors.tertiary` | `colors.tertiary` | `colors.tertiary` |
| selected | `colors.primary` | `colors.secondary` | `colors.primary` |

Render material names with `@name` on product surfaces to match the CLI.

## Voice

Heph copy should sound practical, private, and verification-first:

- Say what is true, then what the user can do next.
- Prefer concrete nouns: armory, materials, evidence, citations, model, memory.
- Avoid hype, filler, and vague success language.
- Do not say `successfully`; name the result.
- Errors should explain what happened and the next action.
- Empty states should point to the first meaningful step.
- Keep provider-specific copy optional unless the flow requires it.

Examples:

```text
No materials yet. Add PDFs, Markdown, notes, or text files to start.
No evidence was retrieved for the last turn.
Model missing. Use /login, then choose a model.
Armory memory stays local to this folder.
```

## Agent Usage Guide

When using this design in a web implementation:

1. Read `cli-design.md` first for theme semantics.
2. Use this file for browser-only decisions: typography, radius, layout, shadcn
   composition, forms, focus, and responsive behavior.
3. Implement colors as CSS variables with the token names in this file.
4. Keep labels uppercase and UI-owned values lowercase.
5. Use shadcn primitives instead of raw controls where a primitive exists.
6. Do not copy terminal dimensions such as `38 columns` into responsive browser layout.
7. If a web component represents an existing CLI concept, map its colors through the
   component tables above.
8. After changing palette semantics, update both `cli-design.md` and `design.md`, then run
   `uv run python -m scripts.check_design_docs`.
