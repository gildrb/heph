import SwiftUI

enum AppTheme {
    static let background = Color(hex: 0x060606)
    static let sidebar = Color(hex: 0x050505)
    static let rightPanel = Color(hex: 0x040404)
    static let card = Color(hex: 0x1C1C1C)
    static let chrome = Color(hex: 0x080808)
    static let line = Color(hex: 0x242424)
    static let textPrimary = Color(hex: 0xE3E3E3)
    static let textSecondary = Color(hex: 0xBABABA)
    static let textMuted = Color(hex: 0x595959)
    static let selected = Color(hex: 0x1F1F1F)
    static let hover = Color(hex: 0x242424)
    static let control = Color(hex: 0x141414)
    static let focus = Color(hex: 0x3A3A3A)
}

enum AppTypography {
    static let small: CGFloat = 13
    static let body: CGFloat = 15
    static let hero: CGFloat = 71

    static func font(size: CGFloat, weight: Font.Weight = .regular) -> Font {
        Font.custom("Inter", size: size).weight(weight)
    }
}

enum AppLayout {
    static let paneHorizontal: CGFloat = 12
    static let paneVertical: CGFloat = 16
    static let rowHorizontal: CGFloat = paneHorizontal
    static let rowVertical: CGFloat = 6
}

extension Color {
    init(hex: UInt, opacity: Double = 1) {
        let red = Double((hex >> 16) & 0xFF) / 255
        let green = Double((hex >> 8) & 0xFF) / 255
        let blue = Double(hex & 0xFF) / 255
        self.init(.sRGB, red: red, green: green, blue: blue, opacity: opacity)
    }
}
