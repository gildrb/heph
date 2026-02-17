import SwiftUI

struct SidebarView: View {
    @EnvironmentObject private var appState: AppState
    private let contentInset: CGFloat = AppLayout.paneHorizontal

    var body: some View {
        VStack(alignment: .leading, spacing: appState.isLeftSidebarCollapsed ? 12 : 10) {
            if appState.isLeftSidebarCollapsed {
                collapsedSidebar
            } else {
                expandedSidebar
            }
        }
        .padding(.vertical, AppLayout.paneVertical)
        .padding(.horizontal, appState.isLeftSidebarCollapsed ? AppLayout.paneHorizontal : 0)
    }

    private var collapsedSidebar: some View {
        VStack(alignment: .leading, spacing: 12) {
            Spacer()

            SidebarCompactButton(systemName: "plus", accessibilityLabel: "Create New Chat") {
                appState.newChat()
            }

            SidebarCompactButton(systemName: "magnifyingglass", accessibilityLabel: "Open Search") {
                if appState.isLeftSidebarCollapsed {
                    appState.toggleLeftSidebar()
                }
            }

            SidebarCompactButton(systemName: "gearshape", accessibilityLabel: "Open Settings") {
                appState.showSettings = true
            }
        }
    }

    private var expandedSidebar: some View {
        VStack(alignment: .leading, spacing: 10) {
            VStack(alignment: .leading, spacing: 8) {
                SidebarPrimaryActionRow(systemName: "plus", title: "New Chat") {
                    appState.newChat()
                }

                SidebarSearchBar(text: $appState.sidebarQuery)
            }
            .padding(.horizontal, contentInset)

            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: 0) {
                    HStack(spacing: 8) {
                        Text("Projects")
                            .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                            .foregroundStyle(AppTheme.textSecondary)

                        Spacer(minLength: 0)

                        Button {
                            appState.createProject()
                        } label: {
                            Image(systemName: "folder.badge.plus")
                                .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                                .foregroundStyle(AppTheme.textSecondary)
                                .frame(width: 18, height: 18)
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("Create Project")
                    }
                    .padding(.horizontal, contentInset)
                    .padding(.bottom, 4)

                    if appState.sidebarProjects.isEmpty {
                        Text("No matches found.")
                            .font(AppTypography.font(size: AppTypography.body))
                            .foregroundStyle(AppTheme.textMuted)
                            .padding(.horizontal, contentInset)
                            .padding(.vertical, 4)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    } else {
                        ForEach(appState.sidebarProjects) { project in
                            let projectChats = appState.chats(for: project)
                            let isExpanded = appState.hasSidebarQuery || appState.isProjectExpanded(project.id)

                            SidebarProjectRow(
                                title: project.name,
                                isSelected: appState.selectedProjectID == project.id,
                                isExpanded: isExpanded
                            ) {
                                if appState.hasSidebarQuery {
                                    appState.selectProject(project.id)
                                } else if appState.selectedProjectID == project.id {
                                    appState.toggleProjectExpansion(project.id)
                                } else {
                                    appState.expandProject(project.id)
                                    appState.selectProject(project.id)
                                }
                            }

                            if isExpanded {
                                if projectChats.isEmpty {
                                    Text("No chats yet.")
                                        .font(AppTypography.font(size: AppTypography.small))
                                        .foregroundStyle(AppTheme.textMuted)
                                        .padding(.horizontal, AppLayout.rowHorizontal + 22)
                                        .padding(.vertical, 4)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                } else {
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
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .background(AppTheme.sidebar)

            Button {
                appState.showSettings = true
            } label: {
                Text("SETTINGS")
                    .font(AppTypography.font(size: AppTypography.small, weight: .regular))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, contentInset)
            }
            .buttonStyle(.plain)
        }
    }
}

private struct SidebarCompactButton: View {
    let systemName: String
    let accessibilityLabel: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(AppTypography.font(size: AppTypography.small, weight: .semibold))
                .foregroundStyle(AppTheme.textSecondary)
                .frame(width: 28, height: 28)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(accessibilityLabel)
    }
}

private struct SidebarPrimaryActionRow: View {
    let systemName: String
    let title: String
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                Image(systemName: systemName)
                    .font(AppTypography.font(size: AppTypography.small, weight: .semibold))
                    .foregroundStyle(AppTheme.textSecondary)

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

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary)

            TextField("Search", text: $text)
                .textFieldStyle(.plain)
                .font(AppTypography.font(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)

            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(AppTypography.font(size: AppTypography.small))
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
    let action: () -> Void

    var body: some View {
        SelectableHoverRow(isSelected: isSelected, action: action) {
            HStack(spacing: 8) {
                Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                    .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(width: 10)

                Text(title)
                    .font(AppTypography.font(size: AppTypography.body))
                    .foregroundStyle(AppTheme.textPrimary)
                    .lineLimit(1)
            }
        }
    }
}

private struct SidebarChatRow: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        SelectableHoverRow(
            isSelected: isSelected,
            horizontalPadding: AppLayout.rowHorizontal + 22,
            action: action
        ) {
            Text(title)
                .font(AppTypography.font(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)
                .lineLimit(1)
        }
    }
}

#Preview {
    SidebarView()
        .environmentObject(AppState())
}
