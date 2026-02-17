import Foundation

struct Chat: Identifiable, Hashable {
    let id: UUID
    var title: String
    var message: String
    var attachments: [String]
    var createdAt: Date

    init(
        id: UUID = UUID(),
        title: String,
        message: String,
        attachments: [String] = [],
        createdAt: Date = .now
    ) {
        self.id = id
        self.title = title
        self.message = message
        self.attachments = attachments
        self.createdAt = createdAt
    }
}
