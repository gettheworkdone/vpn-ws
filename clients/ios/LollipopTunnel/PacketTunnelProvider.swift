import Foundation
import NetworkExtension

final class PacketTunnelProvider: NEPacketTunnelProvider {
    private var websocketTask: URLSessionWebSocketTask?
    private var httpPollTimer: Timer?
    private let session = URLSession(configuration: .default)

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

        let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: serverIP)
        let ipv4 = NEIPv4Settings(addresses: ["10.99.0.2"], subnetMasks: ["255.255.255.0"])
        ipv4.includedRoutes = [NEIPv4Route.default()]
        settings.ipv4Settings = ipv4

        setTunnelNetworkSettings(settings) { [weak self] error in
            if let error {
                completionHandler(error)
                return
            }

            if scheme == "https2" {
                self?.startHTTPS2Polling(serverIP: serverIP, port: port, path: path, username: username, password: password)
            } else {
                self?.startWebSocket(serverIP: serverIP, port: port, path: path, username: username, password: password)
            }
            completionHandler(nil)
        }
    }

    private func startWebSocket(serverIP: String, port: String, path: String, username: String, password: String) {
        let host = serverIP.contains(":") ? "[\(serverIP)]" : serverIP
        guard let url = URL(string: "wss://\(host):\(port)/\(path)") else { return }

        var request = URLRequest(url: url)
        let authRaw = "\(username):\(password)"
        request.setValue("Basic \(Data(authRaw.utf8).base64EncodedString())", forHTTPHeaderField: "Authorization")

        websocketTask = session.webSocketTask(with: request)
        websocketTask?.resume()
        wsReadLoop()
    }

    private func wsReadLoop() {
        websocketTask?.receive { [weak self] _ in
            self?.wsReadLoop()
        }
    }

    private func startHTTPS2Polling(serverIP: String, port: String, path: String, username: String, password: String) {
        let host = serverIP.contains(":") ? "[\(serverIP)]" : serverIP
        guard let recvURL = URL(string: "https://\(host):\(port)/\(path)/recv") else { return }
        let auth = "Basic \(Data("\(username):\(password)".utf8).base64EncodedString())"

        httpPollTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            var req = URLRequest(url: recvURL)
            req.setValue(auth, forHTTPHeaderField: "Authorization")
            req.setValue(username, forHTTPHeaderField: "X-Client-Id")
            self.session.dataTask(with: req).resume()
        }
    }

    override func stopTunnel(with reason: NEProviderStopReason, completionHandler: @escaping () -> Void) {
        websocketTask?.cancel(with: .goingAway, reason: nil)
        websocketTask = nil
        httpPollTimer?.invalidate()
        httpPollTimer = nil
        completionHandler()
    }
}
