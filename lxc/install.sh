#!/usr/bin/env bash
# Installeert PSADT Frontend in een Debian 12/13 LXC-container (bijv. Proxmox).
# Gebruik (als root, vanuit de repo-map):  bash lxc/install.sh
# Draait dezelfde app als de Docker-image: zelfde code, zelfde env-variabelen, poort 8000.
set -euo pipefail

APP_DIR=/opt/psadt-frontend
DATA_DIR=/var/lib/psadt-frontend
ENV_FILE=/etc/psadt-frontend.env
SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"

[ "$(id -u)" -eq 0 ] || { echo "Draai dit script als root."; exit 1; }

apt-get update -qq
apt-get install -y -qq python3 python3-venv curl ca-certificates rsync
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
rsync -a --delete --exclude node_modules --exclude .git --exclude data "$SRC_DIR"/ "$APP_DIR"/

(cd "$APP_DIR/frontend" && npm ci --silent && npm run build)
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --upgrade pip
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt"

if [ ! -f "$ENV_FILE" ]; then
  cp "$APP_DIR/.env.example" "$ENV_FILE"
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
