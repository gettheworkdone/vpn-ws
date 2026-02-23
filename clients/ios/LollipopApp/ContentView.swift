import SwiftUI

struct ContentView: View {
    @StateObject private var vpnManager = LollipopVPNManager.shared

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
                    Toggle("Use TLS (wss)", isOn: $vpnManager.useTLS)
                }

                Section("Authentication") {
                    TextField("Username", text: $vpnManager.username)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    SecureField("Password", text: $vpnManager.password)
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
        }
    }
}
