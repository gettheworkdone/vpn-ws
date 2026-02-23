import Foundation
import NetworkExtension

final class PacketTunnelProvider: NEPacketTunnelProvider {
    private var task: URLSessionWebSocketTask?

    override func startTunnel(options: [String : NSObject]?, completionHandler: @escaping (Error?) -> Void) {
        guard let proto = protocolConfiguration as? NETunnelProviderProtocol,
              let cfg = proto.providerConfiguration,
              let serverIP = cfg["serverIP"] as? String,
              let port = cfg["port"] as? String,
              let path = cfg["path"] as? String,
              let username = cfg["username"] as? String,
              let password = cfg["password"] as? String,
              let scheme = cfg["scheme"] as? String else {
            completionHandler(NSError(domain: "Lollipop", code: 1, userInfo: [NSLocalizedDescriptionKey: "Missing configuration"]))
            return
        }

        let host = serverIP.contains(":") ? "[\(serverIP)]" : serverIP
        guard let url = URL(string: "\(scheme)://\(host):\(port)/\(path)") else {
            completionHandler(NSError(domain: "Lollipop", code: 2, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"]))
            return
        }

        var request = URLRequest(url: url)
        let authRaw = "\(username):\(password)"
        let auth = Data(authRaw.utf8).base64EncodedString()
        request.setValue("Basic \(auth)", forHTTPHeaderField: "Authorization")

        let session = URLSession(configuration: .default)
        task = session.webSocketTask(with: request)
        task?.resume()

        let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: serverIP)
        let ipv4 = NEIPv4Settings(addresses: ["10.99.0.2"], subnetMasks: ["255.255.255.0"])
        ipv4.includedRoutes = [NEIPv4Route.default()]
        settings.ipv4Settings = ipv4

        setTunnelNetworkSettings(settings) { [weak self] error in
            if error == nil {
                self?.readLoop()
            }
            completionHandler(error)
        }
    }

    override func stopTunnel(with reason: NEProviderStopReason, completionHandler: @escaping () -> Void) {
        task?.cancel(with: .goingAway, reason: nil)
        task = nil
        completionHandler()
    }

    private func readLoop() {
        task?.receive { [weak self] _ in
            self?.readLoop()
        }
    }
}
