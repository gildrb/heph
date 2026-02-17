import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct MainView: View {
    @EnvironmentObject private var appState: AppState
    private let leftRatio: CGFloat = 1 / 5
    private let rightRatio: CGFloat = 1 / 7
    private let leftMinimumWidth: CGFloat = 250
    private let leftCollapsedWidth: CGFloat = 56
    private let rightMinimumWidth: CGFloat = 190
    private let minimumMainWidth: CGFloat = 80
    private let trafficLightsOffset: CGFloat = 72
    private let workspaceBarHeightRegular: CGFloat = 34
    private let workspaceBarHeightCompact: CGFloat = 30

    var body: some View {
        GeometryReader { proxy in
            let isCompact = proxy.size.width < 1200 || proxy.size.height < 760
            let workspaceBarHeight = isCompact ? workspaceBarHeightCompact : workspaceBarHeightRegular
            let widths = panelWidths(
                totalWidth: proxy.size.width,
                rightPanelVisible: appState.showRightPanel,
                leftSidebarCollapsed: appState.isLeftSidebarCollapsed
            )
            let sidebarWidth = widths.left
            let rightPanelWidth = widths.right

            VStack(spacing: 0) {
                workspaceTopBar(
                    sidebarWidth: sidebarWidth,
                    rightPanelWidth: rightPanelWidth,
                    workspaceBarHeight: workspaceBarHeight
                )

                Rectangle()
                    .fill(AppTheme.line)
                    .frame(height: 1)

                HStack(spacing: 0) {
                    SidebarView()
                        .frame(width: sidebarWidth)
                        .background(
                            AppTheme.sidebar
                                .overlay(.ultraThinMaterial.opacity(0.08))
                        )

                    Rectangle()
                        .fill(AppTheme.line)
                        .frame(width: 1)

                    ContentAreaView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(
                            AppTheme.background
                                .overlay(.ultraThinMaterial.opacity(0.03))
                        )

                    if appState.showRightPanel {
                        Rectangle()
                            .fill(AppTheme.line)
                            .frame(width: 1)

                        RightPanelView()
                            .frame(width: rightPanelWidth)
                            .background(
                                AppTheme.rightPanel
                                    .overlay(.ultraThinMaterial.opacity(0.08))
                            )
                            .transition(.move(edge: .trailing).combined(with: .opacity))
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AppTheme.background)
        .ignoresSafeArea(.container, edges: .top)
        .sheet(isPresented: $appState.showSettings) {
            SettingsView()
                .environmentObject(appState)
                .frame(minWidth: 560, minHeight: 420)
        }
    }

    private func workspaceTopBar(
        sidebarWidth: CGFloat,
        rightPanelWidth: CGFloat,
        workspaceBarHeight: CGFloat
    ) -> some View {
        HStack(spacing: 0) {
            Color.clear
                .frame(width: sidebarWidth, height: workspaceBarHeight)

            Rectangle()
                .fill(AppTheme.line)
                .frame(width: 1, height: workspaceBarHeight)

            HStack(spacing: 0) {
                topBarNavigation(workspaceBarHeight: workspaceBarHeight)

                Rectangle()
                    .fill(AppTheme.line)
                    .frame(width: 1, height: workspaceBarHeight)

                mainProjectTabs(workspaceBarHeight: workspaceBarHeight)

                Spacer(minLength: 0)
            }
            .frame(height: workspaceBarHeight)

            if appState.showRightPanel {
                Rectangle()
                    .fill(AppTheme.line)
                    .frame(width: 1, height: workspaceBarHeight)

                Color.clear
                    .frame(width: rightPanelWidth, height: workspaceBarHeight)
            }
        }
        .frame(height: workspaceBarHeight)
        .background(
            AppTheme.chrome
                .overlay(.regularMaterial.opacity(0.08))
        )
        .overlay(alignment: .leading) {
            LeftSidebarToggleButton(isCollapsed: appState.isLeftSidebarCollapsed) {
                appState.toggleLeftSidebar()
            }
            .padding(.leading, AppLayout.paneHorizontal + trafficLightsOffset)
        }
        .overlay(alignment: .trailing) {
            RightSidebarToggleButton(isExpanded: appState.showRightPanel) {
                appState.toggleRightPanel()
            }
            .padding(.trailing, AppLayout.paneHorizontal)
        }
    }

    private func topBarNavigation(workspaceBarHeight: CGFloat) -> some View {
        HStack(spacing: 6) {
            NavigationArrowButton(
                systemName: "arrow.left",
                isEnabled: appState.canNavigateBack,
                accessibilityLabel: "Navigate Back",
                action: { appState.navigateBack() }
            )

            NavigationArrowButton(
                systemName: "arrow.right",
                isEnabled: appState.canNavigateForward,
                accessibilityLabel: "Navigate Forward",
                action: { appState.navigateForward() }
            )
        }
        .padding(.horizontal, AppLayout.paneHorizontal)
        .frame(height: workspaceBarHeight)
    }

    private func mainProjectTabs(workspaceBarHeight: CGFloat) -> some View {
        HStack(spacing: 0) {
            ForEach(appState.openProjectTabs) { project in
                ProjectTabItem(
                    project: project,
                    isSelected: appState.selectedProjectID == project.id,
                    height: workspaceBarHeight,
                    onSelect: { appState.selectProject(project.id) },
                    onClose: { appState.closeProjectTab(project.id) }
                )

                if project.id != appState.openProjectTabs.last?.id {
                    Rectangle()
                        .fill(AppTheme.line)
                        .frame(width: 1, height: workspaceBarHeight)
                }
            }
        }
    }

    private func panelWidths(
        totalWidth: CGFloat,
        rightPanelVisible: Bool,
        leftSidebarCollapsed: Bool
    ) -> (left: CGFloat, right: CGFloat) {
        let adaptiveLeftMinimum = totalWidth < 1200 ? 200 : leftMinimumWidth
        let adaptiveRightMinimum = totalWidth < 1200 ? 150 : rightMinimumWidth
        var leftWidth = leftSidebarCollapsed ? leftCollapsedWidth : max(totalWidth * leftRatio, adaptiveLeftMinimum)
        var rightWidth: CGFloat = rightPanelVisible ? max(totalWidth * rightRatio, adaptiveRightMinimum) : 0

        let dividerCount: CGFloat = rightPanelVisible ? 2 : 1
        let adaptiveMainMinimum: CGFloat = totalWidth < 1200 ? 140 : minimumMainWidth
        let maxSidebarSpace = max(totalWidth - dividerCount - adaptiveMainMinimum, 0)
        let sidebarSpace = leftWidth + rightWidth

        if sidebarSpace > maxSidebarSpace, sidebarSpace > 0 {
            let scale = maxSidebarSpace / sidebarSpace
            leftWidth *= scale
            rightWidth *= scale
        }

        return (leftWidth, rightWidth)
    }
}

private struct LeftSidebarToggleButton: View {
    let isCollapsed: Bool
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            Image(systemName: "sidebar.left")
                .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary)
                .frame(width: 28, height: 28)
                .background(
                    RoundedRectangle(cornerRadius: 7, style: .continuous)
                        .fill(!isCollapsed || isHovering ? AppTheme.hover : .clear)
                )
        }
        .buttonStyle(.plain)
        .accessibilityLabel(isCollapsed ? "Expand Left Sidebar" : "Collapse Left Sidebar")
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

private struct NavigationArrowButton: View {
    let systemName: String
    let isEnabled: Bool
    let accessibilityLabel: String
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(AppTypography.font(size: AppTypography.body, weight: .medium))
                .foregroundStyle(isEnabled ? AppTheme.textSecondary : AppTheme.textMuted)
                .frame(width: 24, height: 24)
                .background(
                    RoundedRectangle(cornerRadius: 6, style: .continuous)
                        .fill(isEnabled && isHovering ? AppTheme.hover : .clear)
                )
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled)
        .accessibilityLabel(accessibilityLabel)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

#Preview {
    MainView()
        .environmentObject(AppState())
}

private struct RightSidebarToggleButton: View {
    let isExpanded: Bool
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            Image(systemName: "sidebar.right")
                .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary)
                .frame(width: 28, height: 28)
                .background(
                    RoundedRectangle(cornerRadius: 7, style: .continuous)
                        .fill(isExpanded || isHovering ? AppTheme.hover : .clear)
                )
        }
        .buttonStyle(.plain)
        .accessibilityLabel(isExpanded ? "Collapse Right Sidebar" : "Expand Right Sidebar")
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

private struct ProjectTabItem: View {
    let project: Project
    let isSelected: Bool
    let height: CGFloat
    let onSelect: () -> Void
    let onClose: () -> Void
    @State private var isHovering = false

    var body: some View {
        ZStack(alignment: .trailing) {
            Button(action: onSelect) {
                HStack(spacing: 8) {
                    Text(project.name)
                        .font(AppTypography.font(size: AppTypography.body))
                        .foregroundStyle(isSelected ? AppTheme.textPrimary : AppTheme.textSecondary)
                        .lineLimit(1)
                    Spacer(minLength: 0)
                    Color.clear
                        .frame(width: 16, height: 16)
                }
                .padding(.horizontal, AppLayout.paneHorizontal)
                .frame(height: height)
                .frame(minWidth: 102, maxWidth: 220, alignment: .leading)
                .background(
                    isSelected
                        ? AppTheme.selected
                        : (isHovering ? AppTheme.hover.opacity(0.6) : Color.clear)
                )
            }
            .buttonStyle(.plain)
            .help(project.path)

            Button(action: onClose) {
                Image(systemName: "xmark")
                    .font(AppTypography.font(size: AppTypography.small, weight: .medium))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(width: 16, height: 16)
                    .background(
                        RoundedRectangle(cornerRadius: 4, style: .continuous)
                            .fill(AppTheme.hover.opacity(0.5))
                    )
            }
            .buttonStyle(.plain)
            .padding(.trailing, AppLayout.paneHorizontal)
            .opacity(isHovering ? 1 : 0)
            .allowsHitTesting(isHovering)
        }
        .onHover { hovering in
            isHovering = hovering
        }
    }
}
