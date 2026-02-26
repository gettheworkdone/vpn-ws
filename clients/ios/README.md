# Lollipop iOS client source

Contains iOS app + Packet Tunnel extension with protocol switcher support:

- `wss` mode
- `https2` mode

Files:
- `LollipopApp/*` – SwiftUI UI + profile management
- `LollipopTunnel/*` – `NEPacketTunnelProvider`

## Build

1. Create iOS app project in Xcode named `Lollipop`.
2. Add Packet Tunnel extension target `LollipopTunnel`.
3. Replace generated files with this folder files.
4. Set bundle IDs (`com.example.Lollipop.LollipopTunnel`) or adjust code.
5. Enable NetworkExtension capability in app + extension.
6. Build on real device with Apple developer profile.

## Protocol switcher

In app UI, select protocol with segmented control:
- `wss`
- `https2`

Extension routes behavior based on selected scheme in provider configuration.
