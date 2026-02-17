# Hephaistos Workboard

Last updated: 2026-02-17

## Session Start Checklist
1. Read `docs/PROJECT_SPEC.md`
2. Read this file (`docs/WORKBOARD.md`)
3. Pick the top item in `Next Up`
4. Implement and verify (`xcodebuild`)
5. Update `Done Recently`, `Next Up`, and `Open Questions`

## Next Up
- Bundle Inter font files in app resources so typography does not depend on OS-installed fonts.
- Review compact-window behavior visually and tune any remaining crowding in right panel controls.
- Start functionality pass for real vault folder selection and creation flow (Finder-based open/create UX).

## In Progress
- None

## Done Recently
- Reworked left sidebar collapse into a ChatGPT-style icon rail with persistent quick actions and a focused search handoff when expanding.
- Collapsed top chrome into a single row and moved both sidebar toggles into that row so controls sit on the traffic-light line instead of below it.
- Unified pane padding tokens across left/main/right panes and replaced right `Form` layout with explicit padded cards for consistent alignment.
- Increased main content top inset so the project title has more space below the top bar.
- Replaced Search/Hide toggle with an always-visible sidebar search bar stacked below New Chat.
- Added a dedicated no-directory "Chats" folder so normal (non-vault) chats are separated from project chats.
- Moved chat history into project dropdowns in the left sidebar (removed standalone global Chats list).
- Reduced workspace tab-strip height for a slimmer top tab bar.
- Standardized app-wide spacing tokens and pane paddings.
- Fixed sidebar full-width hover/active row behavior.
- Implemented navigation history for back/forward arrows.
- Repositioned panel toggles to top bar corners.
- Improved compact-window responsiveness (adaptive bars, pane min widths, scroll behavior).
- Replaced chat send text button with upward arrow icon.
- Switched typography calls across project to `Inter` via shared `AppTypography.font(...)`.
- Reduced top chrome heights to remove excess vertical space in the header area.
- Moved top toggle controls into the titlebar line so they align with traffic lights.
- Replaced sidebar `List` sections with a custom scroll stack to enforce consistent left padding, full-width row hover, and spacing between Projects and Chats.

## Open Questions
- Should we lock a minimum window width/height at app level to avoid extreme compact breakpoints?
- Should right panel auto-collapse below a width threshold, or always stay visible until manually toggled?

## Notes
- If UI rules change, update `docs/PROJECT_SPEC.md` first, then implement.
- Keep this file concise and current so any new session can continue immediately.
