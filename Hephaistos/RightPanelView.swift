import SwiftUI

struct RightPanelView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        Form {
            Section {
                Picker("Preset", selection: presetBinding) {
                    ForEach(appState.presets) { preset in
                        Text(preset.name).tag(preset.id)
                    }
                }
                .pickerStyle(.menu)

                MetricRow(title: "Model", value: appState.currentModelName)
                MetricRow(title: "Temperature", value: String(format: "%.1f", appState.temperature))
                Slider(value: $appState.temperature, in: 0...2, step: 0.1)
                    .controlSize(.small)

                MetricRow(title: "Max Tokens", value: "\(appState.maxTokens)")
                Stepper("", value: $appState.maxTokens, in: 256...16384, step: 256)
                    .labelsHidden()
                    .controlSize(.small)

                MetricRow(title: "Top P", value: String(format: "%.1f", appState.topP))
                Slider(value: $appState.topP, in: 0.1...1, step: 0.1)
                    .controlSize(.small)

                Toggle("Stream responses", isOn: $appState.streamResponses)
                    .toggleStyle(.switch)
                Toggle("Reasoning mode", isOn: $appState.reasoningMode)
                    .toggleStyle(.switch)
            } header: {
                sectionTitle("Advanced Parameters")
            }

            Section {
                TextEditor(text: systemPromptBinding)
                    .font(.system(size: AppTypography.body))
                    .scrollContentBackground(.hidden)
                    .background(AppTheme.control)
                    .cornerRadius(8)
                    .frame(minHeight: 140)
            } header: {
                sectionTitle("System Prompt")
            }

            Section {
                ForEach(appState.selectedProject?.excludedFiles ?? [], id: \.self) { path in
                    HStack(spacing: 8) {
                        Text(path)
                            .font(.system(size: AppTypography.body))
                            .foregroundStyle(AppTheme.textPrimary)
                            .lineLimit(1)

                        Spacer(minLength: 0)

                        Button {
                            appState.removeExcludedFile(path)
                        } label: {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(AppTheme.textMuted)
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("Remove Excluded File")
                    }
                }

                HStack(spacing: 8) {
                    TextField("Path to exclude", text: $appState.excludedFileDraft)
                        .textFieldStyle(.roundedBorder)
                    Button("Add") {
                        appState.addExcludedFile()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
            } header: {
                sectionTitle("Exclude Files")
            }
        }
        .formStyle(.grouped)
        .scrollContentBackground(.hidden)
        .padding(.horizontal, AppLayout.paneHorizontal)
        .padding(.vertical, AppLayout.paneVertical)
    }

    private var presetBinding: Binding<AIPreset.ID> {
        Binding(
            get: { appState.selectedPresetID },
            set: { appState.applyPreset($0) }
        )
    }

    private var systemPromptBinding: Binding<String> {
        Binding(
            get: { appState.selectedProject?.systemPrompt ?? "" },
            set: { appState.updateSystemPrompt($0) }
        )
    }

    private func sectionTitle(_ title: String) -> some View {
        Text(title)
            .font(.system(size: AppTypography.small))
            .foregroundStyle(AppTheme.textSecondary)
    }
}

#Preview {
    RightPanelView()
        .environmentObject(AppState())
}

private struct MetricRow: View {
    let title: String
    let value: String

    var body: some View {
        LabeledContent {
            Text(value)
                .font(.system(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)
        } label: {
            Text(title)
                .font(.system(size: AppTypography.body))
                .foregroundStyle(AppTheme.textSecondary)
        }
    }
}
