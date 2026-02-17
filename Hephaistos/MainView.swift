import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct MainView: View {
    @EnvironmentObject private var appState: AppState
    private let leftRatio: CGFloat = 1 / 5
    private let rightRatio: CGFloat = 1 / 7
    private let leftDefaultWidth: CGFloat = 280
    private let leftMinimumWidth: CGFloat = 250
    private let rightMinimumWidth: CGFloat = 220
    private let leftCollapsedWidth: CGFloat = 72
    private let leftCompactThreshold: CGFloat = 118
    private let minimumMainWidth: CGFloat = 80
    private let workspaceBarHeightRegular: CGFloat = 34
    private let workspaceBarHeightCompact: CGFloat = 30
    @State private var leftSidebarWidth: CGFloat = 280
    @State private var leftSidebarDragStartWidth: CGFloat?

    var body: some View {
        GeometryReader { proxy in
            let isCompact = proxy.size.width < 1200 || proxy.size.height < 760
            let workspaceBarHeight = isCompact ? workspaceBarHeightCompact : workspaceBarHeightRegular
            let requestedLeftWidth = clampedLeftSidebarWidth(
                leftSidebarWidth,
                totalWidth: proxy.size.width,
                rightSidebarCollapsed: appState.isRightSidebarCollapsed
            )
            let widths = panelWidths(
                totalWidth: proxy.size.width,
                requestedLeftWidth: requestedLeftWidth,
                rightSidebarCollapsed: appState.isRightSidebarCollapsed
            )
            let sidebarWidth = widths.left
            let rightPanelWidth = widths.right
            let isLeftSidebarCompact = sidebarWidth <= leftCompactThreshold

            VStack(spacing: 0) {
                workspaceTopBar(
                    sidebarWidth: sidebarWidth,
                    rightPanelWidth: rightPanelWidth,
                    rightSidebarCollapsed: appState.isRightSidebarCollapsed,
                    workspaceBarHeight: workspaceBarHeight
                )

                Rectangle()
                    .fill(AppTheme.line)
                    .frame(height: 1)

                HStack(spacing: 0) {
                    SidebarView(
                        isCompact: isLeftSidebarCompact
                    )
                        .frame(width: sidebarWidth)
                        .frame(maxHeight: .infinity)
                        .background(
                            AppTheme.sidebar
                                .overlay(.ultraThinMaterial.opacity(0.08))
                        )

                    sidebarResizeDivider(
                        totalWidth: proxy.size.width,
                        currentSidebarWidth: sidebarWidth
                    )

                    ContentAreaView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(
                            AppTheme.background
                                .overlay(.ultraThinMaterial.opacity(0.03))
                        )

                    if !appState.isRightSidebarCollapsed {
                        Rectangle()
                            .fill(AppTheme.line)
                            .frame(width: 1)

                        RightPanelView()
                            .frame(width: rightPanelWidth)
                            .frame(maxHeight: .infinity)
                            .background(
                                AppTheme.rightPanel
                                    .overlay(.ultraThinMaterial.opacity(0.08))
                            )
                            .transition(.move(edge: .trailing).combined(with: .opacity))
                    }
                }
            }
            .onAppear {
                leftSidebarWidth = max(leftDefaultWidth, proxy.size.width * leftRatio)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AppTheme.background)
        .ignoresSafeArea(.container, edges: .top)
        .overlay {
            if appState.isSpotlightSearchPresented {
                SpotlightSearchOverlay(isPresented: $appState.isSpotlightSearchPresented)
                    .environmentObject(appState)
                    .transition(.opacity)
                    .zIndex(10)
            }
        }
        .sheet(isPresented: $appState.showSettings) {
            SettingsView()
                .environmentObject(appState)
                .frame(minWidth: 560, minHeight: 420)
        }
    }

    private func workspaceTopBar(
        sidebarWidth: CGFloat,
        rightPanelWidth: CGFloat,
        rightSidebarCollapsed: Bool,
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
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .frame(height: workspaceBarHeight)

            if !rightSidebarCollapsed {
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
        .overlay(alignment: .trailing) {
            RightSidebarToggleButton(isCollapsed: appState.isRightSidebarCollapsed) {
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
        ScrollViewReader { scrollProxy in
            ScrollView(.horizontal, showsIndicators: true) {
                HStack(spacing: 0) {
                    ForEach(appState.openProjectTabs) { project in
                        ProjectTabItem(
                            project: project,
                            isSelected: appState.selectedProjectID == project.id,
                            isPinned: appState.isProjectTabPinned(project.id),
                            height: workspaceBarHeight,
                            onSelect: { appState.selectProject(project.id) },
                            onClose: { appState.closeProjectTab(project.id) },
                            onTogglePin: { appState.toggleProjectTabPin(project.id) },
                            onCopyPath: { appState.copyProjectPath(project.path) },
                            onCopyPathLink: { appState.copyProjectPathLink(project.path) }
                        )
                        .id(project.id)

                        if project.id != appState.openProjectTabs.last?.id {
                            Rectangle()
                                .fill(AppTheme.line)
                                .frame(width: 1, height: workspaceBarHeight)
                        }
                    }
                }
            }
            .onAppear {
                scrollTabsToSelected(using: scrollProxy)
            }
            .onChange(of: appState.openProjectTabIDs) { _, _ in
                scrollTabsToSelected(using: scrollProxy)
            }
            .onChange(of: appState.selectedProjectID) { _, _ in
                scrollTabsToSelected(using: scrollProxy)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func scrollTabsToSelected(using scrollProxy: ScrollViewProxy) {
        let targetTabID = appState.selectedProjectID ?? appState.openProjectTabs.last?.id
        guard let targetTabID else { return }

        DispatchQueue.main.async {
            withAnimation(.easeInOut(duration: 0.2)) {
                scrollProxy.scrollTo(targetTabID, anchor: .trailing)
            }
        }
    }

    private func panelWidths(
        totalWidth: CGFloat,
        requestedLeftWidth: CGFloat,
        rightSidebarCollapsed: Bool
    ) -> (left: CGFloat, right: CGFloat) {
        var leftWidth = clampedLeftSidebarWidth(
            requestedLeftWidth,
            totalWidth: totalWidth,
            rightSidebarCollapsed: rightSidebarCollapsed
        )
        var rightWidth = preferredRightPanelWidth(totalWidth: totalWidth, rightSidebarCollapsed: rightSidebarCollapsed)

        let dividerCount: CGFloat = rightSidebarCollapsed ? 1 : 2
        let adaptiveMainMinimum: CGFloat = totalWidth < 1200 ? 140 : minimumMainWidth
        let maxSidebarSpace = max(totalWidth - dividerCount - adaptiveMainMinimum, 0)

        let overflow = leftWidth + rightWidth - maxSidebarSpace
        if overflow > 0 {
            let rightReduction = min(rightWidth, overflow)
            rightWidth -= rightReduction

            let remainingOverflow = overflow - rightReduction
            if remainingOverflow > 0 {
                leftWidth = max(leftCollapsedWidth, leftWidth - remainingOverflow)
            }
        }

        return (leftWidth, rightWidth)
    }

    private func preferredRightPanelWidth(totalWidth: CGFloat, rightSidebarCollapsed: Bool) -> CGFloat {
        let adaptiveRightMinimum = totalWidth < 1200 ? 170 : rightMinimumWidth
        return rightSidebarCollapsed ? 0 : max(totalWidth * rightRatio, adaptiveRightMinimum)
    }

    private func clampedLeftSidebarWidth(
        _ proposedWidth: CGFloat,
        totalWidth: CGFloat,
        rightSidebarCollapsed: Bool
    ) -> CGFloat {
        let dividerCount: CGFloat = rightSidebarCollapsed ? 1 : 2
        let adaptiveMainMinimum: CGFloat = totalWidth < 1200 ? 140 : minimumMainWidth
        let maxWidth = max(
            leftCollapsedWidth,
            totalWidth - dividerCount - adaptiveMainMinimum - (rightSidebarCollapsed ? 0 : rightMinimumWidth)
        )
        return min(max(proposedWidth, leftCollapsedWidth), maxWidth)
    }

    private func sidebarResizeDivider(totalWidth: CGFloat, currentSidebarWidth: CGFloat) -> some View {
        Rectangle()
            .fill(AppTheme.line)
            .frame(width: 1)
            .overlay {
                Color.clear
                    .frame(width: 8)
                    .contentShape(Rectangle())
                    .onHover { hovering in
#if canImport(AppKit)
                        if hovering {
                            NSCursor.resizeLeftRight.set()
                        } else {
                            NSCursor.arrow.set()
                        }
#endif
                    }
                    .gesture(
                        DragGesture(minimumDistance: 0)
                            .onChanged { value in
                                if leftSidebarDragStartWidth == nil {
                                    leftSidebarDragStartWidth = currentSidebarWidth
                                }

                                guard let dragStartWidth = leftSidebarDragStartWidth else { return }
                                let proposed = dragStartWidth + value.translation.width
                                leftSidebarWidth = clampedLeftSidebarWidth(
                                    proposed,
                                    totalWidth: totalWidth,
                                    rightSidebarCollapsed: appState.isRightSidebarCollapsed
                                )
                            }
                            .onEnded { _ in
                                leftSidebarDragStartWidth = nil
                            }
                    )
            }
            .zIndex(1)
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
                .font(AppTypography.font(size: AppTypography.icon, weight: .medium))
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
    let isCollapsed: Bool
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            Image(systemName: "sidebar.right")
                .font(AppTypography.font(size: AppTypography.icon, weight: .medium))
                .foregroundStyle(AppTheme.textSecondary)
                .frame(width: 28, height: 28)
                .background(
                    RoundedRectangle(cornerRadius: 7, style: .continuous)
                        .fill(!isCollapsed || isHovering ? AppTheme.hover : .clear)
                )
        }
        .buttonStyle(.plain)
        .accessibilityLabel(isCollapsed ? "Expand Right Sidebar" : "Collapse Right Sidebar")
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

private struct ProjectTabItem: View {
    let project: Project
    let isSelected: Bool
    let isPinned: Bool
    let height: CGFloat
    let onSelect: () -> Void
    let onClose: () -> Void
    let onTogglePin: () -> Void
    let onCopyPath: () -> Void
    let onCopyPathLink: () -> Void
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

            if isPinned {
                Image(systemName: "pin.fill")
                    .font(AppTypography.font(size: AppTypography.icon, weight: .medium))
                    .foregroundStyle(AppTheme.textSecondary)
                    .frame(width: 16, height: 16)
                    .padding(.trailing, AppLayout.paneHorizontal)
                    .allowsHitTesting(false)
            } else {
                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(AppTypography.font(size: AppTypography.icon, weight: .medium))
                        .foregroundStyle(AppTheme.textSecondary)
                        .frame(width: 16, height: 16)
                        .background(
                            RoundedRectangle(cornerRadius: 4, style: .continuous)
                                .fill(isHovering ? AppTheme.hover.opacity(0.5) : Color.clear)
                        )
                }
                .buttonStyle(.plain)
                .padding(.trailing, AppLayout.paneHorizontal)
                .opacity(isHovering ? 1 : 0)
                .allowsHitTesting(isHovering)
            }
        }
        .onHover { hovering in
            isHovering = hovering
        }
        .contextMenu {
            Button {
                onCopyPath()
            } label: {
                Label("Copy Path", systemImage: "doc.on.doc")
            }

            Button {
                onCopyPathLink()
            } label: {
                Label("Copy Path as Link", systemImage: "link")
            }

            Divider()

            Button {
                onTogglePin()
            } label: {
                Label(
                    isPinned ? "Unpin Tab" : "Pin Tab",
                    systemImage: isPinned ? "pin.slash" : "pin"
                )
            }

            Divider()

            Button {
                onClose()
            } label: {
                Label("Close Tab", systemImage: "xmark")
            }
        }
    }
}
