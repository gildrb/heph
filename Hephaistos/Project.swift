import Foundation

struct Project: Identifiable, Hashable {
    let id: UUID
    var name: String
    var path: String
    var history: [Chat]
    var systemPrompt: String
    var excludedFiles: [String]

    init(
        id: UUID = UUID(),
        name: String,
        path: String,
        history: [Chat] = [],
        systemPrompt: String = "",
        excludedFiles: [String] = []
    ) {
        self.id = id
        self.name = name
        self.path = path
        self.history = history
        self.systemPrompt = systemPrompt
        self.excludedFiles = excludedFiles
    }

    var hasDirectory: Bool {
        !path.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
}
