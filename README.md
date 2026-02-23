# Lollipop (formerly vpn-ws)

Lollipop is a Layer-2 VPN over WebSocket (`ws://`) and secure WebSocket (`wss://`).

- **Server binary**: `vpn-ws`
- **Client binary**: `vpn-ws-client`
- **Desktop GUI wrapper**: `clients/lollipop_gui.py`

This README is intentionally long and copy/paste-friendly.

---

## 1) What you are building

Lollipop creates a TAP interface and forwards Ethernet frames over WebSocket.

- `ws://` mode = plain HTTP (debug only)
- `wss://` mode = HTTPS + TLS encryption (normal usage)
- Works behind nginx using `uwsgi_pass`
- Authentication is handled by nginx (basic auth, mTLS, etc.)

---

## 2) Tested architecture for no-domain VPS

You said you have **no domain**, only VPS IP.

This guide supports:

- IPv4 only (`203.0.113.10`)
- IPv6 only (`2001:db8::10`)
- dual stack

We generate a **self-signed certificate with IP SAN** and then install/trust the cert on clients.

---

## 3) Build from source (server and client)

### Ubuntu/Debian build deps

```bash
sudo apt update
sudo apt install -y build-essential make gcc libssl-dev pkg-config
```

### Build

```bash
git clone https://github.com/unbit/vpn-ws.git
cd vpn-ws
make clean
make
```

Expected output binaries:

- `./vpn-ws`
- `./vpn-ws-client`

Optional static server build:

```bash
make clean
make vpn-ws-static
```

---

## 4) Server setup on VPS (Ubuntu example)

## 4.1 Install runtime packages

```bash
sudo apt update
sudo apt install -y nginx apache2-utils iproute2 bridge-utils ca-certificates openssl
```

## 4.2 Create directories

```bash
sudo mkdir -p /etc/lollipop /var/log/lollipop /run/lollipop
sudo chown -R root:root /etc/lollipop
sudo chmod 755 /etc/lollipop /var/log/lollipop
```

## 4.3 Create nginx basic auth credentials

```bash
sudo htpasswd -c /etc/nginx/.lollipop_htpasswd lollipop
# enter a strong password when asked
```

## 4.4 Create a self-signed cert for IP address (NO DOMAIN)

> Replace IPs below with your real VPS IPs.

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
```

Generate key + cert:

```bash
sudo openssl req -x509 -nodes -newkey rsa:4096 -days 825 \
  -keyout /etc/lollipop/server.key \
  -out /etc/lollipop/server.crt \
  -config /etc/lollipop/openssl-ip.cnf
```

Secure permissions:

```bash
sudo chmod 600 /etc/lollipop/server.key
sudo chmod 644 /etc/lollipop/server.crt
```

## 4.5 Start Lollipop server daemon (unix socket mode)

```bash
cd /opt
sudo mkdir -p /opt/lollipop
sudo cp /path/to/vpn-ws /opt/lollipop/vpn-ws
sudo chmod 755 /opt/lollipop/vpn-ws
```

Manual test run:

```bash
sudo /opt/lollipop/vpn-ws /run/lollipop/vpn.sock
```

If you want server TAP too (optional):

```bash
sudo /opt/lollipop/vpn-ws --tuntap vpn0 /run/lollipop/vpn.sock
```

## 4.6 Configure nginx with BOTH ws(debug) and wss(normal)

```bash
cat <<'EOF' | sudo tee /etc/nginx/sites-available/lollipop.conf
server {
    listen 80;
    listen [::]:80;
    server_name _;

    # Debug only (unencrypted)
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

    ssl_certificate     /etc/lollipop/server.crt;
    ssl_certificate_key /etc/lollipop/server.key;

    # reasonable defaults
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Normal encrypted endpoint
    location /vpn {
        include uwsgi_params;
        uwsgi_pass unix:/run/lollipop/vpn.sock;
        auth_basic "Lollipop VPN";
        auth_basic_user_file /etc/nginx/.lollipop_htpasswd;
    }

    # Optional admin JSON API
    location /vpn_admin {
        include uwsgi_params;
        uwsgi_modifier1 1;
        uwsgi_pass unix:/run/lollipop/vpn.sock;
        auth_basic "Lollipop Admin";
        auth_basic_user_file /etc/nginx/.lollipop_htpasswd;
    }
}
EOF
```

Enable site:

```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/lollipop.conf /etc/nginx/sites-enabled/lollipop.conf
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 5) Add Lollipop server to systemd (autostart on reboot)

```bash
cat <<'EOF' | sudo tee /etc/systemd/system/lollipop.service
[Unit]
Description=Lollipop VPN WebSocket backend
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
```

Enable + start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable lollipop.service
sudo systemctl start lollipop.service
sudo systemctl status lollipop.service --no-pager
```

---

## 6) Export certificate from server and install on client

Copy server public cert to your local machine:

```bash
scp root@203.0.113.10:/etc/lollipop/server.crt ./lollipop-server.crt
```

(If only IPv6 reachable):

```bash
scp root@[2001:db8::10]:/etc/lollipop/server.crt ./lollipop-server.crt
```

### Linux trust store

```bash
sudo cp ./lollipop-server.crt /usr/local/share/ca-certificates/lollipop-server.crt
sudo update-ca-certificates
```

### macOS trust store

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./lollipop-server.crt
```

### Windows trust store (PowerShell as Admin)

```powershell
Import-Certificate -FilePath .\lollipop-server.crt -CertStoreLocation Cert:\LocalMachine\Root
```

### iOS trust store

1. AirDrop/mail/file-share `lollipop-server.crt` to iPhone.
2. Open file and install profile.
3. Go to **Settings -> General -> About -> Certificate Trust Settings**.
4. Enable full trust for your Lollipop certificate.

---

## 7) Client CLI usage (Linux/macOS/Windows)

General syntax:

```bash
vpn-ws-client <tap_or_device> <ws_or_wss_url>
```

### 7.1 Linux client

Create/open TAP by name automatically (run as root):

```bash
sudo ./vpn-ws-client vpn-ws0 wss://lollipop:YOUR_PASSWORD@203.0.113.10/vpn
```

IPv6 target:

```bash
sudo ./vpn-ws-client vpn-ws0 wss://lollipop:YOUR_PASSWORD@[2001:db8::10]/vpn
```

Assign IP to TAP after connect (example):

```bash
sudo ip addr add 10.99.0.2/24 dev vpn-ws0
sudo ip link set vpn-ws0 up
```

### 7.2 macOS client

Install TAP driver first (third-party tuntap package required), then:

```bash
sudo ./vpn-ws-client /dev/tap0 wss://lollipop:YOUR_PASSWORD@203.0.113.10/vpn
```

### 7.3 Windows client

1. Install TAP-Windows adapter.
2. Name adapter (example: `lollipop`).
3. Run elevated shell:

```powershell
.\vpn-ws-client.exe lollipop wss://lollipop:YOUR_PASSWORD@203.0.113.10/vpn
```

---

## 8) Desktop GUI app: Lollipop

A simple PyQt GUI is included:

- `clients/lollipop_gui.py`

Install dependency:

```bash
python3 -m pip install PyQt5
```

Run:

```bash
python3 clients/lollipop_gui.py
```

In GUI:

- Enter server IP (IPv4 or IPv6)
- Enter username/password
- Choose `wss` (recommended) or `ws` (debug)
- Click **Connect**

The GUI wraps `vpn-ws-client`, so TAP support is still required.

---

## 9) iOS support (important technical reality)

iOS does not allow arbitrary user apps to create TAP interfaces and full Layer-2 tunnels unless the app has Apple Network Extension entitlements.

So for iOS:

- You can install/trust certs (covered above)
- You can connect at app level with custom software
- But full system-wide Layer-2 VPN requires Apple-approved entitlements and an iOS app built around `NetworkExtension`

This repository now provides complete server + desktop client flow. For iOS production-grade tunnel app, you must build/sign a dedicated NetworkExtension app with Apple entitlement approval.

---

## 10) Debug flow vs production flow

### Debug (`ws://`)

```bash
sudo ./vpn-ws-client vpn-ws0 ws://lollipop:YOUR_PASSWORD@203.0.113.10/vpn
```

### Production (`wss://`)

```bash
sudo ./vpn-ws-client vpn-ws0 wss://lollipop:YOUR_PASSWORD@203.0.113.10/vpn
```

Always prefer `wss://` in normal use.

---

## 11) Optional bridge mode examples

Server bridge mode:

```bash
sudo /opt/lollipop/vpn-ws --bridge --tuntap vpn0 /run/lollipop/vpn.sock
```

Client bridge mode:

```bash
sudo ./vpn-ws-client --bridge vpn-ws0 wss://lollipop:YOUR_PASSWORD@203.0.113.10/vpn
```

---

## 12) Useful operations

Check logs:

```bash
sudo journalctl -u lollipop.service -f
sudo journalctl -u nginx -f
```

Validate port listeners:

```bash
sudo ss -tulpen | grep -E ':80|:443'
```

Check nginx config:

```bash
sudo nginx -t
```

---

## 13) Security checklist

- Use `wss://` in production
- Keep `/etc/lollipop/server.key` mode `600`
- Use strong nginx basic auth password
- Keep server patched
- Install/trust certificate explicitly on clients
- Do not use `--no-verify` in client

---

## 14) Changed naming

User-facing name is now **Lollipop**.

Binary names remain `vpn-ws` and `vpn-ws-client` for compatibility.
