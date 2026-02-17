import SwiftUI

struct SpotlightSearchOverlay: View {
    @EnvironmentObject private var appState: AppState
    @Binding var isPresented: Bool
    @State private var query = ""
    @FocusState private var isSearchFieldFocused: Bool

    var body: some View {
        ZStack {
            Color.black.opacity(0.5)
                .ignoresSafeArea()
                .onTapGesture {
                    dismiss()
                }

            VStack(spacing: 0) {
                searchHeader

                Rectangle()
                    .fill(AppTheme.line)
                    .frame(height: 1)

                searchResults
            }
            .frame(maxWidth: SpotlightLayout.maxWidth)
            .background(
                RoundedRectangle(cornerRadius: SpotlightLayout.cornerRadius, style: .continuous)
                    .fill(AppTheme.card.opacity(0.96))
            )
            .overlay(
                RoundedRectangle(cornerRadius: SpotlightLayout.cornerRadius, style: .continuous)
                    .stroke(AppTheme.line, lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.35), radius: 24, y: 12)
            .padding(.horizontal, SpotlightLayout.outerHorizontalPadding)
            .padding(.top, SpotlightLayout.topPadding)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        }
        .onAppear {
            DispatchQueue.main.async {
                isSearchFieldFocused = true
            }
        }
        .onExitCommand {
            dismiss()
        }
    }

    private var searchHeader: some View {
        HStack(spacing: 10) {
            TextField("Search chats...", text: $query)
                .textFieldStyle(.plain)
                .font(AppTypography.font(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)
                .focused($isSearchFieldFocused)

            Button {
                dismiss()
            } label: {
                Image(systemName: "xmark")
                    .font(AppTypography.font(size: 18, weight: .medium))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(width: 24, height: 24)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Close Search")
        }
        .padding(.horizontal, SpotlightLayout.headerHorizontalPadding)
        .padding(.vertical, SpotlightLayout.headerVerticalPadding)
    }

    private var searchResults: some View {
        let groups = groupedSearchResults

        return ScrollView(.vertical, showsIndicators: false) {
            VStack(alignment: .leading, spacing: 0) {
                SpotlightActionRow(systemName: "square.and.pencil", title: "New Chat") {
                    appState.newChat()
                    dismiss()
                }
                .padding(.top, 6)

                ForEach(groups) { group in
                    Text(group.title)
                        .font(AppTypography.font(size: AppTypography.category, weight: .medium))
                        .foregroundStyle(AppTheme.textMuted)
                        .padding(.horizontal, SpotlightLayout.headerHorizontalPadding)
                        .padding(.top, 22)
                        .padding(.bottom, 8)

                    ForEach(group.entries) { result in
                        SpotlightChatRow(result: result) {
                            appState.selectChat(result.chat.id, in: result.projectID)
                            dismiss()
                        }
                    }
                }

                if groups.isEmpty {
                    Text("No chats found.")
                        .font(AppTypography.font(size: AppTypography.body))
                        .foregroundStyle(AppTheme.textMuted)
                        .padding(.horizontal, SpotlightLayout.headerHorizontalPadding)
                        .padding(.vertical, 16)
                }
            }
            .padding(.bottom, 14)
        }
        .frame(maxHeight: SpotlightLayout.maxResultsHeight)
    }

    private var groupedSearchResults: [SearchResultGroup] {
        let results = appState.searchChats(query: query)
        let calendar = Calendar.current
        let grouped = Dictionary(grouping: results) { result in
            calendar.startOfDay(for: result.chat.createdAt)
        }

        return grouped.keys
            .sorted(by: >)
            .map { date in
                let entries = (grouped[date] ?? []).sorted { left, right in
                    left.chat.createdAt > right.chat.createdAt
                }
                return SearchResultGroup(date: date, title: dayLabel(for: date), entries: entries)
            }
    }

    private func dayLabel(for date: Date) -> String {
        let calendar = Calendar.current
        if calendar.isDateInToday(date) {
            return "Today"
        }
        if calendar.isDateInYesterday(date) {
            return "Yesterday"
        }

        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .none
        return formatter.string(from: date)
    }

    private func dismiss() {
        isPresented = false
    }
}

private struct SpotlightActionRow: View {
    let systemName: String
    let title: String
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                Image(systemName: systemName)
                    .font(AppTypography.font(size: AppTypography.icon, weight: .semibold))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(width: 16)

                Text(title)
                    .font(AppTypography.font(size: AppTypography.body))
                    .foregroundStyle(AppTheme.textPrimary)
                    .lineLimit(1)

                Spacer(minLength: 0)
            }
            .padding(.horizontal, SpotlightLayout.headerHorizontalPadding)
            .padding(.vertical, AppLayout.rowVertical + 3)
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

private struct SpotlightChatRow: View {
    let result: AppState.ChatSearchResult
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                Image(systemName: "bubble.left")
                    .font(AppTypography.font(size: AppTypography.icon, weight: .medium))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(width: 16)

                Text(result.chat.title)
                    .font(AppTypography.font(size: AppTypography.body))
                    .foregroundStyle(AppTheme.textPrimary)
                    .lineLimit(1)

                Spacer(minLength: 0)

                Text(result.projectName)
                    .font(AppTypography.font(size: AppTypography.body))
                    .foregroundStyle(AppTheme.textMuted)
                    .lineLimit(1)
            }
            .padding(.horizontal, SpotlightLayout.headerHorizontalPadding)
            .padding(.vertical, AppLayout.rowVertical + 3)
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

private struct SearchResultGroup: Identifiable {
    let date: Date
    let title: String
    let entries: [AppState.ChatSearchResult]

    var id: Date { date }
}

private enum SpotlightLayout {
    static let maxWidth: CGFloat = 1100
    static let maxResultsHeight: CGFloat = 650
    static let cornerRadius: CGFloat = 28
    static let topPadding: CGFloat = 80
    static let outerHorizontalPadding: CGFloat = 72
    static let headerHorizontalPadding: CGFloat = 48
    static let headerVerticalPadding: CGFloat = 20
}
