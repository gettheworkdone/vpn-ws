# Lollipop iOS client source

This folder contains source files for an iOS app + Packet Tunnel extension using `NetworkExtension`:

- `LollipopApp/*` – SwiftUI app (UI and profile management)
- `LollipopTunnel/*` – `NEPacketTunnelProvider` extension entry point

## Build steps (Xcode)

1. Open Xcode and create a new **iOS App** project named `Lollipop`.
2. Add a new target: **Network Extension -> Packet Tunnel** named `LollipopTunnel`.
3. Replace generated Swift files with files from this folder.
4. Set bundle IDs to match `LollipopVPNManager.swift` (`com.example.Lollipop.LollipopTunnel`) or update code.
5. In Apple Developer portal, enable:
   - Network Extensions entitlement
   - Packet Tunnel provider capability
6. In both app and extension targets, enable **Network Extensions** capability.
7. Build and run on a real iOS device (not simulator).

## Important

- The extension currently demonstrates session management and websocket auth wiring.
- To be production-ready as a Layer-2 tunnel, you need full frame <-> packet encapsulation logic compatible with `vpn-ws`.
