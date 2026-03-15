# Lollipop

Lollipop is an IP-only deployable tunneling system with two client-selectable transports:

1. **WSS mode (true VPN mode)**: Layer-2 TAP tunnel over secure websocket (`wss`).
2. **HTTPS2 mode (experimental)**: request/response payload channel over HTTPS.

Server side is Linux (Ubuntu) and Docker-based. Client side is Linux, macOS, Windows and iOS.

---

## 1. Overview

### 1.1 Architecture

- **Server runtime**: `lollipop-server` behind nginx inside Docker.
- **Client runtime**:
  - Linux: GUI + CLI
  - macOS: GUI
  - Windows: GUI (no CLI requirement)
  - iOS: GUI app + Packet Tunnel extension
- **Security**: self-signed certificate generated for IP SAN; no domain required.

### 1.2 What is “true VPN” here?

Use **WSS + TAP** mode and route default traffic through the tunnel interface.

- Linux/macOS: route control done by client-side network settings (documented below).
- iOS: route control done in `PacketTunnelProvider` network settings.
- HTTPS2 mode is experimental and not equivalent to full L2 VPN transport.

---

## 2. Repository map (file-by-file purpose)

### Core C runtime

- `src/main.c` - server entry/event loop.
- `src/client.c` - native client (WSS transport, auth, headers JSON handling).
- `src/io.c` - frame forwarding logic.
- `src/tuntap.c` - TAP creation and TAP I/O.
- `src/socket.c` - IPv4/IPv6/unix socket helpers.
- `src/ssl.c` - TLS support for client.
- `src/uwsgi.c` - nginx/uWSGI integration + handshake response.
- `src/vpn-ws.h` - shared structs and declarations.

### Build/runtime packaging

- `Makefile` - builds `lollipop-server` and `lollipop-client` (+ compatibility copies).
- `docker/Dockerfile` - full server image.
- `docker/entrypoint.sh` - startup + cert generation + process launch.
- `docker/nginx.conf.template` - nginx routes for WSS and HTTPS2 modes.

### HTTPS2 experimental transport

- `server_h2/https2_payload_server.py` - queue-based send/recv service.
- `clients/https2_payload_cli.py` - one-shot send/recv client.
- `clients/https2_payload_poll.py` - long-poll receive loop.
- `clients/utls/main.go` - uTLS HTTP/2 client (browser-like TLS fingerprint).

### Desktop GUI clients

- `clients/lollipop_gui.py` - main desktop GUI.
- `clients/linux/lollipop.sh` - Linux GUI launcher.
- `clients/macos/lollipop.command` - macOS GUI launcher.
- `clients/windows/lollipop.bat` - Windows GUI launcher.

### iOS client

- `clients/ios/LollipopApp/LollipopApp.swift` - app entry.
- `clients/ios/LollipopApp/ContentView.swift` - app UI.
- `clients/ios/LollipopApp/LollipopVPNManager.swift` - profile/config management.
- `clients/ios/LollipopTunnel/PacketTunnelProvider.swift` - tunnel extension logic.
- `clients/ios/README.md` - exhaustive iOS build/deploy steps.

### Config templates

- `config/browser_headers.example.json` - full headers template for request customization.

---

## 3. Installation and dependencies

## 3.1 Server side (Ubuntu only)

### Install Docker on Ubuntu VPS

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
```

### Build server image

```bash
git clone <your-fork-or-repo-url> lollipop
cd lollipop
docker build -t lollipop-server -f docker/Dockerfile .
```

### Run server container (IP-only)

```bash
docker run -d \
  --name lollipop-server \
  -p 80:80 -p 443:443 \
  -e SERVER_IPV4=203.0.113.10 \
  -e SERVER_IPV6=2001:db8::10 \
  -v lollipop-certs:/data/certs \
  lollipop-server
```

### Generated certificate paths

- `/data/certs/cucumber.crt`
- `/data/certs/potato.key`

Copy public cert:

```bash
docker cp lollipop-server:/data/certs/cucumber.crt ./cucumber.crt
```

---

## 3.2 Linux client dependencies

### GUI mode

```bash
sudo apt update
sudo apt install -y python3 python3-pip
python3 -m pip install --user PyQt5 requests
```

### CLI mode (Linux only)

```bash
sudo apt install -y build-essential make gcc libssl-dev
make clean
make
```

---

## 3.3 macOS client dependencies

- Install Python 3 (Homebrew or python.org)
- Install GUI dependencies:

```bash
python3 -m pip install PyQt5 requests
```

- Install TAP driver if using true WSS VPN mode.

---

## 3.4 Windows client dependencies (GUI only)

- Install Python 3.11+ (enable “Add python to PATH”).
- Install dependencies:

```powershell
py -m pip install PyQt5 requests
```

- Build binaries once (on Windows with build toolchain) or use provided/prebuilt `lollipop-client.exe` in your packaging flow.
- Launch GUI via `clients\windows\lollipop.bat`.

> Windows usage is GUI-first in this project; terminal operation is not required.

---

## 3.5 iOS client dependencies

- macOS + Xcode 15+
- Apple Developer account with NetworkExtension capability
- Real iPhone/iPad for deployment

Detailed click-by-click instructions are in `clients/ios/README.md`.

---

## 4. Common client options (same concept across all GUIs)

All GUI clients expose the same conceptual fields:

- Server IP
- Port
- Path
- Username
- Password
- Protocol selector: `wss` / `https2`
- Headers JSON config
- Connect button
- Disconnect button

Desktop GUI also includes optional cert path and HTTPS2 send payload helper.

---

## 5. Headers JSON config (only JSON, no manual header flags)

Use `config/browser_headers.example.json` as your template and edit values.

Linux CLI usage (Linux only):

```bash
sudo ./lollipop-client \
  --user cucumber \
  --password potato \
  --headers-json ./config/browser_headers.example.json \
  vpn-ws0 wss://203.0.113.10/cucumber
```

Desktop GUI / iOS:
- choose/import this JSON from GUI.

---

## 6. End-to-end usage

## 6.1 Linux GUI

```bash
./clients/linux/lollipop.sh
```

### Linux GUI visual map

- **Top fields**: server IP/port/path/user/password
- **Protocol selector**: `wss` or `https2`
- **Headers JSON**: file path + browse button
- **Buttons**:
  - `Connect`
  - `Disconnect`
  - `Send HTTPS2 payload`
- **Logs panel**: connection and runtime messages

## 6.2 macOS GUI

```bash
./clients/macos/lollipop.command
```

Visual layout and controls are the same as Linux GUI.

## 6.3 Windows GUI

```bat
clients\windows\lollipop.bat
```

Visual layout and controls are the same as Linux GUI.

## 6.4 iOS GUI

Follow `clients/ios/README.md` and run app on device.

### iOS visual map

- **Server section**: IP, port, path, protocol segmented control
- **Authentication section**: username/password
- **Headers JSON section**: import button + JSON editor text area
- **Actions**: Save Profile, Connect/Disconnect
- **Status section**: current state/errors

---

## 7. True VPN routing behavior

## 7.1 Linux full-traffic example

After WSS connection:

```bash
sudo ip link set vpn-ws0 up
sudo ip addr add 10.99.0.2/24 dev vpn-ws0
sudo ip route replace default dev vpn-ws0
```

To revert:

```bash
sudo dhclient
```

## 7.2 macOS full-traffic example

After WSS connection:

```bash
sudo ifconfig tap0 10.99.0.3 10.99.0.1 up
sudo route change default 10.99.0.1
```

To revert default route back to your normal gateway.

## 7.3 iOS

Route behavior is controlled by `NEPacketTunnelNetworkSettings` in `PacketTunnelProvider.swift`.

---

## 8. Build iOS app from scratch

Use `clients/ios/README.md`.

That guide includes exact Xcode UI flow:
- what to click,
- which template to choose,
- which bundle identifiers to set,
- where to add capabilities,
- how to deploy to physical iPhone.

---

## 9. Testing checklist (from this README flow)

- Build native binaries.
- Validate Python client scripts syntax.
- Validate Go uTLS client build.
- Localhost HTTPS2 send/recv smoke test.

(See “Tests run” section below for executed commands.)

---

## 10. Tests run for this revision

Executed in Linux environment:

1. `make clean && make`
2. `python3 -m py_compile clients/lollipop_gui.py clients/https2_payload_cli.py clients/https2_payload_poll.py server_h2/https2_payload_server.py`
3. `cd clients/utls && go build .`
4. Installed required Python deps for local tests:
   - `python3 -m pip install --user requests flask`
5. Localhost integration test:
   - `python3 server_h2/https2_payload_server.py`
   - `python3 clients/https2_payload_cli.py --base http://127.0.0.1:18080 --client-id test1 --send "hello-local"`
   - `python3 clients/https2_payload_cli.py --base http://127.0.0.1:18080 --client-id test1 --recv`
   - verified payload round-trip.
