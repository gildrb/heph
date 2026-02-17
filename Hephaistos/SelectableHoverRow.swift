import SwiftUI

struct SelectableHoverRow<Content: View>: View {
    let isSelected: Bool
    let horizontalPadding: CGFloat
    let verticalPadding: CGFloat
    let action: () -> Void
    @ViewBuilder let content: () -> Content
    @State private var isHovering = false

    init(
        isSelected: Bool,
        horizontalPadding: CGFloat = AppLayout.rowHorizontal,
        verticalPadding: CGFloat = AppLayout.rowVertical,
        action: @escaping () -> Void,
        @ViewBuilder content: @escaping () -> Content
    ) {
        self.isSelected = isSelected
        self.horizontalPadding = horizontalPadding
        self.verticalPadding = verticalPadding
        self.action = action
        self.content = content
    }

    var body: some View {
        content()
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, horizontalPadding)
            .padding(.vertical, verticalPadding)
        .contentShape(Rectangle())
        .background(backgroundColor)
        .onTapGesture(perform: action)
        .onHover { hovering in
            isHovering = hovering
        }
        .accessibilityAddTraits(.isButton)
    }

    private var backgroundColor: Color {
        if isSelected {
            return AppTheme.selected
        }
        return isHovering ? AppTheme.hover : .clear
    }
}
