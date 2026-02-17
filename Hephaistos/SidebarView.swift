import SwiftUI

struct SidebarView: View {
    @EnvironmentObject private var appState: AppState
    private let contentInset: CGFloat = AppLayout.paneHorizontal
    private let rowInset = EdgeInsets(top: 1, leading: 0, bottom: 1, trailing: 0)

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
            HStack {
                SidebarIconButton(
                    systemName: "sidebar.left",
                    isActive: !appState.isLeftSidebarCollapsed,
                    accessibilityLabel: appState.isLeftSidebarCollapsed ? "Expand Left Sidebar" : "Collapse Left Sidebar"
                ) {
                    appState.toggleLeftSidebar()
                }
                Spacer()
            }

            Spacer()

            SidebarCompactButton(systemName: "plus", accessibilityLabel: "Create New Chat") {
                appState.newChat()
            }

            SidebarCompactButton(systemName: "magnifyingglass", accessibilityLabel: "Search Chats") {
                appState.toggleLeftSidebar()
                if !appState.isSearchVisible {
                    appState.toggleSearch()
                }
            }

            SidebarCompactButton(systemName: "gearshape", accessibilityLabel: "Open Settings") {
                appState.showSettings = true
            }
        }
    }

    private var expandedSidebar: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                SidebarIconButton(
                    systemName: "sidebar.left",
                    isActive: !appState.isLeftSidebarCollapsed,
                    accessibilityLabel: appState.isLeftSidebarCollapsed ? "Expand Left Sidebar" : "Collapse Left Sidebar"
                ) {
                    appState.toggleLeftSidebar()
                }

                SidebarActionButton(title: "New Chat") {
                    appState.newChat()
                }

                SidebarActionButton(title: appState.isSearchVisible ? "Hide Search" : "Search") {
                    appState.toggleSearch()
                }
            }
            .padding(.horizontal, contentInset)

            if appState.isSearchVisible {
                TextField("Search history", text: $appState.sidebarQuery)
                    .font(.system(size: AppTypography.body))
                    .textFieldStyle(.roundedBorder)
                    .controlSize(.small)
                    .padding(.horizontal, contentInset)
            }

            List {
                Section {
                    ForEach(appState.projects) { project in
                        SidebarSelectableRow(
                            title: project.name,
                            isSelected: appState.selectedProjectID == project.id
                        ) {
                            appState.selectProject(project.id)
                        }
                        .listRowInsets(rowInset)
                        .listRowSeparator(.hidden)
                        .listRowBackground(Color.clear)
                    }
                } header: {
                    HStack(spacing: 8) {
                        Text("Projects")
                            .font(.system(size: AppTypography.small, weight: .medium))
                            .foregroundStyle(AppTheme.textSecondary)

                        Spacer(minLength: 0)

                        Button {
                            appState.createProject()
                        } label: {
                            Image(systemName: "folder.badge.plus")
                                .font(.system(size: AppTypography.small, weight: .medium))
                                .foregroundStyle(AppTheme.textSecondary)
                                .frame(width: 18, height: 18)
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("Create Project")
                    }
                    .textCase(nil)
                    .padding(.horizontal, contentInset)
                }

                Section {
                    if appState.filteredChats.isEmpty {
                        Text("No chats yet. Create one with New Chat.")
                            .font(.system(size: AppTypography.body))
                            .foregroundStyle(AppTheme.textMuted)
                            .padding(.horizontal, contentInset)
                            .padding(.vertical, 4)
                            .listRowInsets(rowInset)
                            .listRowSeparator(.hidden)
                            .listRowBackground(Color.clear)
                    } else {
                        ForEach(appState.filteredChats) { chat in
                            SidebarSelectableRow(
                                title: chat.title,
                                isSelected: appState.selectedChatID == chat.id
                            ) {
                                appState.selectChat(chat.id)
                            }
                            .listRowInsets(rowInset)
                            .listRowSeparator(.hidden)
                            .listRowBackground(Color.clear)
                        }
                    }
                } header: {
                    Text("Chats")
                        .font(.system(size: AppTypography.small, weight: .medium))
                        .foregroundStyle(AppTheme.textSecondary)
                        .textCase(nil)
                        .padding(.horizontal, contentInset)
                }
            }
            .listStyle(.plain)
            .environment(\.defaultMinListRowHeight, 30)
            .scrollContentBackground(.hidden)
            .background(AppTheme.sidebar)

            Button {
                appState.showSettings = true
            } label: {
                Text("SETTINGS")
                    .font(.system(size: AppTypography.small, weight: .regular))
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
                .font(.system(size: AppTypography.small, weight: .semibold))
                .foregroundStyle(AppTheme.textSecondary)
                .frame(width: 28, height: 28)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(accessibilityLabel)
    }
}

private struct SidebarActionButton: View {
    let title: String
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: AppTypography.small, weight: .regular))
                .foregroundStyle(AppTheme.textSecondary)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .frame(maxWidth: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: 7, style: .continuous)
                        .fill(isHovering ? AppTheme.hover : .clear)
                )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

private struct SidebarIconButton: View {
    let systemName: String
    let isActive: Bool
    let accessibilityLabel: String
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: AppTypography.small, weight: .medium))
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

private struct SidebarSelectableRow: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        SelectableHoverRow(isSelected: isSelected, action: action) {
            Text(title)
                .font(.system(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)
                .lineLimit(1)
        }
    }
}

#Preview {
    SidebarView()
        .environmentObject(AppState())
}
