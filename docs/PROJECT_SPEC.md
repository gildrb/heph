# Hephaistos Project Spec

## Product Goal
Hephaistos is a native-feeling macOS study app:
- AI wrapper with preset advanced parameters
- LLM-agnostic design
- Project model based on local directories ("vaults"), similar to Obsidian
- Portable project organization, later cloud-sync capable

## Current Architecture
- UI framework: SwiftUI (macOS app)
- Primary state container: `AppState`
- Layout composition:
  - `MainView` orchestrates three-pane shell and top bars
  - `SidebarView` handles projects/chats/search/settings entry
  - `ContentAreaView` handles project hero, composer, project history
  - `RightPanelView` handles LLM/preset parameter controls
- Row interaction reuse: `SelectableHoverRow`
- Theme and sizing tokens: `AppTheme`, `AppTypography`, `AppLayout`

## Visual Rules (Current)
- Font family: `Inter` across app via `AppTypography.font(...)`
- Text sizes:
  - App text tokens (`small`, `body`, `category`, `hero`): `15`
  - Symbol/icon token (`icon`): `13`
- Pane sizing (current):
  - Left sidebar defaults near `1/5` and is user-resizable via divider drag.
  - Right panel targets `1/7` and can be collapsed to icon rail via toggle.
  - Main content always stays between left and right panes and absorbs remaining space.
- Hover and active rows in sidebars must span full sidebar width
- Padding uses shared layout tokens (`AppLayout`) for consistency

## Interaction Rules (Current)
- Right panel toggle is in the top bar corner
- Left sidebar has no hide toggle; it is always present and width-resizable by dragging the left divider
- Left sidebar auto-switches to compact icon rail when narrowed to compact width, while retaining quick actions (new chat, search, create project, settings)
- Top navigation arrows support back/forward state history
  - History tracks project/chat context
- Project tabs are horizontally scrollable in the top bar to prevent layout collapse when many tabs are open
- Search filters by chat title and chat content (word-based)
- Composer supports:
  - Text input
  - File attachments
  - Send with upward arrow button

## Non-Negotiables
- Native macOS feel and tidy alignment
- Reuse same spacing/color/typography primitives
- No decorative fake macOS traffic lights
- Keep UI consistency over one-off styling
