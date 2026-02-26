# Lollipop transport toolkit

Lollipop now exposes two transport modes:

1. **WSS mode** (`wss://`) for persistent websocket Layer-2 tunneling (`vpn-ws` + `vpn-ws-client`).
2. **HTTPS2 mode** (`https://...` request/response) for payload tunneling without persistent websocket sessions.

Both modes are available in desktop GUI and iOS client switchers.

---

## 1) Build

```bash
make clean
make
```

Binaries:
- `./vpn-ws`
- `./vpn-ws-client`

---

## 2) Configurable request headers

Native client supports repeatable browser-like header overrides:

```bash
sudo ./vpn-ws-client \
  --user cucumber \
  --password potato \
  --header "User-Agent: Mozilla/5.0" \
  --header "Accept-Language: en-US,en;q=0.9" \
  --header "Cache-Control: no-cache" \
  vpn-ws0 wss://127.0.0.1/cucumber
```

Options:
- `--user`
- `--password`
- `--header "Name: Value"` (max 32)

---

## 3) Docker server (nginx + vpn-ws + https2 payload service)

### Build image

```bash
docker build -t lollipop-server -f docker/Dockerfile .
```

### Run

```bash
docker run -d \
  --name lollipop-server \
  -p 80:80 -p 443:443 \
  -e SERVER_IPV4=127.0.0.1 \
  -e SERVER_IPV6=::1 \
  -v lollipop-certs:/data/certs \
  lollipop-server
```

### Generated cert paths

- cert: `/data/certs/cucumber.crt`
- key: `/data/certs/potato.key`

Copy cert to host:

```bash
docker cp lollipop-server:/data/certs/cucumber.crt ./cucumber.crt
```

No VPN words are used in generated certificate naming.

---

## 4) Localhost test on Linux (required smoke test)

This verifies the new HTTPS2 mode end-to-end on localhost.

### Start experimental payload server locally

```bash
python3 server_h2/h2_tunnel_server.py
```

In a second terminal:

```bash
python3 clients/h2_tunnel_client.py --base http://127.0.0.1:18080 --client-id test1 --send "hello-local"
python3 clients/h2_tunnel_client.py --base http://127.0.0.1:18080 --client-id test1 --recv
```

Expected: second command prints `hello-local`.

---

## 5) uTLS client for browser-like TLS fingerprint

If you want browser-like TLS handshake fingerprinting, use included Go uTLS client:

- source: `clients/utls/main.go`
- module: `clients/utls/go.mod`

Run:

```bash
cd clients/utls
go mod tidy
go run . --base https://127.0.0.1/potato_h2 --client-id test1 --send "hello"
go run . --base https://127.0.0.1/potato_h2 --client-id test1 --recv
```

This uses `utls.HelloChrome_Auto` for TLS handshake shaping.

---

## 6) WSS mode usage

```bash
sudo ./vpn-ws-client --user cucumber --password potato vpn-ws0 wss://127.0.0.1/cucumber
```

IPv6:

```bash
sudo ./vpn-ws-client --user cucumber --password potato vpn-ws0 wss://[::1]/cucumber
```

---

## 7) HTTPS2 mode usage

Paths served by nginx in docker stack:
- `POST /potato_h2/send`
- `GET /potato_h2/recv`

CLI example:

```bash
python3 clients/h2_tunnel_client.py \
  --base https://127.0.0.1/potato_h2 \
  --client-id node1 \
  --cafile ./cucumber.crt \
  --send "hello-from-client"

python3 clients/h2_tunnel_client.py \
  --base https://127.0.0.1/potato_h2 \
  --client-id node1 \
  --cafile ./cucumber.crt \
  --recv
```

---

## 8) Client protocol switchers (all platforms)

### Linux / macOS / Windows

Use `clients/lollipop_gui.py` (launchers in `clients/linux`, `clients/macos`, `clients/windows`).

GUI protocol selector now includes:
- `ws`
- `wss`
- `https2`

### iOS

`clients/ios/LollipopApp/ContentView.swift` includes protocol segmented selector:
- `wss`
- `https2`

Tunnel provider in `clients/ios/LollipopTunnel/PacketTunnelProvider.swift` handles both branches.

---

## 9) Notes

- WSS mode is still the correct choice for full L2 vpn-ws behavior.
- HTTPS2 mode is experimental request/response payload transport.
- You can tune handshake/request headers with `--header` and your own nginx rules.
