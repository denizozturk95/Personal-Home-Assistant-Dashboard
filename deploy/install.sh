#!/usr/bin/env bash
# One-shot Pi setup. Run from the repo root on the Pi: bash deploy/install.sh
# Assumes Raspberry Pi OS (Debian) with user `pi`. Adjust paths if you use a different user.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-$USER}"
CERT_DIR=/etc/ssl/dashboard

echo "==> Installing system packages"
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip nginx avahi-daemon openssl

echo "==> Creating Python venv"
python3 -m venv "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/pip" install --upgrade pip
"$REPO_DIR/.venv/bin/pip" install -r "$REPO_DIR/backend/requirements.txt"

echo "==> Seeding backend/.env (edit it to set your token)"
if [ ! -f "$REPO_DIR/backend/.env" ]; then
  cp "$REPO_DIR/backend/.env.example" "$REPO_DIR/backend/.env"
  TOKEN=$(openssl rand -hex 32)
  sed -i "s/change-me-to-a-long-random-string/$TOKEN/" "$REPO_DIR/backend/.env"
  echo "    generated token: $TOKEN"
fi

echo "==> Self-signed TLS cert for dashboard.local"
sudo mkdir -p "$CERT_DIR"
if [ ! -f "$CERT_DIR/fullchain.pem" ]; then
  sudo openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out    "$CERT_DIR/fullchain.pem" \
    -subj "/CN=dashboard.local" \
    -addext "subjectAltName=DNS:dashboard.local"
fi

echo "==> Installing systemd unit"
sudo cp "$REPO_DIR/deploy/dashboard.service" /etc/systemd/system/dashboard.service
sudo sed -i "s|/home/pi|/home/$SERVICE_USER|g; s|User=pi|User=$SERVICE_USER|" \
  /etc/systemd/system/dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable --now dashboard.service

echo "==> Installing nginx site"
sudo cp "$REPO_DIR/deploy/nginx.conf" /etc/nginx/sites-available/dashboard
sudo ln -sf /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/dashboard
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload-or-restart nginx

echo "==> Done. Visit https://dashboard.local on your iPhone."
echo "    The first visit will warn about the self-signed cert — accept it once."
