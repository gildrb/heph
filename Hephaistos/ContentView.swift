//
//  ContentView.swift
//  Hephaistos
//
//  Created by Gil Rodrigues on 17.02.26.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        MainView()
    }
}

#Preview {
    ContentView()
        .environmentObject(AppState())
}
