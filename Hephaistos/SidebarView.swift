import SwiftUI

struct SidebarView: View {
    @EnvironmentObject private var appState: AppState
    let isCompact: Bool
    let onRequestExpand: (() -> Void)?
    @FocusState private var isSearchFocused: Bool

    init(
        isCompact: Bool = false,
        onRequestExpand: (() -> Void)? = nil
    ) {
        self.isCompact = isCompact
        self.onRequestExpand = onRequestExpand
    }

    var body: some View {
        Group {
            if isCompact {
                collapsedSidebar
                    .transition(.opacity.combined(with: .move(edge: .leading)))
            } else {
                expandedSidebar
                    .transition(.opacity.combined(with: .move(edge: .leading)))
            }
        }
        .padding(.top, isCompact ? AppLayout.paneVertical : AppLayout.rowVertical)
        .padding(.bottom, AppLayout.paneVertical)
        .padding(.horizontal, isCompact ? AppLayout.paneHorizontal : 0)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .animation(.easeInOut(duration: 0.2), value: isCompact)
    }

    private var collapsedSidebar: some View {
        VStack(spacing: 12) {
            SidebarCompactButton(systemName: "square.and.pencil", accessibilityLabel: "Create New Chat") {
                appState.newChat()
            }

            SidebarCompactButton(
                systemName: "magnifyingglass",
                accessibilityLabel: "Expand Sidebar for Search",
                isActive: appState.hasSidebarQuery
            ) {
                expandSidebar(focusSearch: true)
            }

            SidebarCompactButton(systemName: "folder.badge.plus", accessibilityLabel: "Create Project") {
                appState.createProject()
            }

            Spacer(minLength: 0)

            SidebarCompactButton(systemName: "gearshape", accessibilityLabel: "Open Settings") {
                appState.showSettings = true
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
    }

    private var expandedSidebar: some View {
        VStack(alignment: .leading, spacing: 10) {
            VStack(alignment: .leading, spacing: 8) {
                SidebarPrimaryActionRow(systemName: "square.and.pencil", title: "New Chat") {
                    appState.newChat()
                }
            }

            SidebarSearchBar(text: $appState.sidebarQuery, isFocused: $isSearchFocused)

            ScrollView(.vertical, showsIndicators: false) {
                let projectEntries = appState.sidebarProjects.filter(\.hasDirectory)
                let chatEntries = appState.sidebarProjects.filter { !$0.hasDirectory }
                let hasChatResults = chatEntries.contains { !appState.chats(for: $0).isEmpty }
                let hasProjectResults = !projectEntries.isEmpty

                VStack(alignment: .leading, spacing: 14) {
                    VStack(alignment: .leading, spacing: 0) {
                        sidebarCategoryTitle("Projects")

                        SidebarPrimaryActionRow(systemName: "folder.badge.plus", title: "New Project") {
                            appState.createProject()
                        }
                        .padding(.bottom, 4)

                        ForEach(projectEntries) { project in
                            let projectChats = appState.chats(for: project)
                            let isExpanded = appState.isProjectExpanded(project.id)

                            SidebarProjectRow(
                                title: project.name,
                                isSelected: appState.selectedProjectID == project.id,
                                isExpanded: isExpanded,
                                selectAction: {
                                    appState.selectProject(project.id)
                                },
                                toggleExpansionAction: {
                                    appState.toggleProjectExpansion(project.id)
                                }
                            )

                            if isExpanded {
                                if !projectChats.isEmpty {
                                    ForEach(projectChats) { chat in
                                        SidebarChatRow(
                                            title: chat.title,
                                            isSelected: appState.selectedProjectID == project.id && appState.selectedChatID == chat.id
                                        ) {
                                            appState.selectChat(chat.id, in: project.id)
                                        }
                                    }
                                }
                            }
                        }
                    }

                    VStack(alignment: .leading, spacing: 0) {
                        sidebarCategoryTitle("Chats")

                        ForEach(chatEntries) { project in
                            let projectChats = appState.chats(for: project)

                            ForEach(projectChats) { chat in
                                SidebarChatRow(
                                    title: chat.title,
                                    isSelected: appState.selectedProjectID == project.id && appState.selectedChatID == chat.id
                                ) {
                                    appState.selectChat(chat.id, in: project.id)
                                }
                            }
                        }
                    }

                    if appState.hasSidebarQuery && !hasProjectResults && !hasChatResults {
                        Text("No matches found.")
                            .font(AppTypography.font(size: AppTypography.body))
                            .foregroundStyle(AppTheme.textMuted)
                            .padding(.leading, SidebarRowLayout.textLeading)
                            .padding(.trailing, AppLayout.rowHorizontal)
                            .padding(.top, 4)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .background(AppTheme.sidebar)

            VStack(alignment: .leading, spacing: 8) {
                Button {
                    appState.showSettings = true
                } label: {
                    Text("SETTINGS")
                        .font(AppTypography.font(size: AppTypography.category, weight: .regular))
                        .foregroundStyle(AppTheme.textSecondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.leading, SidebarRowLayout.textLeading)
                        .padding(.trailing, AppLayout.rowHorizontal)
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func expandSidebar(focusSearch: Bool) {
        onRequestExpand?()

        if focusSearch {
            focusSearchBar(after: 0.2)
        }
    }

    private func focusSearchBar(after delay: Double = 0) {
        DispatchQueue.main.asyncAfter(deadline: .now() + delay) {
            isSearchFocused = true
        }
    }

    private func sidebarCategoryTitle(_ title: String) -> some View {
        HStack(spacing: 8) {
            Text(title)
                .font(AppTypography.font(size: AppTypography.category, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary)
            Spacer(minLength: 0)
        }
        .padding(.leading, SidebarRowLayout.textLeading)
        .padding(.trailing, AppLayout.rowHorizontal)
        .padding(.bottom, 6)
    }
}

private struct SidebarCompactButton: View {
    let systemName: String
    let accessibilityLabel: String
    let isActive: Bool
    let action: () -> Void
    @State private var isHovering = false

    init(
        systemName: String,
        accessibilityLabel: String,
        isActive: Bool = false,
        action: @escaping () -> Void
    ) {
        self.systemName = systemName
        self.accessibilityLabel = accessibilityLabel
        self.isActive = isActive
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(AppTypography.font(size: AppTypography.icon, weight: .semibold))
                .foregroundStyle(AppTheme.textSecondary)
                .frame(width: 28, height: 28)
                .background(
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .fill(isActive || isHovering ? AppTheme.hover : .clear)
                )
        }
        .buttonStyle(.plain)
        .accessibilityLabel(accessibilityLabel)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

private struct SidebarPrimaryActionRow: View {
    let systemName: String
    let title: String
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: SidebarRowLayout.textSpacing) {
                Image(systemName: systemName)
                    .font(AppTypography.font(size: AppTypography.icon, weight: .semibold))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(width: SidebarRowLayout.iconWidth)

                Text(title)
                    .font(AppTypography.font(size: AppTypography.body, weight: .regular))
                    .foregroundStyle(AppTheme.textSecondary)
                    .lineLimit(1)

                Spacer(minLength: 0)
            }
            .padding(.horizontal, AppLayout.rowHorizontal)
            .padding(.vertical, AppLayout.rowVertical)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(isHovering ? AppTheme.hover : .clear)
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

private struct SidebarSearchBar: View {
    @Binding var text: String
    @FocusState.Binding var isFocused: Bool

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .font(AppTypography.font(size: AppTypography.icon, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary)

            TextField("Search", text: $text)
                .textFieldStyle(.plain)
                .font(AppTypography.font(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)
                .focused($isFocused)

            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(AppTypography.font(size: AppTypography.icon))
                        .foregroundStyle(AppTheme.textMuted)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Clear Search")
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .fill(AppTheme.control)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(AppTheme.line, lineWidth: 1)
        )
    }
}

private struct SidebarProjectRow: View {
    let title: String
    let isSelected: Bool
    let isExpanded: Bool
    let selectAction: () -> Void
    let toggleExpansionAction: () -> Void
    @State private var isHovering = false

    var body: some View {
        HStack(spacing: SidebarRowLayout.textSpacing) {
            Button(action: toggleExpansionAction) {
                Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                    .font(AppTypography.font(size: AppTypography.icon, weight: .medium))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(width: SidebarRowLayout.iconWidth)
            }
            .buttonStyle(.plain)
            .accessibilityLabel(isExpanded ? "Collapse Project History" : "Expand Project History")

            HStack(spacing: 8) {
                Text(title)
                    .font(AppTypography.font(size: AppTypography.body))
                    .foregroundStyle(AppTheme.textPrimary)
                    .lineLimit(1)

                Spacer(minLength: 0)
            }
            .contentShape(Rectangle())
            .onTapGesture(perform: selectAction)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, AppLayout.rowHorizontal)
        .padding(.vertical, AppLayout.rowVertical)
        .background(backgroundColor)
        .onHover { hovering in
            isHovering = hovering
        }
    }

    private var backgroundColor: Color {
        if isSelected {
            return AppTheme.selected
        }
        return isHovering ? AppTheme.hover : .clear
    }
}

private struct SidebarChatRow: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        SelectableHoverRow(
            isSelected: isSelected,
            horizontalPadding: SidebarRowLayout.textLeading,
            action: action
        ) {
            Text(title)
                .font(AppTypography.font(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)
                .lineLimit(1)
        }
    }
}

private enum SidebarRowLayout {
    static let iconWidth: CGFloat = 14
    static let textSpacing: CGFloat = 10
    static let textLeading: CGFloat = AppLayout.rowHorizontal + iconWidth + textSpacing
}

#Preview {
    SidebarView()
        .environmentObject(AppState())
}
