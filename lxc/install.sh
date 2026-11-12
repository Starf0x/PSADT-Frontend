#!/usr/bin/env bash
# Installeert PSADT Frontend in een Debian 12/13 LXC-container (bijv. Proxmox).
# Gebruik (als root, ín de LXC, niet op de Proxmox-host):
#   vanuit een clone:   bash lxc/install.sh
#   los (one-liner):    bash -c "$(curl -fsSL https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/lxc/install.sh)"
#   privé-repo:         GITHUB_TOKEN=<token> bash -c "$(curl -fsSL -H "Authorization: Bearer <token>" -H "Accept: application/vnd.github.raw" https://api.github.com/repos/Starf0x/PSADT-Frontend/contents/lxc/install.sh)"
# Wil je vanaf de Proxmox-host meteen een LXC laten aanmaken? Gebruik ct/psadt-frontend.sh.
# Draait dezelfde app als de Docker-image: zelfde code, zelfde env-variabelen, poort 8000.
# Optioneel: PSADT_COOKIE_SECURE=false (alleen bij eerste installatie) als je zonder HTTPS test.
set -euo pipefail

REPO="${PSADT_REPO:-Starf0x/PSADT-Frontend}"
BRANCH="${PSADT_BRANCH:-main}"

APP_DIR=/opt/psadt-frontend
DATA_DIR=/var/lib/psadt-frontend
ENV_FILE=/etc/psadt-frontend.env
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." 2>/dev/null && pwd || true)"

[ "$(id -u)" -eq 0 ] || { echo "Draai dit script als root."; exit 1; }
if command -v pveversion >/dev/null 2>&1; then
  echo "Dit is een Proxmox-host. Draai dit script ín een LXC, of gebruik ct/psadt-frontend.sh op de host."
  exit 1
fi

apt-get update -qq
apt-get install -y -qq python3 python3-venv curl ca-certificates rsync git

# Los gedraaid (bijv. via curl)? Dan eerst de broncode ophalen.
if [ "${PSADT_SKIP_FETCH:-0}" != 1 ] && { [ -z "$SRC_DIR" ] || [ ! -f "$SRC_DIR/backend/requirements.txt" ] || [ "$SRC_DIR" = /opt/psadt-frontend-src ]; }; then
  SRC_DIR=/opt/psadt-frontend-src
  URL="https://github.com/$REPO.git"
  [ -n "${GITHUB_TOKEN:-}" ] && URL="https://x-access-token:${GITHUB_TOKEN}@github.com/$REPO.git"
  if [ -d "$SRC_DIR/.git" ]; then
    if git -C "$SRC_DIR" fetch -q "$URL" "$BRANCH"; then
      git -C "$SRC_DIR" reset -q --hard FETCH_HEAD
    else
      echo "Let op: kon $REPO niet ophalen (privé-repo? zet GITHUB_TOKEN). Bestaande code wordt gebruikt."
    fi
  else
    rm -rf "$SRC_DIR" && git clone -q --depth 1 -b "$BRANCH" "$URL" "$SRC_DIR"
    git -C "$SRC_DIR" remote set-url origin "https://github.com/$REPO.git"  # token niet bewaren
  fi
fi
if ! command -v node >/dev/null || [ "$(node -v | cut -c2- | cut -d. -f1)" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y -qq nodejs
fi

# PowerShell 7 (alleen voor syntaxcontrole van gegenereerde scripts), zelfde versie als de Docker-image
PWSH_VERSION=7.4.6
if [ ! -x /opt/pwsh/pwsh ] || ! /opt/pwsh/pwsh -NoProfile -Command '$PSVersionTable.PSVersion.ToString()' | grep -qx "$PWSH_VERSION"; then
  case "$(dpkg --print-architecture)" in arm64) PARCH=arm64 ;; *) PARCH=x64 ;; esac
  rm -rf /opt/pwsh && mkdir -p /opt/pwsh
  curl -fsSL "https://github.com/PowerShell/PowerShell/releases/download/v${PWSH_VERSION}/powershell-${PWSH_VERSION}-linux-${PARCH}.tar.gz" | tar xz -C /opt/pwsh
  chmod +x /opt/pwsh/pwsh
fi

# Officieel PSADT v4-pakket voor de export (zelfde versie en hash als de Docker-image)
PSADT_VERSION=4.1.8
PSADT_SHA256=50cb8d32973fc7648060a48cad63912ecb5caca5a70754f37e83aa06bd380283
mkdir -p /opt/psadt
TK=/opt/psadt/PSAppDeployToolkit_Template_v4.zip
if ! echo "$PSADT_SHA256  $TK" | sha256sum -c - >/dev/null 2>&1; then
  curl -fsSL -o "$TK" "https://github.com/PSAppDeployToolkit/PSAppDeployToolkit/releases/download/${PSADT_VERSION}/PSAppDeployToolkit_Template_v4.zip"
  echo "$PSADT_SHA256  $TK" | sha256sum -c -
fi

id psadt >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin psadt
mkdir -p "$APP_DIR" "$DATA_DIR"
rsync -a --delete --exclude node_modules --exclude .git --exclude data --exclude .venv "$SRC_DIR"/ "$APP_DIR"/

(cd "$APP_DIR/frontend" && npm ci --silent && npm run build)
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --upgrade pip
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt"

if [ ! -f "$ENV_FILE" ]; then
  cp "$APP_DIR/.env.example" "$ENV_FILE"
  if [ -n "${PSADT_ADMIN_PASSWORD:-}" ]; then
    sed -i "s|^PSADT_ADMIN_PASSWORD=.*|PSADT_ADMIN_PASSWORD=${PSADT_ADMIN_PASSWORD}|" "$ENV_FILE"
  fi
  if [ -n "${PSADT_COOKIE_SECURE:-}" ]; then
    sed -i "s/^PSADT_COOKIE_SECURE=.*/PSADT_COOKIE_SECURE=${PSADT_COOKIE_SECURE}/" "$ENV_FILE"
  fi
  cat >> "$ENV_FILE" <<ENVX
PSADT_DATA_DIR=$DATA_DIR
PSADT_PWSH_PATH=/opt/pwsh/pwsh
PSADT_TOOLKIT_ZIP=/opt/psadt/PSAppDeployToolkit_Template_v4.zip
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
POWERSHELL_TELEMETRY_OPTOUT=1
POWERSHELL_UPDATECHECK=Off
ENVX
  chmod 600 "$ENV_FILE"
fi
chown -R psadt:psadt "$DATA_DIR"

cat > /etc/systemd/system/psadt-frontend.service <<UNIT
[Unit]
Description=PSADT Frontend
After=network-online.target

[Service]
User=psadt
WorkingDirectory=$APP_DIR/backend
EnvironmentFile=$ENV_FILE
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips *
Restart=on-failure
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=$DATA_DIR

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now psadt-frontend
echo "Klaar. Admin-wachtwoord (bij eerste start): journalctl -u psadt-frontend | grep admin-wachtwoord"
