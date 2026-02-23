import Foundation
import NetworkExtension

final class LollipopVPNManager: ObservableObject {
    static let shared = LollipopVPNManager()

    @Published var serverIP = "203.0.113.10"
    @Published var port = "443"
    @Published var path = "vpn"
    @Published var username = "lollipop"
    @Published var password = ""
    @Published var useTLS = true
    @Published var statusMessage = "Idle"
    @Published var isConnected = false

    private let manager = NETunnelProviderManager()

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
                    self?.applyManager(saved)
                    self?.statusMessage = "Profile loaded"
                } else {
                    self?.statusMessage = "No saved profile"
                }
            }
        }
    }

    private func applyManager(_ saved: NETunnelProviderManager) {
        manager.localizedDescription = saved.localizedDescription
        manager.protocolConfiguration = saved.protocolConfiguration
        manager.isEnabled = saved.isEnabled
        manager.onDemandRules = saved.onDemandRules
        manager.isOnDemandEnabled = saved.isOnDemandEnabled
        if let session = manager.connection as? NETunnelProviderSession {
            isConnected = session.status == .connected || session.status == .connecting
        }
    }

    func saveProfile() {
        let proto = NETunnelProviderProtocol()
        proto.providerBundleIdentifier = "com.example.Lollipop.LollipopTunnel"
        proto.serverAddress = serverIP
        proto.username = username

        var config: [String: NSObject] = [
            "serverIP": serverIP as NSString,
            "port": port as NSString,
            "path": path as NSString,
            "username": username as NSString,
            "password": password as NSString,
            "scheme": (useTLS ? "wss" : "ws") as NSString,
        ]
        proto.providerConfiguration = config

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
        guard let session = manager.connection as? NETunnelProviderSession else {
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
