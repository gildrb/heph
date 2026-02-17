import SwiftUI
import UniformTypeIdentifiers

struct ContentAreaView: View {
    @EnvironmentObject private var appState: AppState
    @FocusState private var isComposerFocused: Bool
    @State private var isPathHovering = false
    @State private var isFileImporterPresented = false
    
    private var isDraftEmpty: Bool {
        appState.draftMessage.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private var canSendDraft: Bool {
        !isDraftEmpty || !appState.draftAttachments.isEmpty
    }

    var body: some View {
        GeometryReader { proxy in
            let isCompact = proxy.size.width < 980 || proxy.size.height < 700

            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: isCompact ? 16 : 22) {
                    if let project = appState.selectedProject {
                        header(for: project, isCompact: isCompact)
                        chatComposer
                        historySection(for: appState.filteredChats)
                    } else {
                        Text("Select a project to begin")
                            .font(AppTypography.font(size: AppTypography.body))
                            .foregroundStyle(AppTheme.textSecondary)
                    }
                }
                .padding(.horizontal, AppLayout.paneHorizontal)
                .padding(.top, AppLayout.paneVertical)
                .padding(.bottom, AppLayout.paneVertical)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    private func header(for project: Project, isCompact: Bool) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 16) {
            Text(project.name)
                .font(AppTypography.font(size: isCompact ? 52 : AppTypography.hero, weight: .regular))
                .foregroundStyle(AppTheme.textPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.8)

            if project.hasDirectory {
                Button {
                    appState.openProjectDirectoryInFinder(project.path)
                } label: {
                    Text(project.path)
                        .font(AppTypography.font(size: AppTypography.body))
                        .foregroundStyle(isPathHovering ? AppTheme.textPrimary : AppTheme.textSecondary)
                        .underline(isPathHovering, color: AppTheme.textSecondary)
                        .lineLimit(1)
                        .truncationMode(.middle)
                }
                .buttonStyle(.plain)
                .help("Open project folder in Finder")
                .accessibilityLabel("Open Project Folder in Finder")
                .onHover { hovering in
                    isPathHovering = hovering
                }
            }

            Spacer()
        }
    }

    private var chatComposer: some View {
        VStack(alignment: .leading, spacing: 0) {
            ZStack(alignment: .topLeading) {
                TextEditor(text: $appState.draftMessage)
                    .font(AppTypography.font(size: AppTypography.body))
                    .foregroundStyle(AppTheme.textPrimary)
                    .scrollContentBackground(.hidden)
                    .focused($isComposerFocused)
                    .frame(height: 44)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)

                if isDraftEmpty {
                    Text("Type your question here...")
                        .font(AppTypography.font(size: AppTypography.body))
                        .foregroundStyle(AppTheme.textMuted)
                        .padding(.top, 10)
                        .padding(.leading, 14)
                        .allowsHitTesting(false)
                }
            }
            .contentShape(Rectangle())
            .onTapGesture {
                isComposerFocused = true
            }

            if !appState.draftAttachments.isEmpty {
                Rectangle()
                    .fill(AppTheme.line)
                    .frame(height: 1)

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(appState.draftAttachments, id: \.path) { url in
                            AttachmentChip(
                                title: url.lastPathComponent,
                                removeAction: { appState.removeDraftAttachment(url) }
                            )
                            .help(url.path)
                        }
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                }
            }

            Rectangle()
                .fill(AppTheme.line)
                .frame(height: 1)

            HStack(spacing: 8) {
                ComposerIconButton(systemName: "plus") {
                    isFileImporterPresented = true
                }

                Spacer()

                Button {
                    appState.sendDraftMessage()
                } label: {
                    Image(systemName: "arrow.up")
                        .font(AppTypography.font(size: AppTypography.small, weight: .semibold))
                        .foregroundStyle(canSendDraft ? AppTheme.textPrimary : AppTheme.textMuted)
                        .frame(width: 26, height: 26)
                }
                .background(
                    Circle()
                        .fill(canSendDraft ? AppTheme.focus : AppTheme.line)
                )
                .buttonStyle(.plain)
                .disabled(!canSendDraft)
                .keyboardShortcut(.return, modifiers: [.command])
                .accessibilityLabel("Send")
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
        }
        .background(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(AppTheme.control)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(isComposerFocused ? AppTheme.focus : AppTheme.line, lineWidth: 1)
        )
        .fileImporter(
            isPresented: $isFileImporterPresented,
            allowedContentTypes: [.item],
            allowsMultipleSelection: true
        ) { result in
            if case let .success(urls) = result {
                appState.addDraftAttachments(urls)
            }
        }
    }

    private func historySection(for chats: [Chat]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Project History")
                .font(AppTypography.font(size: AppTypography.small))
                .foregroundStyle(AppTheme.textSecondary)

            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    if chats.isEmpty {
                        Text("No project history yet.")
                            .font(AppTypography.font(size: AppTypography.body))
                            .foregroundStyle(AppTheme.textMuted)
                            .padding(.top, 2)
                    } else {
                        ForEach(chats) { chat in
                            ProjectHistoryRow(chat: chat, isSelected: appState.selectedChatID == chat.id) {
                                appState.selectChat(chat.id)
                            }
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }
}

private struct ComposerIconButton: View {
    let systemName: String
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary)
                .frame(width: 24, height: 24)
                .background(
                    RoundedRectangle(cornerRadius: 6, style: .continuous)
                        .fill(isHovering ? AppTheme.hover : .clear)
                )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

private struct AttachmentChip: View {
    let title: String
    let removeAction: () -> Void

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: "doc")
                .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary)

            Text(title)
                .font(AppTypography.font(size: AppTypography.small))
                .foregroundStyle(AppTheme.textPrimary)
                .lineLimit(1)

            Button(action: removeAction) {
                Image(systemName: "xmark")
                    .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                    .foregroundStyle(AppTheme.textSecondary)
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            RoundedRectangle(cornerRadius: 7, style: .continuous)
                .fill(AppTheme.selected)
        )
    }
}

#Preview {
    ContentAreaView()
        .environmentObject(AppState())
}

private struct ProjectHistoryRow: View {
    let chat: Chat
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        SelectableHoverRow(
            isSelected: isSelected,
            horizontalPadding: AppLayout.rowHorizontal,
            verticalPadding: AppLayout.rowVertical,
            action: action
        ) {
            HStack {
                Text(chat.title)
                    .font(AppTypography.font(size: AppTypography.body))
                    .foregroundStyle(AppTheme.textPrimary)
                    .lineLimit(1)

                Spacer()

                Text(chat.createdAt, style: .date)
                    .font(AppTypography.font(size: AppTypography.body))
                    .foregroundStyle(AppTheme.textMuted)
            }
        }
    }
}
