import SwiftUI

struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var appState: AppState
    @State private var saveHistory = true
    @State private var openLastProject = true

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Settings")
                .font(AppTypography.font(size: AppTypography.body, weight: .semibold))
                .foregroundStyle(AppTheme.textPrimary)

            Toggle("Save local history", isOn: $saveHistory)
            Toggle("Open last project on launch", isOn: $openLastProject)
            Toggle("Show right panel by default", isOn: $appState.showRightPanel)

            Spacer()

            HStack {
                Spacer()
                Button("Done") {
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(.horizontal, AppLayout.paneHorizontal)
        .padding(.vertical, AppLayout.paneVertical)
        .background(AppTheme.background)
        .font(AppTypography.font(size: AppTypography.body))
    }
}

#Preview {
    SettingsView()
        .environmentObject(AppState())
}
