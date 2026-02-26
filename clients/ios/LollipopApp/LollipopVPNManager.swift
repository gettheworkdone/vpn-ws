import Foundation
import NetworkExtension

final class LollipopVPNManager: ObservableObject {
    static let shared = LollipopVPNManager()

    @Published var serverIP = "203.0.113.10"
    @Published var port = "443"
    @Published var path = "cucumber"
    @Published var username = "cucumber"
    @Published var password = "potato"
    @Published var protocolMode = "wss"
    @Published var statusMessage = "Idle"
    @Published var isConnected = false

    private var manager: NETunnelProviderManager?

    private init() {
        loadProfile()
    }

    func loadProfile() {
        NETunnelProviderManager.loadAllFromPreferences { [weak self] managers, error in
            DispatchQueue.main.async {
                if let error {
                    self?.statusMessage = "Load error: \(error.localizedDescription)"
                    return
                }

                if let saved = managers?.first {
                    self?.manager = saved
                    self?.statusMessage = "Profile loaded"
                    self?.isConnected = saved.connection.status == .connected || saved.connection.status == .connecting
                } else {
                    self?.manager = NETunnelProviderManager()
                    self?.statusMessage = "No saved profile"
                }
            }
        }
    }

    func saveProfile() {
        guard let manager else {
            statusMessage = "Manager unavailable"
            return
        }

        let proto = NETunnelProviderProtocol()
        proto.providerBundleIdentifier = "com.example.Lollipop.LollipopTunnel"
        proto.serverAddress = serverIP
        proto.username = username

        proto.providerConfiguration = [
            "serverIP": serverIP as NSString,
            "port": port as NSString,
            "path": path as NSString,
            "username": username as NSString,
            "password": password as NSString,
            "scheme": protocolMode as NSString,
        ]

        manager.localizedDescription = "Lollipop"
        manager.protocolConfiguration = proto
        manager.isEnabled = true

        manager.saveToPreferences { [weak self] error in
            DispatchQueue.main.async {
                if let error {
                    self?.statusMessage = "Save error: \(error.localizedDescription)"
                    return
                }
                self?.statusMessage = "Profile saved"
            }
        }
    }

    func toggleConnection() {
        guard let manager, let session = manager.connection as? NETunnelProviderSession else {
            statusMessage = "Invalid tunnel session"
            return
        }

        switch session.status {
        case .connected, .connecting:
            session.stopVPNTunnel()
            isConnected = false
            statusMessage = "Disconnected"
        default:
            do {
                try session.startVPNTunnel()
                isConnected = true
                statusMessage = "Connecting..."
            } catch {
                statusMessage = "Connect error: \(error.localizedDescription)"
            }
        }
    }
}
