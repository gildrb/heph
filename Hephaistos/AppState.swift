import Foundation
import SwiftUI
import Combine
#if canImport(AppKit)
import AppKit
#endif

@MainActor
final class AppState: ObservableObject {
    @Published var projects: [Project]
    @Published var openProjectTabIDs: [Project.ID]
    @Published var selectedProjectID: Project.ID?
    @Published var selectedChatID: Chat.ID?

    @Published var isSearchVisible = false
    @Published var sidebarQuery = ""
    @Published var isLeftSidebarCollapsed = false
    @Published var showRightPanel = true
    @Published var showSettings = false

    @Published var draftMessage = ""
    @Published var draftAttachments: [URL] = []

    @Published var presets: [AIPreset]
    @Published var selectedPresetID: AIPreset.ID
    @Published var temperature: Double
    @Published var maxTokens: Int
    @Published var topP: Double
    @Published var streamResponses = true
    @Published var reasoningMode = false

    @Published var excludedFileDraft = ""

    init() {
        let availablePresets = Self.defaultPresets
        let defaultPreset = availablePresets[0]
        let starterProjects = Self.defaultProjects

        projects = starterProjects
        openProjectTabIDs = starterProjects.map(\.id)
        selectedProjectID = starterProjects.first?.id
        selectedChatID = starterProjects.first?.history.first?.id

        presets = availablePresets
        selectedPresetID = defaultPreset.id
        temperature = defaultPreset.temperature
        maxTokens = defaultPreset.maxTokens
        topP = defaultPreset.topP
    }

    var selectedProject: Project? {
        guard let selectedProjectID else { return nil }
        return projects.first(where: { $0.id == selectedProjectID })
    }

    var selectedProjectName: String {
        selectedProject?.name ?? "Untitled"
    }

    var openProjectTabs: [Project] {
        openProjectTabIDs.compactMap { tabID in
            projects.first(where: { $0.id == tabID })
        }
    }

    var filteredChats: [Chat] {
        guard let project = selectedProject else { return [] }
        let query = sidebarQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !query.isEmpty else { return project.history }
        return project.history.filter {
            $0.title.localizedCaseInsensitiveContains(query) ||
            $0.message.localizedCaseInsensitiveContains(query) ||
            $0.attachments.contains(where: { $0.localizedCaseInsensitiveContains(query) })
        }
    }

    var currentModelName: String {
        presets.first(where: { $0.id == selectedPresetID })?.model ?? "Unknown"
    }

    func selectProject(_ projectID: Project.ID) {
        if !openProjectTabIDs.contains(projectID) {
            openProjectTabIDs.append(projectID)
        }
        selectedProjectID = projectID
        selectedChatID = projects.first(where: { $0.id == projectID })?.history.first?.id
    }

    func closeProjectTab(_ projectID: Project.ID) {
        guard let closingIndex = openProjectTabIDs.firstIndex(of: projectID) else { return }
        openProjectTabIDs.remove(at: closingIndex)

        guard selectedProjectID == projectID else { return }

        if openProjectTabIDs.isEmpty {
            selectedProjectID = nil
            selectedChatID = nil
            return
        }

        let fallbackIndex = min(closingIndex, openProjectTabIDs.count - 1)
        let fallbackID = openProjectTabIDs[fallbackIndex]
        selectedProjectID = fallbackID
        selectedChatID = projects.first(where: { $0.id == fallbackID })?.history.first?.id
    }

    func selectChat(_ chatID: Chat.ID) {
        selectedChatID = chatID
    }

    func createProject() {
        let baseName = "New Vault"
        var candidateName = baseName
        var suffix = 1

        while projects.contains(where: { $0.name == candidateName }) {
            suffix += 1
            candidateName = "\(baseName) \(suffix)"
        }

        let safeFolderName = candidateName.replacingOccurrences(of: " ", with: "-")
        let defaultPath = URL(fileURLWithPath: NSHomeDirectory())
            .appendingPathComponent("Hephaistos")
            .appendingPathComponent(safeFolderName)
            .path

        let newProject = Project(
            name: candidateName,
            path: defaultPath,
            history: [],
            systemPrompt: "",
            excludedFiles: []
        )

        projects.append(newProject)
        openProjectTabIDs.append(newProject.id)
        selectedProjectID = newProject.id
        selectedChatID = nil
    }

    func newChat() {
        updateSelectedProject { project in
            let chatNumber = project.history.count + 1
            let chat = Chat(
                title: chatNumber == 1 ? "New Chat" : "New Chat \(chatNumber)",
                message: "",
                createdAt: .now
            )
            project.history.insert(chat, at: 0)
            selectedChatID = chat.id
        }
    }

    func addDraftAttachments(_ urls: [URL]) {
        for url in urls {
            let normalized = url.standardizedFileURL
            let alreadyAttached = draftAttachments.contains {
                $0.standardizedFileURL.path == normalized.path
            }
            if !alreadyAttached {
                draftAttachments.append(normalized)
            }
        }
    }

    func removeDraftAttachment(_ url: URL) {
        let targetPath = url.standardizedFileURL.path
        draftAttachments.removeAll { $0.standardizedFileURL.path == targetPath }
    }

    func sendDraftMessage() {
        let trimmed = draftMessage.trimmingCharacters(in: .whitespacesAndNewlines)
        let attachments = draftAttachments.map(\.path)
        guard !trimmed.isEmpty || !attachments.isEmpty else { return }

        updateSelectedProject { project in
            let title = draftTitle(message: trimmed, attachments: attachments)
            let chat = Chat(title: title, message: trimmed, attachments: attachments, createdAt: .now)
            project.history.insert(chat, at: 0)
            selectedChatID = chat.id
        }

        draftMessage = ""
        draftAttachments.removeAll()
    }

    func toggleSearch() {
        isSearchVisible.toggle()
        if !isSearchVisible {
            sidebarQuery = ""
        }
    }

    func toggleLeftSidebar() {
        withAnimation(.easeInOut(duration: 0.2)) {
            isLeftSidebarCollapsed.toggle()
        }
    }

    func toggleRightPanel() {
        withAnimation(.easeInOut(duration: 0.2)) {
            showRightPanel.toggle()
        }
    }

    func applyPreset(_ presetID: AIPreset.ID) {
        guard let preset = presets.first(where: { $0.id == presetID }) else { return }
        selectedPresetID = preset.id
        temperature = preset.temperature
        maxTokens = preset.maxTokens
        topP = preset.topP
    }

    func updateSystemPrompt(_ prompt: String) {
        updateSelectedProject { project in
            project.systemPrompt = prompt
        }
    }

    func addExcludedFile() {
        let trimmed = excludedFileDraft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        updateSelectedProject { project in
            guard !project.excludedFiles.contains(trimmed) else { return }
            project.excludedFiles.append(trimmed)
        }
        excludedFileDraft = ""
    }

    func removeExcludedFile(_ path: String) {
        updateSelectedProject { project in
            project.excludedFiles.removeAll(where: { $0 == path })
        }
    }

    func openProjectDirectoryInFinder(_ path: String) {
#if canImport(AppKit)
        let fileManager = FileManager.default
        let projectURL = URL(fileURLWithPath: path)
        var isDirectory: ObjCBool = false

        if fileManager.fileExists(atPath: projectURL.path, isDirectory: &isDirectory), isDirectory.boolValue {
            NSWorkspace.shared.open(projectURL)
            return
        }

        let parentURL = projectURL.deletingLastPathComponent()
        if fileManager.fileExists(atPath: parentURL.path, isDirectory: &isDirectory), isDirectory.boolValue {
            NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: parentURL.path)
            return
        }

        NSWorkspace.shared.open(URL(fileURLWithPath: NSHomeDirectory()))
#endif
    }

    private func updateSelectedProject(_ mutation: (inout Project) -> Void) {
        guard let selectedProjectID, let index = projects.firstIndex(where: { $0.id == selectedProjectID }) else {
            return
        }
        mutation(&projects[index])
    }

    private func draftTitle(message: String, attachments: [String]) -> String {
        if !message.isEmpty {
            return String(message.prefix(42))
        }
        if let firstAttachment = attachments.first {
            return URL(fileURLWithPath: firstAttachment).lastPathComponent
        }
        return "New Chat"
    }
}

private extension AppState {
    static var defaultPresets: [AIPreset] {
        [
            AIPreset(name: "Balanced", model: "gpt-5", temperature: 0.7, maxTokens: 4096, topP: 1.0),
            AIPreset(name: "Precise", model: "gpt-5", temperature: 0.2, maxTokens: 2048, topP: 0.8),
            AIPreset(name: "Creative", model: "gpt-5", temperature: 1.1, maxTokens: 4096, topP: 1.0)
        ]
    }

    static var defaultProjects: [Project] {
        return [
            Project(
                name: "MfI-1",
                path: "/Users/gildrb/Hephaestus/MfI-1",
                history: [],
                systemPrompt: "You are a concise project assistant.",
                excludedFiles: ["build/", ".git/"]
            ),
            Project(
                name: "AKIDS-1",
                path: "/Users/gildrb/Hephaestus/AKIDS-1",
                history: [],
                systemPrompt: "Prefer practical, tested coding steps.",
                excludedFiles: ["DerivedData/"]
            ),
            Project(
                name: "GdP",
                path: "/Users/gildrb/Hephaestus/GdP",
                history: [],
                systemPrompt: "Use system-level architecture language where relevant.",
                excludedFiles: []
            )
        ]
    }
}
