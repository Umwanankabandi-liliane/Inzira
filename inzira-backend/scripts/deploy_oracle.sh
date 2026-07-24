#!/usr/bin/env bash
# Inzira — Oracle Cloud Always Free deploy helper
# Usage:
#   ./scripts/deploy_oracle.sh              # first-time setup (packages + venv)
#   ./scripts/deploy_oracle.sh --finish     # after .env is filled: assets + systemd
#   ./scripts/deploy_oracle.sh --caddy      # HTTPS (set INZIRA_DOMAIN=inzira.duckdns.org)
#   ./scripts/deploy_oracle.sh --update     # git pull + restart

set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
USER_NAME="${SUDO_USER:-$USER}"

install_packages() {
  echo "=== Installing system packages ==="
  sudo apt-get update
  sudo apt-get install -y git python3-venv python3-pip build-essential libpq-dev curl unzip
}

setup_venv() {
  echo "=== Python virtualenv + dependencies ==="
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements-prod.txt
}

ensure_env() {
  if [[ ! -f .env ]]; then
    echo ""
    echo "Create .env now (copy from your PC). Example:"
    echo "  nano $ROOT/.env"
    echo ""
    cp -n .env.example .env 2>/dev/null || true
    if [[ -f .env ]]; then
      echo "Started from .env.example — edit with your real secrets, then run:"
      echo "  ./scripts/deploy_oracle.sh --finish"
    fi
    exit 0
  fi
}

download_assets() {
  # shellcheck disable=SC1091
  source .venv/bin/activate
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  echo "=== Downloading ML bundle (may take several minutes) ==="
  python scripts/download_deploy_assets.py
}

install_systemd() {
  echo "=== Installing systemd service ==="
  sudo cp deploy/oracle/inzira.service /etc/systemd/system/inzira.service
  sudo sed -i "s|__INZIRA_ROOT__|$ROOT|g" /etc/systemd/system/inzira.service
  sudo sed -i "s|__INZIRA_USER__|$USER_NAME|g" /etc/systemd/system/inzira.service
  sudo systemctl daemon-reload
  sudo systemctl enable inzira
  sudo systemctl restart inzira
  echo "Waiting for models to load (up to 3 min)..."
  sleep 30
  for i in 1 2 3 4 5 6; do
    if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
      curl -s http://127.0.0.1:8000/health
      echo ""
      echo "=== Inzira is running on port 8000 ==="
      return 0
    fi
    sleep 20
  done
  echo "Health check not ready yet — check logs:"
  echo "  sudo journalctl -u inzira -n 50 --no-pager"
}

install_caddy() {
  local domain="${INZIRA_DOMAIN:-}"
  if [[ -z "$domain" ]]; then
    echo "Set your DuckDNS domain first, e.g.:"
    echo "  export INZIRA_DOMAIN=inzira.duckdns.org"
    echo "  ./scripts/deploy_oracle.sh --caddy"
    exit 1
  fi
  echo "=== Installing Caddy for https://$domain ==="
  if ! command -v caddy >/dev/null 2>&1; then
    sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt-get update
    sudo apt-get install -y caddy
  fi
  sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
$domain {
    reverse_proxy 127.0.0.1:8000
}
EOF
  sudo systemctl enable caddy
  sudo systemctl restart caddy
  echo "HTTPS ready: https://$domain"
  echo "Add $domain to Firebase → Authentication → Authorized domains"
}

update_app() {
  if [[ -d "$ROOT/../.git" ]]; then
    cd "$ROOT/.."
    git pull
    cd "$ROOT"
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -r requirements-prod.txt
  sudo systemctl restart inzira
  echo "Updated and restarted."
}

case "${1:-}" in
  --finish)
    ensure_env
    download_assets
    install_systemd
    ;;
  --caddy)
    install_caddy
    ;;
  --update)
    update_app
    ;;
  *)
    install_packages
    setup_venv
    ensure_env
    echo ""
    echo "Next: edit .env with your secrets, then:"
    echo "  ./scripts/deploy_oracle.sh --finish"
  echo "  export INZIRA_DOMAIN=inzira.duckdns.org"
  echo "  ./scripts/deploy_oracle.sh --caddy"
    ;;
esac
