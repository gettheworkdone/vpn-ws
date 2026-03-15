# Lollipop iOS build guide (ultra-detailed, click-by-click)

This guide starts from a blank Mac and ends with Lollipop running on a real iPhone.

---

## 1) Prerequisites

1. macOS with Xcode 15+ installed from App Store.
2. Paid Apple Developer account.
3. Your Apple team has NetworkExtension capability enabled.
4. Real iPhone connected by USB.

---

## 2) Create base app project in Xcode

1. Open **Xcode**.
2. Click **Create a new Xcode project**.
3. In template chooser:
   - Platform: **iOS**
   - Template: **App**
   - Click **Next**.
4. Fill project form exactly:
   - Product Name: `Lollipop`
   - Team: **your Apple team**
   - Organization Identifier: e.g. `com.yourcompany`
   - Interface: `SwiftUI`
   - Language: `Swift`
   - Use Core Data: `No`
   - Include Tests: optional
5. Click **Next**, choose folder, click **Create**.

---

## 3) Add Packet Tunnel extension target

1. In left panel, click project root (`Lollipop`).
2. In center pane, under **Targets**, click **+**.
3. In template window:
   - iOS -> Network Extension -> **Packet Tunnel**.
4. Click **Next**.
5. Product Name: `LollipopTunnel`.
6. Finish creation.
7. If prompted “Activate scheme?” click **Activate**.

---

## 4) Configure signing and bundle IDs

### 4.1 App target

1. Select target **Lollipop**.
2. Open tab **Signing & Capabilities**.
3. Check **Automatically manage signing**.
4. Team: choose your Apple team.
5. Bundle Identifier: `com.yourcompany.Lollipop`.

### 4.2 Extension target

1. Select target **LollipopTunnel**.
2. Open **Signing & Capabilities**.
3. Check **Automatically manage signing**.
4. Team: choose same Apple team.
5. Bundle Identifier: `com.yourcompany.Lollipop.LollipopTunnel`.

### 4.3 Match bundle ID in code

Open `LollipopVPNManager.swift` and set:

```swift
proto.providerBundleIdentifier = "com.yourcompany.Lollipop.LollipopTunnel"
```

It must exactly equal extension bundle identifier.

---

## 5) Add capabilities

Do this for both targets (`Lollipop` and `LollipopTunnel`):

1. Open **Signing & Capabilities**.
2. Click **+ Capability**.
3. Add **Network Extensions**.
4. For extension target choose Packet Tunnel type where prompted.

---

## 6) Replace generated source files with repository files

### 6.1 App target files (Target Membership = Lollipop)

- `clients/ios/LollipopApp/LollipopApp.swift`
- `clients/ios/LollipopApp/ContentView.swift`
- `clients/ios/LollipopApp/LollipopVPNManager.swift`

### 6.2 Extension target files (Target Membership = LollipopTunnel)

- `clients/ios/LollipopTunnel/PacketTunnelProvider.swift`

How to add:
1. Right-click folder in Xcode -> **Add Files to "Lollipop"...**
2. Select file.
3. Ensure correct **Target Membership** checkbox is ticked.
4. Remove old generated duplicates if needed.

---

## 7) Prepare certificate on iPhone

1. On server host, copy cert from Docker:
   - `/data/certs/cucumber.crt`
2. Send `cucumber.crt` to iPhone (AirDrop/email/files).
3. Open file on iPhone and install profile.
4. iPhone: **Settings -> General -> About -> Certificate Trust Settings**.
5. Enable trust for `cucumber.crt`.

---

## 8) First build and deploy to device

1. Connect iPhone to Mac with cable.
2. In Xcode top bar, select scheme **Lollipop** and your iPhone device.
3. Press **Cmd+B** (build).
4. Press **Cmd+R** (run).
5. On first run, iPhone may ask to trust developer profile:
   - Settings -> General -> VPN & Device Management -> Trust your developer app.
6. Launch Lollipop app on iPhone.

---

## 9) iOS app UI (visual explanation)

Screen sections:

1. **Server**
   - Server IP
   - Port
   - Path
   - Protocol segmented control (`wss`, `https2`)
2. **Authentication**
   - Username
   - Password
3. **Headers JSON**
   - Import headers JSON file button
   - Text editor to view/edit JSON directly
4. **Actions**
   - Save Profile
   - Connect / Disconnect
5. **Status**
   - Human-readable current state/error

---

## 10) Connect flow

1. Fill Server IP/Port/Path.
2. Fill Username/Password.
3. Choose protocol:
   - `wss` for true VPN mode
   - `https2` for payload mode
4. Import headers JSON (optional) or edit in text area.
5. Tap **Save Profile**.
6. Tap **Connect**.
7. Confirm VPN icon appears if tunnel is active.

---

## 11) Troubleshooting

- **Save error / load error**: signing/provisioning problem.
- **Invalid tunnel session**: bundle ID mismatch or extension not signed.
- **TLS errors**: cert not trusted on device.
- **No traffic**: check server path and credentials.
- **Extension not launching**: NetworkExtension capability missing on either target.

---

## 12) Keep app safe to disable

To turn off quickly:

- Tap **Disconnect** in app, or
- iOS Settings -> VPN -> disable connection.

This restores normal network behavior.
