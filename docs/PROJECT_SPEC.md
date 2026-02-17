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
- Font sizes:
  - Small: `13`
  - Body: `15`
  - Hero: `71` (adaptive down in compact layout)
- Pane proportions (target):
  - Left sidebar: `1/5`
  - Right panel: `1/7`
  - Main content: remaining space, prioritized to absorb shrink
- Hover and active rows in sidebars must span full sidebar width
- Padding uses shared layout tokens (`AppLayout`) for consistency

## Interaction Rules (Current)
- Left and right panel toggles are in top bar corners
- Left sidebar collapse switches to an icon rail with persistent quick actions (new chat, search, create project, settings)
- Top navigation arrows support back/forward state history
  - History tracks project/chat context
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
