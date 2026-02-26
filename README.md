# Lollipop transport toolkit

Lollipop provides two transports:

1. **WebSocket over TLS (`wss://`)** using `vpn-ws` / `vpn-ws-client` (full L2 tunnel).
2. **HTTPS/HTTP2 request-response payload tunnel** (experimental) using `server_h2/h2_tunnel_server.py` + `clients/h2_tunnel_client.py`.

Server remains command-line software, now packaged in Docker.

---

## Build native binaries

```bash
make clean
make
```

Produces:

- `./vpn-ws`
- `./vpn-ws-client`

---

## Client headers are fully configurable

`vpn-ws-client` now supports repeated `--header` options, so request headers can look browser-like and be tuned later:

```bash
sudo ./vpn-ws-client \
  --user cucumber \
  --password potato \
  --header "User-Agent: Mozilla/5.0" \
  --header "Accept-Language: en-US,en;q=0.9" \
  --header "Cache-Control: no-cache" \
  vpn-ws0 \
  wss://203.0.113.10/cucumber
```

Also supported:

- `--user <name>`
- `--password <secret>`

---

## Docker server (recommended)

This runs nginx + `vpn-ws` + experimental HTTPS payload service in one container.

### 1) Build image

```bash
docker build -t lollipop-server -f docker/Dockerfile .
```

### 2) Run container

```bash
docker run -d \
  --name lollipop-server \
  -p 80:80 -p 443:443 \
  -e SERVER_IPV4=203.0.113.10 \
  -e SERVER_IPV6=2001:db8::10 \
  -v lollipop-certs:/data/certs \
  lollipop-server
```

### 3) Certificate location (copy for clients)

Inside container / mounted volume:

- cert: `/data/certs/cucumber.crt`
- key: `/data/certs/potato.key`

Copy cert to host:

```bash
docker cp lollipop-server:/data/certs/cucumber.crt ./cucumber.crt
```

Then trust/install this cert on your clients.

> Certificate subject and auth words intentionally avoid VPN naming and use simple words (`cucumber`, `potato`).

---

## WSS mode (full L2 tunnel)

Run client:

```bash
sudo ./vpn-ws-client --user cucumber --password potato vpn-ws0 wss://203.0.113.10/cucumber
```

IPv6:

```bash
sudo ./vpn-ws-client --user cucumber --password potato vpn-ws0 wss://[2001:db8::10]/cucumber
```

---

## HTTPS/HTTP2 mode (request-response payload, experimental)

This is not the websocket L2 tunnel. It is HTTP payload exchange over TLS.

### Server endpoint paths

- `POST /potato_h2/send`
- `GET /potato_h2/recv`

These are exposed through nginx TLS listener (`listen 443 ssl http2;`).

### Client usage

Install dependency:

```bash
python3 -m pip install requests
```

Send payload:

```bash
python3 clients/h2_tunnel_client.py \
  --base https://203.0.113.10/potato_h2 \
  --client-id node1 \
  --cafile ./cucumber.crt \
  --send "hello-from-client"
```

Receive payload:

```bash
python3 clients/h2_tunnel_client.py \
  --base https://203.0.113.10/potato_h2 \
  --client-id node1 \
  --cafile ./cucumber.crt \
  --recv
```

---

## Notes

- `wss://` mode = persistent websocket tunnel, best for full VPN-like behavior.
- HTTPS/HTTP2 mode = request-response transport, useful when you need plain HTTPS-like traffic patterns.
- You can tune headers with `--header` and adjust nginx paths/words as needed.
