//
//  HephaistosApp.swift
//  Hephaistos
//
//  Created by Gil Rodrigues on 17.02.26.
//

import SwiftUI

@main
struct HephaistosApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .environment(\.font, AppTypography.font(size: AppTypography.body))
                .preferredColorScheme(.dark)
        }
        .windowStyle(.hiddenTitleBar)
    }
}
