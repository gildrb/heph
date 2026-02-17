import Foundation

struct AIPreset: Identifiable, Hashable {
    let id: UUID
    var name: String
    var model: String
    var temperature: Double
    var maxTokens: Int
    var topP: Double

    init(
        id: UUID = UUID(),
        name: String,
        model: String,
        temperature: Double,
        maxTokens: Int,
        topP: Double
    ) {
        self.id = id
        self.name = name
        self.model = model
        self.temperature = temperature
        self.maxTokens = maxTokens
        self.topP = topP
    }
}
