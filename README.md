# Lollipop

Lollipop is a transport toolkit with two modes:

1. **True VPN mode (recommended):** `wss` + TAP (Layer-2 tunnel), using `lollipop-server` and `lollipop-client`.
2. **HTTPS2 payload mode (experimental):** request/response payload transport over HTTPS.

Everything works with **IP-only server setup** (no domain required).

---

## 1) Project file map (what each file does)

### Core C implementation

- `src/main.c` - server event loop entry point.
- `src/client.c` - native client entry point and websocket handshake logic.
- `src/io.c` - frame forwarding between TAP and websocket peers.
- `src/tuntap.c` - TAP/TUN device creation and I/O.
- `src/socket.c` - bind/connect helpers (IPv4/IPv6/unix socket).
- `src/ssl.c` - TLS handling for native client.
- `src/uwsgi.c` - nginx/uWSGI request parsing and websocket upgrade response.
- `src/vpn-ws.h` - shared structures and function declarations.

### Build and packaging

- `Makefile` - builds `lollipop-server`, `lollipop-client` and compatibility copies (`vpn-ws`, `vpn-ws-client`).
- `docker/Dockerfile` - docker server image.
- `docker/entrypoint.sh` - container startup, cert generation, starts nginx + backend services.
- `docker/nginx.conf.template` - nginx routes for WSS and HTTPS2 modes.

### HTTPS2 experimental transport

- `server_h2/https2_payload_server.py` - simple queue-based payload server (`/send`, `/recv`).
- `clients/https2_payload_cli.py` - one-shot send/recv CLI for HTTPS2 mode.
- `clients/https2_payload_poll.py` - long-poll receiver helper.
- `clients/utls/main.go` - uTLS-based HTTPS2 client (browser-like TLS fingerprint).
- `clients/utls/go.mod`, `clients/utls/go.sum` - Go module dependencies.

### Desktop clients

- `clients/lollipop_gui.py` - desktop GUI with protocol switch (`ws`, `wss`, `https2`).
- `clients/linux/lollipop.sh` - Linux launcher.
- `clients/macos/lollipop.command` - macOS launcher.
- `clients/windows/lollipop.bat` - Windows launcher.

### iOS client

- `clients/ios/LollipopApp/LollipopApp.swift` - SwiftUI app root.
- `clients/ios/LollipopApp/ContentView.swift` - iOS UI and protocol selector (`wss`/`https2`).
- `clients/ios/LollipopApp/LollipopVPNManager.swift` - profile save/load and tunnel start/stop.
- `clients/ios/LollipopTunnel/PacketTunnelProvider.swift` - packet tunnel extension logic.
- `clients/ios/README.md` - full Xcode from-scratch build guide.

### Config

- `config/browser_headers.example.json` - sample header configuration JSON for `--headers-json`.

---

## 2) Build binaries

```bash
make clean
make
```

Output binaries:

- `./lollipop-server`
- `./lollipop-client`

Compatibility copies also generated:

- `./vpn-ws`
- `./vpn-ws-client`

---

## 3) Header customization JSON

Lollipop client now supports:

- `--header "Name: Value"` (repeatable)
- `--headers-json /path/to/file.json`

Example JSON (`config/browser_headers.example.json`):

```json
{
  "User-Agent": "Mozilla/5.0 ...",
  "Accept": "text/html,...",
  "Accept-Language": "en-US,en;q=0.9"
}
```

Usage:

```bash
sudo ./lollipop-client \
  --user cucumber \
  --password potato \
  --headers-json ./config/browser_headers.example.json \
  vpn-ws0 wss://127.0.0.1/cucumber
```

---

## 4) Install Docker on Ubuntu VPS

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

---

## 5) Run server in Docker (IP only, no domain)

### Build image

```bash
docker build -t lollipop-server -f docker/Dockerfile .
```

### Run container

```bash
docker run -d \
  --name lollipop-server \
  -p 80:80 -p 443:443 \
  -e SERVER_IPV4=203.0.113.10 \
  -e SERVER_IPV6=2001:db8::10 \
  -v lollipop-certs:/data/certs \
  lollipop-server
```

### Certificate paths (generated automatically)

- cert: `/data/certs/cucumber.crt`
- key: `/data/certs/potato.key`

Copy cert to host:

```bash
docker cp lollipop-server:/data/certs/cucumber.crt ./cucumber.crt
```

Then install/trust `cucumber.crt` on clients.

---

## 6) Localhost Linux test (verified flow)

### A. Start HTTPS2 test server locally

```bash
python3 -m pip install --user flask requests
python3 server_h2/https2_payload_server.py
```

### B. In second terminal, send then receive

```bash
python3 clients/https2_payload_cli.py --base http://127.0.0.1:18080 --client-id test1 --send "hello-local"
python3 clients/https2_payload_cli.py --base http://127.0.0.1:18080 --client-id test1 --recv
```

Expected: `hello-local` is returned.

---

## 7) True VPN requirement (route all traffic)

For **full-device traffic routing**, use **WSS mode + TAP + default route changes**.

### Linux example (all traffic)

```bash
sudo ./lollipop-client --user cucumber --password potato vpn-ws0 wss://203.0.113.10/cucumber
sudo ip link set vpn-ws0 up
sudo ip addr add 10.99.0.2/24 dev vpn-ws0
sudo ip route replace default dev vpn-ws0
```

### macOS example (all traffic)

1. Install TAP driver.
2. Start client:

```bash
sudo ./lollipop-client --user cucumber --password potato /dev/tap0 wss://203.0.113.10/cucumber
```

3. Assign address and default route (example):

```bash
sudo ifconfig tap0 10.99.0.3 10.99.0.1 up
sudo route change default 10.99.0.1
```

### iOS

On iOS, full-device routing is controlled by the Packet Tunnel extension and network settings set in `PacketTunnelProvider.swift`.

> HTTPS2 mode is experimental payload transport and not equivalent to full L2 VPN behavior.

---

## 8) Desktop client usage (Linux + macOS + Windows)

### Install dependencies

Linux/macOS:

```bash
python3 -m pip install PyQt5 requests
```

### Launch

Linux:

```bash
./clients/linux/lollipop.sh
```

macOS:

```bash
./clients/macos/lollipop.command
```

Windows:

```bat
clients\windows\lollipop.bat
```

In GUI choose protocol:

- `wss` for true VPN tunnel
- `https2` for payload mode

---

## 9) iOS full build from scratch

Read and follow:

- `clients/ios/README.md`

That document includes:

- project creation fields,
- extension creation,
- bundle IDs/signing,
- capability setup,
- device deployment,
- certificate trust and troubleshooting.

---

## 10) uTLS client (browser-like TLS fingerprint)

```bash
cd clients/utls
go mod tidy
go run . --base https://203.0.113.10/potato_h2 --client-id test1 --send "hello"
go run . --base https://203.0.113.10/potato_h2 --client-id test1 --recv
```

This uses `utls.HelloChrome_Auto`.

---

## 11) WSS and HTTPS2 endpoints in docker nginx

- WSS path: `/cucumber`
- HTTPS2 send path: `/potato_h2/send`
- HTTPS2 recv path: `/potato_h2/recv`

All are reachable by **IP address only**.
