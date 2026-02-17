import Foundation
import SwiftUI
import Combine
#if canImport(AppKit)
import AppKit
#endif

@MainActor
final class AppState: ObservableObject {
    private struct NavigationState: Equatable {
        let projectID: Project.ID?
        let chatID: Chat.ID?
    }

    @Published var projects: [Project]
    @Published var openProjectTabIDs: [Project.ID]
    @Published var pinnedProjectTabIDs: [Project.ID]
    @Published var selectedProjectID: Project.ID?
    @Published var selectedChatID: Chat.ID?

    @Published var sidebarQuery = ""
    @Published var expandedProjectIDs: Set<Project.ID>
    @Published var isRightSidebarCollapsed = false
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
    private var backStack: [NavigationState] = []
    private var forwardStack: [NavigationState] = []
    private let normalChatsFolderName = "Chats"

    init() {
        let availablePresets = Self.defaultPresets
        let defaultPreset = availablePresets[0]
        let starterProjects = Self.defaultProjects

        projects = starterProjects
        openProjectTabIDs = []
        pinnedProjectTabIDs = []
        selectedProjectID = nil
        selectedChatID = nil
        expandedProjectIDs = []

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
        return filterChats(in: project, query: sidebarQuery)
    }

    var hasSidebarQuery: Bool {
        !sidebarQuery.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var sidebarProjects: [Project] {
        let query = sidebarQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        let matchingProjects: [Project]

        if hasSidebarQuery {
            matchingProjects = projects.filter { project in
                project.name.localizedCaseInsensitiveContains(query)
                || !filterChats(in: project, query: query).isEmpty
            }
        } else {
            matchingProjects = projects
        }

        return orderedSidebarProjects(matchingProjects)
    }

    private func orderedSidebarProjects(_ source: [Project]) -> [Project] {
        guard let chatsIndex = source.firstIndex(where: { !$0.hasDirectory && $0.name == normalChatsFolderName }) else {
            return source
        }

        var ordered = source
        let chatsProject = ordered.remove(at: chatsIndex)
        ordered.append(chatsProject)
        return ordered
    }

    func chats(for project: Project) -> [Chat] {
        filterChats(in: project, query: sidebarQuery)
    }

    func isProjectExpanded(_ projectID: Project.ID) -> Bool {
        expandedProjectIDs.contains(projectID)
    }

    func toggleProjectExpansion(_ projectID: Project.ID) {
        if expandedProjectIDs.contains(projectID) {
            expandedProjectIDs.remove(projectID)
        } else {
            expandedProjectIDs.insert(projectID)
        }
    }

    func expandProject(_ projectID: Project.ID) {
        expandedProjectIDs.insert(projectID)
    }

    var currentModelName: String {
        presets.first(where: { $0.id == selectedPresetID })?.model ?? "Unknown"
    }

    var canNavigateBack: Bool {
        !backStack.isEmpty
    }

    var canNavigateForward: Bool {
        !forwardStack.isEmpty
    }

    func selectProject(_ projectID: Project.ID) {
        let firstChatID = projects.first(where: { $0.id == projectID })?.history.first?.id
        navigate(to: NavigationState(projectID: projectID, chatID: firstChatID), recording: true)
    }

    func isProjectTabPinned(_ projectID: Project.ID) -> Bool {
        pinnedProjectTabIDs.contains(projectID)
    }

    func toggleProjectTabPin(_ projectID: Project.ID) {
        if isProjectTabPinned(projectID) {
            unpinProjectTab(projectID)
        } else {
            pinProjectTab(projectID)
        }
    }

    func pinProjectTab(_ projectID: Project.ID) {
        guard openProjectTabIDs.contains(projectID) else { return }
        guard !pinnedProjectTabIDs.contains(projectID) else { return }
        pinnedProjectTabIDs.insert(projectID, at: 0)
        normalizeOpenTabOrder()
    }

    func unpinProjectTab(_ projectID: Project.ID) {
        guard pinnedProjectTabIDs.contains(projectID) else { return }
        pinnedProjectTabIDs.removeAll(where: { $0 == projectID })
        normalizeOpenTabOrder()
    }

    func closeProjectTab(_ projectID: Project.ID) {
        guard let closingIndex = openProjectTabIDs.firstIndex(of: projectID) else { return }
        openProjectTabIDs.remove(at: closingIndex)
        pinnedProjectTabIDs.removeAll(where: { $0 == projectID })

        guard selectedProjectID == projectID else { return }

        if openProjectTabIDs.isEmpty {
            navigate(to: NavigationState(projectID: nil, chatID: nil), recording: true)
            return
        }

        let fallbackIndex = min(closingIndex, openProjectTabIDs.count - 1)
        let fallbackID = openProjectTabIDs[fallbackIndex]
        let fallbackChatID = projects.first(where: { $0.id == fallbackID })?.history.first?.id
        navigate(to: NavigationState(projectID: fallbackID, chatID: fallbackChatID), recording: true)
    }

    func selectChat(_ chatID: Chat.ID) {
        navigate(to: NavigationState(projectID: selectedProjectID, chatID: chatID), recording: true)
    }

    func selectChat(_ chatID: Chat.ID, in projectID: Project.ID) {
        expandedProjectIDs.insert(projectID)
        navigate(to: NavigationState(projectID: projectID, chatID: chatID), recording: true)
    }

    func createProject() {
        let baseName = "New Project"
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
        navigate(to: NavigationState(projectID: newProject.id, chatID: nil), recording: true)
    }

    func newChat() {
        if selectedProjectID == nil {
            let chatsProjectID = ensureNormalChatsProject()
            selectProject(chatsProjectID)
        }

        var newChatID: Chat.ID?
        updateSelectedProject { project in
            let chatNumber = project.history.count + 1
            let chat = Chat(
                title: chatNumber == 1 ? "New Chat" : "New Chat \(chatNumber)",
                message: "",
                createdAt: .now
            )
            project.history.insert(chat, at: 0)
            newChatID = chat.id
        }

        if let selectedProjectID {
            expandedProjectIDs.insert(selectedProjectID)
        }

        if let newChatID {
            navigate(to: NavigationState(projectID: selectedProjectID, chatID: newChatID), recording: true)
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
        if selectedProjectID == nil {
            let chatsProjectID = ensureNormalChatsProject()
            selectProject(chatsProjectID)
        }

        let trimmed = draftMessage.trimmingCharacters(in: .whitespacesAndNewlines)
        let attachments = draftAttachments.map(\.path)
        guard !trimmed.isEmpty || !attachments.isEmpty else { return }

        var newChatID: Chat.ID?
        updateSelectedProject { project in
            let title = draftTitle(message: trimmed, attachments: attachments)
            let chat = Chat(title: title, message: trimmed, attachments: attachments, createdAt: .now)
            project.history.insert(chat, at: 0)
            newChatID = chat.id
        }

        if let newChatID {
            navigate(to: NavigationState(projectID: selectedProjectID, chatID: newChatID), recording: true)
        }

        draftMessage = ""
        draftAttachments.removeAll()
    }

    func navigateBack() {
        guard let previous = backStack.popLast() else { return }
        forwardStack.append(currentNavigationState)
        apply(navigationState: normalized(navigationState: previous))
    }

    func navigateForward() {
        guard let next = forwardStack.popLast() else { return }
        backStack.append(currentNavigationState)
        apply(navigationState: normalized(navigationState: next))
    }

    func toggleRightPanel() {
        withAnimation(.easeInOut(duration: 0.2)) {
            isRightSidebarCollapsed.toggle()
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
        let trimmedPath = path.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedPath.isEmpty else { return }
        let fileManager = FileManager.default
        let projectURL = URL(fileURLWithPath: trimmedPath)
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

    func copyProjectPath(_ path: String) {
        let trimmedPath = path.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedPath.isEmpty else { return }
        copyToPasteboard(trimmedPath)
    }

    func copyProjectPathLink(_ path: String) {
        let trimmedPath = path.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedPath.isEmpty else { return }
        let fileURLString = URL(fileURLWithPath: trimmedPath).absoluteString
        copyToPasteboard(fileURLString)
    }

    private func updateSelectedProject(_ mutation: (inout Project) -> Void) {
        guard let selectedProjectID, let index = projects.firstIndex(where: { $0.id == selectedProjectID }) else {
            return
        }
        mutation(&projects[index])
    }

    private var currentNavigationState: NavigationState {
        NavigationState(projectID: selectedProjectID, chatID: selectedChatID)
    }

    private func navigate(to targetState: NavigationState, recording: Bool) {
        let normalizedTarget = normalized(navigationState: targetState)
        let currentState = currentNavigationState
        guard normalizedTarget != currentState else { return }

        if recording {
            backStack.append(currentState)
            forwardStack.removeAll()
        }

        apply(navigationState: normalizedTarget)
    }

    private func normalized(navigationState: NavigationState) -> NavigationState {
        guard
            let projectID = navigationState.projectID,
            let project = projects.first(where: { $0.id == projectID })
        else {
            return NavigationState(projectID: nil, chatID: nil)
        }

        let resolvedChatID: Chat.ID?
        if let chatID = navigationState.chatID, project.history.contains(where: { $0.id == chatID }) {
            resolvedChatID = chatID
        } else {
            resolvedChatID = project.history.first?.id
        }

        return NavigationState(projectID: projectID, chatID: resolvedChatID)
    }

    private func apply(navigationState: NavigationState) {
        guard let projectID = navigationState.projectID else {
            selectedProjectID = nil
            selectedChatID = nil
            return
        }

        if !openProjectTabIDs.contains(projectID) {
            openProjectTabIDs.append(projectID)
            normalizeOpenTabOrder()
        }

        selectedProjectID = projectID
        selectedChatID = navigationState.chatID
    }

    private func normalizeOpenTabOrder() {
        let openTabSet = Set(openProjectTabIDs)
        pinnedProjectTabIDs = pinnedProjectTabIDs.filter { openTabSet.contains($0) }
        let pinnedTabSet = Set(pinnedProjectTabIDs)
        let unpinnedTabIDs = openProjectTabIDs.filter { !pinnedTabSet.contains($0) }
        openProjectTabIDs = pinnedProjectTabIDs + unpinnedTabIDs
    }

    private func copyToPasteboard(_ string: String) {
#if canImport(AppKit)
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(string, forType: .string)
#endif
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

    private var normalChatsProjectID: Project.ID? {
        projects.first(where: { !$0.hasDirectory && $0.name == normalChatsFolderName })?.id
    }

    private func ensureNormalChatsProject() -> Project.ID {
        if let existingID = normalChatsProjectID {
            return existingID
        }

        let chatsProject = Project(
            name: normalChatsFolderName,
            path: "",
            history: [],
            systemPrompt: "",
            excludedFiles: []
        )
        projects.append(chatsProject)
        return chatsProject.id
    }

    private func filterChats(in project: Project, query: String) -> [Chat] {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return project.history }
        let queryTerms = trimmed
            .split(whereSeparator: \.isWhitespace)
            .map { String($0) }
        return project.history.filter { chat in
            let searchableFields = [chat.title, chat.message] + chat.attachments
            return queryTerms.allSatisfy { term in
                searchableFields.contains(where: { $0.localizedCaseInsensitiveContains(term) })
            }
        }
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
        []
    }
}
