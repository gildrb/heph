import SwiftUI

struct RightPanelView: View {
    @EnvironmentObject private var appState: AppState

    private var excludedFiles: [String] {
        appState.selectedProject?.excludedFiles ?? []
    }

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(alignment: .leading, spacing: AppLayout.paneVertical) {
                advancedParametersSection
                systemPromptSection
                excludeFilesSection
            }
            .padding(.horizontal, AppLayout.paneHorizontal)
            .padding(.vertical, AppLayout.paneVertical)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var advancedParametersSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionTitle("Advanced Parameters")

            VStack(alignment: .leading, spacing: 0) {
                HStack(spacing: 8) {
                    Text("Preset")
                        .font(AppTypography.font(size: AppTypography.body))
                        .foregroundStyle(AppTheme.textSecondary)
                    Spacer(minLength: 8)
                    Picker("", selection: presetBinding) {
                        ForEach(appState.presets) { preset in
                            Text(preset.name).tag(preset.id)
                        }
                    }
                    .labelsHidden()
                    .pickerStyle(.menu)
                    .frame(maxWidth: 140, alignment: .trailing)
                }
                .padding(.horizontal, AppLayout.paneHorizontal)
                .padding(.vertical, 10)

                Divider().overlay(AppTheme.line)

                VStack(alignment: .leading, spacing: 8) {
                    MetricRow(title: "Model", value: appState.currentModelName)
                }
                .padding(.horizontal, AppLayout.paneHorizontal)
                .padding(.vertical, 10)

                Divider().overlay(AppTheme.line)

                VStack(alignment: .leading, spacing: 8) {
                    MetricRow(title: "Temperature", value: String(format: "%.1f", appState.temperature))
                    Slider(value: $appState.temperature, in: 0...2, step: 0.1)
                        .controlSize(.small)
                }
                .padding(.horizontal, AppLayout.paneHorizontal)
                .padding(.vertical, 10)

                Divider().overlay(AppTheme.line)

                Stepper(value: $appState.maxTokens, in: 256...16384, step: 256) {
                    MetricRow(title: "Max Tokens", value: "\(appState.maxTokens)")
                }
                .controlSize(.small)
                .padding(.horizontal, AppLayout.paneHorizontal)
                .padding(.vertical, 10)

                Divider().overlay(AppTheme.line)

                VStack(alignment: .leading, spacing: 8) {
                    MetricRow(title: "Top P", value: String(format: "%.1f", appState.topP))
                    Slider(value: $appState.topP, in: 0.1...1, step: 0.1)
                        .controlSize(.small)
                }
                .padding(.horizontal, AppLayout.paneHorizontal)
                .padding(.vertical, 10)

                Divider().overlay(AppTheme.line)

                Toggle("Stream responses", isOn: $appState.streamResponses)
                    .toggleStyle(.switch)
                    .font(AppTypography.font(size: AppTypography.body))
                    .padding(.horizontal, AppLayout.paneHorizontal)
                    .padding(.vertical, 10)

                Divider().overlay(AppTheme.line)

                Toggle("Reasoning mode", isOn: $appState.reasoningMode)
                    .toggleStyle(.switch)
                    .font(AppTypography.font(size: AppTypography.body))
                    .padding(.horizontal, AppLayout.paneHorizontal)
                    .padding(.vertical, 10)
            }
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(AppTheme.control)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(AppTheme.line, lineWidth: 1)
            )
        }
    }

    private var systemPromptSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionTitle("System Prompt")

            TextEditor(text: systemPromptBinding)
                .font(AppTypography.font(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)
                .scrollContentBackground(.hidden)
                .padding(8)
                .frame(minHeight: 140)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(AppTheme.control)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(AppTheme.line, lineWidth: 1)
                )
        }
    }

    private var excludeFilesSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionTitle("Exclude Files")

            VStack(alignment: .leading, spacing: 0) {
                if excludedFiles.isEmpty {
                    Text("No excluded paths.")
                        .font(AppTypography.font(size: AppTypography.body))
                        .foregroundStyle(AppTheme.textMuted)
                        .padding(.horizontal, AppLayout.paneHorizontal)
                        .padding(.vertical, 10)
                } else {
                    ForEach(Array(excludedFiles.enumerated()), id: \.element) { index, path in
                        HStack(spacing: 8) {
                            Text(path)
                                .font(AppTypography.font(size: AppTypography.body))
                                .foregroundStyle(AppTheme.textPrimary)
                                .lineLimit(1)

                            Spacer(minLength: 0)

                            Button {
                                appState.removeExcludedFile(path)
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                                    .font(AppTypography.font(size: AppTypography.icon))
                                    .foregroundStyle(AppTheme.textMuted)
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("Remove Excluded File")
                        }
                        .padding(.horizontal, AppLayout.paneHorizontal)
                        .padding(.vertical, 10)

                        if index < excludedFiles.count - 1 {
                            Divider().overlay(AppTheme.line)
                        }
                    }
                }

                Divider().overlay(AppTheme.line)

                HStack(spacing: 8) {
                    TextField("Path to exclude", text: $appState.excludedFileDraft)
                        .textFieldStyle(.roundedBorder)
                        .font(AppTypography.font(size: AppTypography.body))

                    Button("Add") {
                        appState.addExcludedFile()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
                .padding(.horizontal, AppLayout.paneHorizontal)
                .padding(.vertical, 10)
            }
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(AppTheme.control)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(AppTheme.line, lineWidth: 1)
            )
        }
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
            .font(AppTypography.font(size: AppTypography.category))
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
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text(title)
                .font(AppTypography.font(size: AppTypography.body))
                .foregroundStyle(AppTheme.textSecondary)
                .lineLimit(1)
                .minimumScaleFactor(0.85)
            Spacer(minLength: 8)
            Text(value)
                .font(AppTypography.font(size: AppTypography.body))
                .foregroundStyle(AppTheme.textPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.85)
        }
    }
}
