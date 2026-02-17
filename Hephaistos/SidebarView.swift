import SwiftUI

struct SidebarView: View {
    private struct PendingChatAction {
        let projectID: Project.ID
        let chatID: Chat.ID
        let currentTitle: String
    }

    @EnvironmentObject private var appState: AppState
    let isCompact: Bool
    @State private var projectPendingRename: Project?
    @State private var renameProjectNameDraft = ""
    @State private var projectPendingDelete: Project?
    @State private var chatPendingRename: PendingChatAction?
    @State private var renameChatTitleDraft = ""
    @State private var chatPendingDelete: PendingChatAction?

    init(
        isCompact: Bool = false
    ) {
        self.isCompact = isCompact
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
        .alert("Rename Project", isPresented: isRenameAlertPresented) {
            TextField("Project Name", text: $renameProjectNameDraft)

            Button("Cancel", role: .cancel) {
                projectPendingRename = nil
                renameProjectNameDraft = ""
            }

            Button("Rename") {
                commitProjectRename()
            }
            .keyboardShortcut(.defaultAction)
        } message: {
            Text("Enter a new name for this project.")
        }
        .alert("Delete Project", isPresented: isDeleteAlertPresented) {
            Button("Cancel", role: .cancel) {
                projectPendingDelete = nil
            }

            Button("Delete", role: .destructive) {
                confirmDeleteProject()
            }
        } message: {
            Text("This project and its local history will be removed from the sidebar.")
        }
        .alert("Rename Chat", isPresented: isRenameChatAlertPresented) {
            TextField("Chat Name", text: $renameChatTitleDraft)

            Button("Cancel", role: .cancel) {
                chatPendingRename = nil
                renameChatTitleDraft = ""
            }

            Button("Rename") {
                commitChatRename()
            }
            .keyboardShortcut(.defaultAction)
        } message: {
            Text("Enter a new name for this chat.")
        }
        .alert("Delete Chat", isPresented: isDeleteChatAlertPresented) {
            Button("Cancel", role: .cancel) {
                chatPendingDelete = nil
            }

            Button("Delete", role: .destructive) {
                confirmDeleteChat()
            }
        } message: {
            Text("This chat will be permanently removed.")
        }
    }

    private var collapsedSidebar: some View {
        VStack(spacing: 12) {
            SidebarCompactButton(systemName: "square.and.pencil", accessibilityLabel: "Create New Chat") {
                appState.newChat()
            }

            SidebarCompactButton(
                systemName: "magnifyingglass",
                accessibilityLabel: "Open Search",
                isActive: appState.isSpotlightSearchPresented
            ) {
                appState.isSpotlightSearchPresented = true
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

                SidebarPrimaryActionRow(systemName: "magnifyingglass", title: "Search") {
                    appState.isSpotlightSearchPresented = true
                }
            }

            ScrollView(.vertical, showsIndicators: false) {
                let projectEntries = appState.sidebarProjects.filter(\.hasDirectory)
                let chatEntries = appState.sidebarProjects.filter { !$0.hasDirectory }

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
                                },
                                renameAction: {
                                    beginProjectRename(project)
                                },
                                deleteAction: {
                                    projectPendingDelete = project
                                }
                            )

                            if isExpanded {
                                if !projectChats.isEmpty {
                                    ForEach(projectChats) { chat in
                                        SidebarChatRow(
                                            title: chat.title,
                                            isSelected: appState.selectedProjectID == project.id && appState.selectedChatID == chat.id,
                                            isPinned: appState.isChatPinned(chat.id),
                                            moveTargets: projectEntries.filter { $0.id != project.id },
                                            renameAction: {
                                                beginChatRename(projectID: project.id, chat: chat)
                                            },
                                            moveToProjectAction: { targetProjectID in
                                                appState.moveChat(chat.id, from: project.id, to: targetProjectID)
                                            },
                                            togglePinAction: {
                                                appState.toggleChatPin(chat.id)
                                            },
                                            deleteAction: {
                                                chatPendingDelete = PendingChatAction(
                                                    projectID: project.id,
                                                    chatID: chat.id,
                                                    currentTitle: chat.title
                                                )
                                            }
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
                            let projectChats = appState.chatsForChatCategory(for: project)

                            ForEach(projectChats) { chat in
                                SidebarChatRow(
                                    title: chat.title,
                                    isSelected: appState.selectedProjectID == project.id && appState.selectedChatID == chat.id,
                                    isPinned: appState.isChatPinned(chat.id),
                                    moveTargets: projectEntries,
                                    renameAction: {
                                        beginChatRename(projectID: project.id, chat: chat)
                                    },
                                    moveToProjectAction: { targetProjectID in
                                        appState.moveChat(chat.id, from: project.id, to: targetProjectID)
                                    },
                                    togglePinAction: {
                                        appState.toggleChatPin(chat.id)
                                    },
                                    deleteAction: {
                                        chatPendingDelete = PendingChatAction(
                                            projectID: project.id,
                                            chatID: chat.id,
                                            currentTitle: chat.title
                                        )
                                    }
                                ) {
                                    appState.selectChat(chat.id, in: project.id)
                                }
                            }
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .background(AppTheme.sidebar)

            VStack(alignment: .leading, spacing: 8) {
                SidebarPrimaryActionRow(systemName: "gearshape", title: "Settings") {
                    appState.showSettings = true
                }
            }
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
        .padding(.trailing, SidebarRowLayout.trailingInset)
        .padding(.bottom, 6)
    }

    private var isRenameAlertPresented: Binding<Bool> {
        Binding(
            get: { projectPendingRename != nil },
            set: { isPresented in
                if !isPresented {
                    projectPendingRename = nil
                    renameProjectNameDraft = ""
                }
            }
        )
    }

    private var isDeleteAlertPresented: Binding<Bool> {
        Binding(
            get: { projectPendingDelete != nil },
            set: { isPresented in
                if !isPresented {
                    projectPendingDelete = nil
                }
            }
        )
    }

    private func beginProjectRename(_ project: Project) {
        projectPendingRename = project
        renameProjectNameDraft = project.name
    }

    private func commitProjectRename() {
        guard let projectID = projectPendingRename?.id else { return }
        appState.renameProject(projectID, to: renameProjectNameDraft)
        projectPendingRename = nil
        renameProjectNameDraft = ""
    }

    private func confirmDeleteProject() {
        guard let projectID = projectPendingDelete?.id else { return }
        appState.deleteProject(projectID)
        projectPendingDelete = nil
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
            .padding(.leading, SidebarRowLayout.leadingInset)
            .padding(.trailing, SidebarRowLayout.trailingInset)
            .padding(.vertical, AppLayout.rowVertical)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(isHovering ? AppTheme.hover : .clear)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

private struct SidebarProjectRow: View {
    let title: String
    let isSelected: Bool
    let isExpanded: Bool
    let selectAction: () -> Void
    let toggleExpansionAction: () -> Void
    let renameAction: () -> Void
    let deleteAction: () -> Void
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

                Menu {
                    Button("Rename") {
                        renameAction()
                    }

                    Button("Delete", role: .destructive) {
                        deleteAction()
                    }
                } label: {
                    Image(systemName: "ellipsis")
                        .font(AppTypography.font(size: AppTypography.icon, weight: .semibold))
                        .foregroundStyle(AppTheme.textSecondary)
                        .frame(width: 16, height: 16)
                }
                .menuStyle(.borderlessButton)
                .opacity(isHovering || isSelected ? 1 : 0)
                .allowsHitTesting(isHovering || isSelected)
            }
            .contentShape(Rectangle())
            .onTapGesture(perform: selectAction)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.leading, SidebarRowLayout.leadingInset)
        .padding(.trailing, SidebarRowLayout.trailingInset)
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
    static let leadingInset: CGFloat = AppLayout.rowHorizontal + 8
    static let trailingInset: CGFloat = AppLayout.rowHorizontal
    static let iconWidth: CGFloat = 14
    static let textSpacing: CGFloat = 10
    static let textLeading: CGFloat = leadingInset + iconWidth + textSpacing
}

#Preview {
    SidebarView()
        .environmentObject(AppState())
}
