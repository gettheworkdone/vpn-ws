#!/usr/bin/env bash
set -euo pipefail

CERT_DIR=${CERT_DIR:-/data/certs}
mkdir -p "$CERT_DIR" /run/lollipop

CERT_CRT="$CERT_DIR/cucumber.crt"
CERT_KEY="$CERT_DIR/potato.key"

if [[ ! -f "$CERT_CRT" || ! -f "$CERT_KEY" ]]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -subj "/CN=cucumber" \
    -addext "subjectAltName=IP:${SERVER_IPV4:-127.0.0.1},IP:${SERVER_IPV6:-::1}" \
    -keyout "$CERT_KEY" \
    -out "$CERT_CRT"
  chmod 600 "$CERT_KEY"
fi

envsubst '$CERT_CRT $CERT_KEY' < /etc/nginx/templates/lollipop.conf.template > /etc/nginx/conf.d/default.conf

gunicorn -w 1 -b 127.0.0.1:18080 server_h2.h2_tunnel_server:app &
/app/vpn-ws /run/lollipop/vpn.sock &
exec nginx -g 'daemon off;'
