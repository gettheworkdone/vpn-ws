import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @StateObject private var vpnManager = LollipopVPNManager.shared
    @State private var showFileImporter = false

    var body: some View {
        NavigationView {
            Form {
                Section("Server") {
                    TextField("Server IP (IPv4 or IPv6)", text: $vpnManager.serverIP)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    TextField("Port", text: $vpnManager.port)
                        .keyboardType(.numberPad)
                    TextField("Path", text: $vpnManager.path)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()

                    Picker("Protocol", selection: $vpnManager.protocolMode) {
                        Text("wss").tag("wss")
                        Text("https2").tag("https2")
                    }
                    .pickerStyle(.segmented)
                }

                Section("Authentication") {
                    TextField("Username", text: $vpnManager.username)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    SecureField("Password", text: $vpnManager.password)
                }

                Section("Headers JSON") {
                    Button("Import headers JSON file") {
                        showFileImporter = true
                    }
                    TextEditor(text: $vpnManager.headersJSONText)
                        .frame(minHeight: 120)
                        .font(.system(.footnote, design: .monospaced))
                }

                Section("Actions") {
                    Button("Save Profile") {
                        vpnManager.saveProfile()
                    }
                    Button(vpnManager.isConnected ? "Disconnect" : "Connect") {
                        vpnManager.toggleConnection()
                    }
                }

                Section("Status") {
                    Text(vpnManager.statusMessage)
                        .font(.footnote)
                }
            }
            .navigationTitle("Lollipop")
            .fileImporter(
                isPresented: $showFileImporter,
                allowedContentTypes: [UTType.json],
                allowsMultipleSelection: false
            ) { result in
                switch result {
                case .success(let urls):
                    if let first = urls.first {
                        vpnManager.importHeadersFile(from: first)
                    }
                case .failure(let err):
                    vpnManager.statusMessage = "Import error: \(err.localizedDescription)"
                }
            }
        }
    }
}
