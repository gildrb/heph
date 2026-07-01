---
version: "0.0.55"
name: "Heph"
description: "Website and brand design specification for the Heph local document harness."
source_of_truth:
  - "cli-design.md"
  - "packages/interfaces/src/interfaces/palette/__init__.py"
  - "packages/heph/src/heph/state/release.toml"
  - "scripts/check_design_docs.py"
  - "README.md"
reference_projects:
  - "/Users/gilrodrigues/Documents/GitHub/gildrb.com"
  - "https://github.com/raunofreiberg/interfaces"
default_theme: "dark"
web_stack:
  document: "HTML"
  styling: "CSS"
  behavior: "vanilla JavaScript or tiny TypeScript"
  build_step: "none unless the product explicitly needs one"
  frameworks: "none"
  component_libraries: "none"
  routing: "static files by default"
  fonts:
    - "Geist Sans"
    - "Geist Mono"
---

# Heph Design

Heph is the public-facing expression of a local document harness for accurate, cited
answers. The website and brand should feel thematically aligned with the CLI: private,
precise, quiet, local-first, evidence-forward, fast, and easy to scan.

This file is for browser and brand surfaces. The CLI is specified separately in
`cli-design.md`. Keep the two systems semantically aligned, but do not copy terminal-only
rules into the web. The web needs responsive layout, real HTML semantics, focus rings,
form states, images, and browser typography; the CLI needs terminal cells and Textual
selectors.

## Core Rules

- Build with plain HTML, CSS, and vanilla JavaScript or tiny TypeScript.
- Do not assume a framework, component library, router, CSS framework, preprocessor, or
  build system.
- Default brand theme is dark.
- Use Geist Sans for interface, headings, and prose.
- Use Geist Mono for code, command examples, metrics, paths, evidence IDs, and timestamps.
- Labels are uppercase; values are lowercase.
- Preserve real identifiers exactly when changing case would reduce correctness.
- Use color sparingly. Most hierarchy comes from neutral text roles, whitespace, borders,
  and strong content structure.
- Accent color is for primary action, warning emphasis, and selected action affordances.
- Do not use gradients, glassmorphism, decorative glow fields, or stock marketing layout
  shortcuts.
- Use CSS custom properties for foundational tokens.
- Keep the implementation static-file friendly by default.

## Web Development Contract

This TOML block is the agent-readable stack contract. It is intentionally plain and should
not be replaced by framework defaults unless the project direction changes explicitly.

```toml
[web_development]
document = "HTML"
styling = "CSS"
behavior = "vanilla JavaScript or tiny TypeScript"
framework = "none"
component_library = "none"
router = "static files by default"
bundler = "none by default"
deployment = "static files"

[web_development.reference]
primary = "gildrb.com"
local_repo = "/Users/gilrodrigues/Documents/GitHub/gildrb.com"
interface_guidelines = "https://github.com/raunofreiberg/interfaces"

[web_development.principles]
fast = true
accessible = true
framework_free = true
native_controls_first = true
decorative_effects = "avoid"
motion = "minimal"
```

Use the `gildrb.com` repo as the local reference for web development taste: quiet
monochrome CSS variables, static deployability, native HTML controls, explicit focus
states, real images, minimal JavaScript, fast asset loading, and restrained interaction.
Use the Rauno Freiberg interface guidelines as framework-independent detail guidance:
native forms, correct input types, no dead interactive areas, no layout shift on hover,
real `<img>` elements, appropriate focus states, fast or absent motion, and careful touch
behavior.

## Source Mapping

The web system inherits meaning from CLI roles, then adapts them to browser constraints.
The block below is intentionally structured rather than tabular so humans can read it in
plain editors and agents can still extract exact token names.

```toml
[web_colors."colors.primary"]
value = "#ffffff"
cli_source = "dark.brand_primary"
use = "Brand text and highest-emphasis foreground on dark."

[web_colors."colors.secondary"]
value = "#8f8f8f"
cli_source = "dark.text_secondary"
use = "Labels, quiet icons, and metadata labels."

[web_colors."colors.tertiary"]
value = "#6f6f6f"
cli_source = "dark.text_muted"
use = "Muted values, helper copy, disabled affordances."

[web_colors."colors.accent"]
value = "#d06a4a"
cli_source = "dark.action_primary_bg"
use = "Primary action, warning accent, focused command action."

[web_colors."colors.accent-foreground"]
value = "#000000"
cli_source = "dark.action_primary_text"
use = "Text on accent."

[web_colors."colors.background-100"]
value = "#000000"
cli_source = "dark.text_inverse"
use = "Opaque web root replacing CLI transparent terminal background."

[web_colors."colors.background-200"]
value = "#161616"
cli_source = "dark.bg_raised"
use = "Cards, raised panels, user-message-like surfaces."

[web_colors."colors.background-300"]
value = "transparent"
cli_source = "dark.bg_surface"
use = "Transparent overlays inside controlled shells."

[web_colors."colors.border"]
value = "#3d3d3d"
cli_source = "dark.border_subtle"
use = "Subtle borders and separators."

[web_colors."colors.success"]
value = "#57c785"
cli_source = "dark.status_success_text"
use = "Success text and badges."

[web_colors."colors.error"]
value = "#ff6b5a"
cli_source = "dark.status_error_text"
use = "Error text, destructive warnings, validation errors."

[web_colors."colors.light.background-100"]
value = "#fafafa"
cli_source = "light.bg_app"
use = "Light root background."

[web_colors."colors.light.background-200"]
value = "#ffffff"
cli_source = "light.bg_surface"
use = "Light cards and primary surfaces."

[web_colors."colors.light.background-300"]
value = "#f2f2f2"
cli_source = "light.bg_raised"
use = "Light raised panels."

[web_colors."colors.light.primary"]
value = "#000000"
cli_source = "light.brand_primary"
use = "Light highest-emphasis foreground."

[web_colors."colors.light.secondary"]
value = "#404040"
cli_source = "light.text_secondary"
use = "Light labels and metadata."

[web_colors."colors.light.tertiary"]
value = "#666666"
cli_source = "light.text_muted"
use = "Light muted values and helper copy."

[web_colors."colors.light.accent"]
value = "#0f7a3a"
cli_source = "light.action_primary_bg"
use = "Light primary action."

[web_colors."colors.light.accent-foreground"]
value = "#ffffff"
cli_source = "light.action_primary_text"
use = "Light action text."

[web_colors."colors.light.border"]
value = "#d9d9d9"
cli_source = "light.border_subtle"
use = "Light subtle borders."

[web_colors."colors.light.success"]
value = "#006b32"
cli_source = "light.status_success_text"
use = "Light success text."

[web_colors."colors.light.error"]
value = "#b00020"
cli_source = "light.status_error_text"
use = "Light error text."
```

The only web-only interpretation above is `colors.background-100` for dark mode: the CLI
uses `transparent` because the terminal owns the canvas. A website needs an opaque root, so
use the existing `#000000` value already present in the CLI palette as inverse/action text.

## CSS Token Contract

Use CSS custom properties so future changes can flow from this document into a static
HTML/CSS implementation without requiring a framework.

```css
:root {
  --font-sans: "Geist", "Geist Fallback", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "Geist Mono", "Geist Mono Fallback", ui-monospace, monospace;

  --color-background: #000000;
  --color-foreground: #ffffff;
  --color-surface: #161616;
  --color-surface-foreground: #cfcfcf;
  --color-primary: #ffffff;
  --color-primary-foreground: #000000;
  --color-secondary: #8f8f8f;
  --color-tertiary: #6f6f6f;
  --color-accent: #d06a4a;
  --color-accent-foreground: #000000;
  --color-error: #ff6b5a;
  --color-success: #57c785;
  --color-border: #3d3d3d;
  --color-focus: #d06a4a;

  --radius-xs: 3px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 8px;
  --radius-xl: 12px;
}

:root[data-theme="light"] {
  --color-background: #fafafa;
  --color-foreground: #000000;
  --color-surface: #ffffff;
  --color-surface-foreground: #000000;
  --color-primary: #000000;
  --color-primary-foreground: #ffffff;
  --color-secondary: #404040;
  --color-tertiary: #666666;
  --color-accent: #0f7a3a;
  --color-accent-foreground: #ffffff;
  --color-error: #b00020;
  --color-success: #006b32;
  --color-border: #d9d9d9;
  --color-focus: #0f7a3a;
}
```

## Typography

The type system has three roles, using two Geist families:

- `font.display`
  - family: Geist Sans
  - weights: 600
  - use: Product name, major headings, high-level page titles.
- `font.body`
  - family: Geist Sans
  - weights: 400, 500, 600
  - use: Interface labels, prose, controls, docs, and dense lists.
- `font.mono`
  - family: Geist Mono
  - weights: 400, 500
  - use: Commands, code, paths, IDs, metrics, timestamps.

Letter spacing is `0` for every Heph web token. Do not use negative letter spacing.

- `typography.heading-72`
  - family: Geist Sans
  - size: 72px
  - weight: 600
  - line height: 72px
  - letter spacing: 0
  - use: Rare hero display.
- `typography.heading-64`
  - family: Geist Sans
  - size: 64px
  - weight: 600
  - line height: 64px
  - letter spacing: 0
  - use: Large launch page title.
- `typography.heading-56`
  - family: Geist Sans
  - size: 56px
  - weight: 600
  - line height: 64px
  - letter spacing: 0
  - use: Product overview title.
- `typography.heading-48`
  - family: Geist Sans
  - size: 48px
  - weight: 600
  - line height: 56px
  - letter spacing: 0
  - use: First-viewport heading.
- `typography.heading-40`
  - family: Geist Sans
  - size: 40px
  - weight: 600
  - line height: 48px
  - letter spacing: 0
  - use: Section opener.
- `typography.heading-32`
  - family: Geist Sans
  - size: 32px
  - weight: 600
  - line height: 40px
  - letter spacing: 0
  - use: Major section heading.
- `typography.heading-24`
  - family: Geist Sans
  - size: 24px
  - weight: 600
  - line height: 32px
  - letter spacing: 0
  - use: Card and detail page heading.
- `typography.heading-20`
  - family: Geist Sans
  - size: 20px
  - weight: 600
  - line height: 28px
  - letter spacing: 0
  - use: Compact panel heading.
- `typography.heading-16`
  - family: Geist Sans
  - size: 16px
  - weight: 600
  - line height: 24px
  - letter spacing: 0
  - use: Dense section title.
- `typography.label-16`
  - family: Geist Sans
  - size: 16px
  - weight: 500
  - line height: 20px
  - letter spacing: 0
  - use: Prominent labels and large controls.
- `typography.label-14`
  - family: Geist Sans
  - size: 14px
  - weight: 500
  - line height: 20px
  - letter spacing: 0
  - use: Default labels, tabs, buttons.
- `typography.label-12`
  - family: Geist Sans
  - size: 12px
  - weight: 500
  - line height: 16px
  - letter spacing: 0
  - use: Metadata labels and badges.
- `typography.copy-20`
  - family: Geist Sans
  - size: 20px
  - weight: 400
  - line height: 32px
  - letter spacing: 0
  - use: Intro copy.
- `typography.copy-16`
  - family: Geist Sans
  - size: 16px
  - weight: 400
  - line height: 24px
  - letter spacing: 0
  - use: Default prose.
- `typography.copy-14`
  - family: Geist Sans
  - size: 14px
  - weight: 400
  - line height: 20px
  - letter spacing: 0
  - use: Product UI copy.
- `typography.copy-13`
  - family: Geist Sans
  - size: 13px
  - weight: 400
  - line height: 18px
  - letter spacing: 0
  - use: Dense helper text.
- `typography.mono-14`
  - family: Geist Mono
  - size: 14px
  - weight: 400
  - line height: 20px
  - letter spacing: 0
  - use: Commands, paths, evidence IDs.
- `typography.mono-13`
  - family: Geist Mono
  - size: 13px
  - weight: 400
  - line height: 18px
  - letter spacing: 0
  - use: Dense data and table cells.
- `typography.mono-12`
  - family: Geist Mono
  - size: 12px
  - weight: 400
  - line height: 16px
  - letter spacing: 0
  - use: Badges, timestamps, tiny metrics.

Typography implementation rules:

- Apply `-webkit-font-smoothing: antialiased`.
- Apply `-moz-osx-font-smoothing: grayscale` where useful.
- Apply `text-rendering: optimizeLegibility`.
- Apply `-webkit-text-size-adjust: 100%`.
- Do not use font weights below `400`.
- Do not change font weight on hover, focus, active, or selected states.
- Use `font-variant-numeric: tabular-nums` for counters, timers, metrics, and totals.
- Use `clamp()` only where a display heading genuinely needs to adapt across viewports.

## Spacing And Layout

Use a 4px spacing base:

- `spacing.1`
  - value: 4px
- `spacing.2`
  - value: 8px
- `spacing.3`
  - value: 12px
- `spacing.4`
  - value: 16px
- `spacing.6`
  - value: 24px
- `spacing.8`
  - value: 32px
- `spacing.10`
  - value: 40px
- `spacing.16`
  - value: 64px
- `spacing.24`
  - value: 96px

Use 8px inside compact groups, 16px between related groups, and 32-40px between major
sections. Product app surfaces should be dense and scannable; public pages can breathe
more, but should still avoid oversized empty decoration.

Reference the `gildrb.com` rhythm when a static page needs portfolio-like restraint:

- desktop wrapper side padding: 48px
- reduced desktop side padding: 32px below very wide layouts
- mobile wrapper side padding: 24px
- image or grid gaps: 20px
- desktop section spacing: 120px
- mobile section spacing: 80px

Recommended breakpoints:

- `breakpoint.sm`
  - value: 401px
- `breakpoint.md`
  - value: 601px
- `breakpoint.lg`
  - value: 961px
- `breakpoint.xl`
  - value: 1200px
- `breakpoint.2xl`
  - value: 1400px

## Radius

The CLI has no roundedness. The website needs a restrained radius system. Avoid heavy
rounded marketing surfaces; cards should stay at 8px or less.

- `radius.xs`
  - value: 3px
  - use: Fine separators, compact inner controls.
- `radius.sm`
  - value: 6px
  - use: Buttons, inputs, badges.
- `radius.md`
  - value: 8px
  - use: Cards and repeated items.
- `radius.lg`
  - value: 8px
  - use: Dialogs and sheets unless the component needs more.
- `radius.xl`
  - value: 12px
  - use: Large modal surfaces only.
- `radius.full`
  - value: 9999px
  - use: Pills, avatars, circular controls.

## Elevation

Hierarchy comes from surfaces and borders first. Use shadows only when a component floats
over content.

- `shadow.card`
  - value: `0 2px 2px rgb(0 0 0 / 0.18)`
  - use: Raised cards on dark backgrounds.
- `shadow.popover`
  - value: `0 1px 1px rgb(0 0 0 / 0.18), 0 8px 16px -8px rgb(0 0 0 / 0.42)`
  - use: Popovers, menus, tooltips.
- `shadow.dialog`
  - value: `0 1px 1px rgb(0 0 0 / 0.18), 0 16px 32px -12px rgb(0 0 0 / 0.55)`
  - use: Dialogs and sheets.

## Motion

Most interactions should feel instant. Use `0ms` when no motion is needed. Honor
`prefers-reduced-motion`.

- `motion.fast`
  - value: 150ms
  - use: Hover and small state transitions.
- `motion.base`
  - value: 200ms
  - use: Popovers, menus, disclosure.
- `motion.slow`
  - value: 300ms
  - use: Dialog and sheet entrance only when a slower transition clarifies state.
- `motion.ease`
  - value: `cubic-bezier(0.175, 0.885, 0.32, 1.1)`
  - use: Short physical reveal.

Motion rules:

- Frequent interactions should avoid extraneous animation.
- Theme switching should not trigger broad transitions.
- Hover states belong inside `@media (hover: hover)`.
- Touch press states should not leave controls looking hovered.
- Do not animate font weight.
- Pause or remove looping animation when off-screen.
- Use `will-change` and GPU hints only for measured rendering problems.

## Components

### Button

- `button.primary`
  - background: `colors.accent`
  - text: `colors.accent-foreground`
  - border: none
  - typography: `typography.label-14`
  - radius: `radius.sm`
  - height: 40px
- `button.secondary`
  - background: `colors.background-200`
  - text: `colors.primary`
  - border: `colors.border`
  - typography: `typography.label-14`
  - radius: `radius.sm`
  - height: 40px
- `button.tertiary`
  - background: transparent
  - text: `colors.primary`
  - border: transparent
  - typography: `typography.label-14`
  - radius: `radius.sm`
  - height: 40px
- `button.error`
  - background: transparent
  - text: `colors.error`
  - border: `colors.error`
  - typography: `typography.label-14`
  - radius: `radius.sm`
  - height: 40px
- `button.small`
  - background: variant-defined
  - text: variant-defined
  - border: variant-defined
  - typography: `typography.label-12`
  - radius: `radius.sm`
  - height: 32px
- `button.large`
  - background: variant-defined
  - text: variant-defined
  - border: variant-defined
  - typography: `typography.label-16`
  - radius: `radius.sm`
  - height: 48px

Use native `<button>` elements. Disable buttons during async submission when duplicate
actions would be harmful. Icon-only controls need explicit `aria-label`s and should use
`currentColor`.

### Input And Textarea

- background: `colors.background-200`
- text: `colors.primary`
- placeholder: `colors.tertiary`
- border: `colors.border`
- focus ring: `colors.accent`
- error text: `colors.error`
- entered text: `typography.copy-14`
- label text: `typography.label-12`

Use native form semantics. Wrap related inputs in a `<form>` so Enter submits naturally.
Clicking an input label should focus the input. Use the correct input `type`. Use native
validation attributes such as `required` when they match the actual requirement. Keep input
font sizes at 16px or larger on touch layouts to avoid iOS zooming.

### Card

Cards are for repeated items, settings groups, detail panels, and tool surfaces. Do not put
cards inside cards.

- background: `colors.background-200`
- foreground: `colors.primary`
- secondary text: `colors.secondary`
- muted values: `colors.tertiary`
- border: `colors.border`
- radius: `radius.md`
- compact padding: `spacing.4`
- comfortable padding: `spacing.6`

### Badge

- `badge.neutral`
  - background: `colors.background-200`
  - text: `colors.secondary`
  - border: `colors.border`
- `badge.success`
  - background: transparent
  - text: `colors.success`
  - border: `colors.success`
- `badge.error`
  - background: transparent
  - text: `colors.error`
  - border: `colors.error`
- `badge.accent`
  - background: transparent
  - text: `colors.accent`
  - border: `colors.accent`

Badges should carry text, not color alone.

### Command Palette

The command palette is the web cousin of the CLI command and inline menu surfaces. Build it
with semantic HTML, buttons, inputs, and tiny JavaScript or TypeScript.

- dialog background: `colors.background-200`
- input text: `colors.primary`
- placeholder: `colors.tertiary`
- selected row background: transparent or `colors.background-200`
- selected row text: `colors.primary`
- command label: uppercase `colors.secondary`
- command value: lowercase `colors.tertiary`

Sequential focusable lists should support predictable keyboard navigation when appropriate.
If a menu should open immediately on press, use pointer or mouse down deliberately rather
than waiting for a delayed click.

### Data Table

Tables should feel like dense evidence and material indexes. Use real `<table>` markup when
the content is truly tabular; otherwise use lists.

- header labels: uppercase `colors.secondary`, `typography.label-12`
- values: lowercase where UI-owned, `colors.primary`, `typography.copy-14`
- metadata: `colors.tertiary`, `typography.mono-13`
- row border: `colors.border`
- hover: `colors.background-200`

### Tabs

- active label: `colors.primary`
- inactive label: `colors.secondary`
- active indicator: `colors.accent`
- panel background: transparent or `colors.background-100`

Tabs should be native links or buttons depending on whether they navigate or switch local
state.

### Dialog And Sheet

Use a dialog for reversible flows and a destructive confirmation flow for destructive
actions. Native `<dialog>` is acceptable when the implementation stays accessible and
testable.

- background: `colors.background-200`
- title: `colors.primary`, `typography.heading-20`
- description: `colors.tertiary`, `typography.copy-14`
- border: `colors.border`
- radius: `radius.lg`
- shadow: `shadow.dialog`

### Alert

- `alert.info`
  - border: `colors.border`
  - title: `colors.primary`
  - body: `colors.tertiary`
- `alert.success`
  - border: `colors.success`
  - title: `colors.success`
  - body: `colors.tertiary`
- `alert.error`
  - border: `colors.error`
  - title: `colors.error`
  - body: `colors.tertiary`

Show feedback close to the trigger. A successful copy should use inline feedback near the
copied text, not a distant notification.

### Evidence Panel

The evidence panel is a first-class web component because citations are core to Heph.

- panel background: `colors.background-200`
- evidence ID: `colors.primary`, `typography.mono-13`
- source path: `colors.tertiary`, `typography.mono-13`
- label: uppercase `colors.secondary`, `typography.label-12`
- excerpt: `colors.primary`, `typography.copy-14`
- missing or unverified state: `colors.error` plus text

### Material Item

- active
  - label: `colors.primary`
  - metadata: `colors.tertiary`
  - marker: `colors.tertiary`
- disabled
  - label: `colors.tertiary`
  - metadata: `colors.tertiary`
  - marker: `colors.tertiary`
- selected
  - label: `colors.primary`
  - metadata: `colors.secondary`
  - marker: `colors.primary`

Render material names with `@name` on product surfaces to match the CLI.

### Media

- Use real `<img>` elements for inspectable images.
- Provide useful `alt` text for meaningful images.
- Mark decorative images with empty `alt`.
- Use responsive image sources where it materially improves loading.
- Lazy-load non-critical images.
- Preload only truly critical first-viewport assets.
- Use `muted` and `playsinline` for autoplaying video.
- Avoid many autoplaying videos, especially on iOS.

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
2. Use this file for browser-only decisions: typography, radius, layout, forms, focus,
   media, motion, and responsive behavior.
3. Build with HTML, CSS, and vanilla JavaScript or tiny TypeScript.
4. Do not introduce a framework, component library, router, or bundler by default.
5. Implement colors as CSS custom properties with the token names in this file.
6. Keep labels uppercase and UI-owned values lowercase.
7. Use native controls before custom controls.
8. Do not copy terminal dimensions such as `38 columns` into responsive browser layout.
9. If a web component represents an existing CLI concept, map its colors through the
   component sections above.
10. After changing palette semantics, update both `cli-design.md` and `design.md`, then run
    `uv run python -m scripts.check_design_docs`.
