# Lollipop (vpn-ws)

Lollipop is a Layer-2 VPN over WebSocket.

- Server binary: `vpn-ws` (CLI only)
- Client binary: `vpn-ws-client` (CLI)
- GUI wrappers/source are in `clients/`

This guide is written as copy/paste instructions for IP-only VPS deployment (no domain), with both debug `ws://` and production `wss://` modes.

---

## 1. Repository layout and clients

- `src/` – C implementation of server/client
- `clients/lollipop_gui.py` – desktop GUI wrapper (uses `vpn-ws-client`)
- `clients/linux/lollipop.sh` – Linux launcher for GUI
- `clients/macos/lollipop.command` – macOS launcher for GUI
- `clients/windows/lollipop.bat` – Windows launcher for GUI
- `clients/ios/` – iOS SwiftUI app + Packet Tunnel extension source (NetworkExtension)

> Server side remains CLI only by design.

---

## 2. Build binaries from source (Linux/macOS)

```bash
sudo apt update
sudo apt install -y build-essential make gcc libssl-dev pkg-config

git clone https://github.com/unbit/vpn-ws.git
cd vpn-ws
make clean
make
```

Expected:

- `./vpn-ws`
- `./vpn-ws-client`

---

## 3. VPS server setup (nginx + systemd + TLS cert with IP SAN)

## 3.1 Install packages

```bash
sudo apt update
sudo apt install -y nginx apache2-utils iproute2 bridge-utils ca-certificates openssl
```

## 3.2 Prepare folders

```bash
sudo mkdir -p /etc/lollipop /opt/lollipop /run/lollipop
sudo cp ./vpn-ws /opt/lollipop/vpn-ws
sudo chmod 755 /opt/lollipop/vpn-ws
```

## 3.3 Create nginx auth credentials

```bash
sudo htpasswd -c /etc/nginx/.lollipop_htpasswd lollipop
```

## 3.4 Generate self-signed cert for IP (no domain)

Edit IPs to your real server IPs:

```bash
cat <<'EOF' | sudo tee /etc/lollipop/openssl-ip.cnf
[req]
default_bits = 4096
prompt = no
default_md = sha256
x509_extensions = v3_req
distinguished_name = dn

[dn]
C = US
ST = VPS
L = VPS
O = Lollipop
OU = VPN
CN = 203.0.113.10

[v3_req]
subjectAltName = @alt_names
extendedKeyUsage = serverAuth
keyUsage = digitalSignature, keyEncipherment

[alt_names]
IP.1 = 203.0.113.10
IP.2 = 2001:db8::10
EOF

sudo openssl req -x509 -nodes -newkey rsa:4096 -days 825 \
  -keyout /etc/lollipop/server.key \
  -out /etc/lollipop/server.crt \
  -config /etc/lollipop/openssl-ip.cnf

sudo chmod 600 /etc/lollipop/server.key
sudo chmod 644 /etc/lollipop/server.crt
```

## 3.5 Run backend manually once (test)

```bash
sudo /opt/lollipop/vpn-ws /run/lollipop/vpn.sock
```

## 3.6 Configure nginx with BOTH ws (debug) and wss (normal)

```bash
cat <<'EOF' | sudo tee /etc/nginx/sites-available/lollipop.conf
server {
    listen 80;
    listen [::]:80;
    server_name _;

    # Debug endpoint (plaintext HTTP/websocket)
    location /vpn {
        include uwsgi_params;
        uwsgi_pass unix:/run/lollipop/vpn.sock;
        auth_basic "Lollipop Debug";
        auth_basic_user_file /etc/nginx/.lollipop_htpasswd;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name _;

    ssl_certificate /etc/lollipop/server.crt;
    ssl_certificate_key /etc/lollipop/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Production encrypted endpoint
    location /vpn {
        include uwsgi_params;
        uwsgi_pass unix:/run/lollipop/vpn.sock;
        auth_basic "Lollipop VPN";
        auth_basic_user_file /etc/nginx/.lollipop_htpasswd;
    }

    location /vpn_admin {
        include uwsgi_params;
        uwsgi_modifier1 1;
        uwsgi_pass unix:/run/lollipop/vpn.sock;
        auth_basic "Lollipop Admin";
        auth_basic_user_file /etc/nginx/.lollipop_htpasswd;
    }
}
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/lollipop.conf /etc/nginx/sites-enabled/lollipop.conf
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 3.7 Add backend to systemd (autostart)

```bash
cat <<'EOF' | sudo tee /etc/systemd/system/lollipop.service
[Unit]
Description=Lollipop VPN websocket backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/opt/lollipop/vpn-ws /run/lollipop/vpn.sock
Restart=always
RestartSec=2
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable lollipop.service
sudo systemctl start lollipop.service
sudo systemctl status lollipop.service --no-pager
```

---

## 4. Certificate distribution and trust

Download server cert to each client machine:

```bash
scp root@203.0.113.10:/etc/lollipop/server.crt ./lollipop-server.crt
# or
scp root@[2001:db8::10]:/etc/lollipop/server.crt ./lollipop-server.crt
```

Trust it system-wide:

### Linux

```bash
sudo cp ./lollipop-server.crt /usr/local/share/ca-certificates/lollipop-server.crt
sudo update-ca-certificates
```

### macOS

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./lollipop-server.crt
```

### Windows (PowerShell as Administrator)

```powershell
Import-Certificate -FilePath .\lollipop-server.crt -CertStoreLocation Cert:\LocalMachine\Root
```

### iOS

1. Copy `lollipop-server.crt` to device.
2. Install profile.
3. Enable trust in **Settings → General → About → Certificate Trust Settings**.

---

## 5. CLI client usage and command explanation

Base syntax:

```bash
vpn-ws-client [OPTIONS] <tap_or_device> <ws_url>
```

### Example command

```bash
sudo ./vpn-ws-client vpn-ws0 wss://lollipop:YOUR_PASSWORD@203.0.113.10/vpn
```

Meaning:

- `sudo` – needed to create/manage TAP interface
- `vpn-ws0` – local TAP interface name
- `wss://` – encrypted websocket over TLS
- `lollipop:YOUR_PASSWORD@` – HTTP BasicAuth credentials (`username:password`)
- `203.0.113.10` – VPS IP
- `/vpn` – nginx location forwarded to backend

### Is password sent in GET query string?

No. It is **not** in query args and not in `GET /...?password=...`.

- Credentials are converted to `Authorization: Basic <base64>` header.
- With `wss://`, the full HTTP handshake headers (including Authorization) are inside TLS encryption on the wire.
- So passive network observers cannot read it.

### Safer credential style (new)

You can now avoid credentials in URL and pass them as options:

```bash
sudo ./vpn-ws-client --user lollipop --password 'YOUR_PASSWORD' vpn-ws0 wss://203.0.113.10/vpn
```

IPv6 example:

```bash
sudo ./vpn-ws-client --user lollipop --password 'YOUR_PASSWORD' vpn-ws0 wss://[2001:db8::10]/vpn
```

---

## 6. What is bridge mode?

Lollipop works at Ethernet (Layer 2). By default, server/client act like virtual switch ports.

### Normal mode (no bridge)

- Only VPN members exchange frames through the vpn-ws switch.
- Local physical LAN is separate.

### Bridge mode

Bridge mode connects the VPN TAP interface to an existing OS bridge (`br0`), effectively extending one broadcast domain.

Use cases:
- expose a full LAN segment to remote peers
- allow L2 protocols (ARP, mDNS, SMB browsing) across sites

Tradeoffs:
- more broadcast traffic
- easier to create loops/misconfiguration
- should be used only when you need true L2 extension

Server bridge mode example:

```bash
sudo /opt/lollipop/vpn-ws --bridge --tuntap vpn0 /run/lollipop/vpn.sock
```

Client bridge mode example:

```bash
sudo ./vpn-ws-client --bridge vpn-ws0 wss://203.0.113.10/vpn
```

---

## 7. Desktop GUI clients (Linux/macOS/Windows)

Install PyQt5:

```bash
python3 -m pip install PyQt5
```

Run per platform:

### Linux

```bash
./clients/linux/lollipop.sh
```

### macOS

```bash
./clients/macos/lollipop.command
```

### Windows

```bat
clients\windows\lollipop.bat
```

GUI fields:
- server IP (v4/v6)
- port/path
- username/password
- protocol ws/wss
- optional client cert argument (`--crt`)

---

## 8. iOS client (NetworkExtension) source

You asked for iOS app support. Source is included in `clients/ios`:

- `clients/ios/LollipopApp/*`
- `clients/ios/LollipopTunnel/*`
- `clients/ios/README.md` build instructions

This uses `NetworkExtension` Packet Tunnel scaffolding and websocket auth wiring compatible with your Apple developer entitlement workflow.

> Build/signing must be done in Xcode on macOS with your Apple team profile.

---

## 9. Debug vs production endpoints

Debug only (plaintext):

```bash
sudo ./vpn-ws-client --user lollipop --password 'YOUR_PASSWORD' vpn-ws0 ws://203.0.113.10/vpn
```

Production (encrypted):

```bash
sudo ./vpn-ws-client --user lollipop --password 'YOUR_PASSWORD' vpn-ws0 wss://203.0.113.10/vpn
```

Always use `wss://` for normal usage.

---

## 10. Health checks

```bash
sudo nginx -t
sudo systemctl status lollipop.service --no-pager
sudo systemctl status nginx --no-pager
sudo ss -tulpen | grep -E ':80|:443'
sudo journalctl -u lollipop.service -f
```
