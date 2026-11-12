#!/usr/bin/env bash
# Het binnenste deel van ct/psadt-frontend.sh: draait in de container nadat de engine hem heeft gemaakt.
#
# De bestandsnaam ligt vast: de engine maakt er `${APP,,}` zonder spaties + `-install` van,
# dus "PSADT Frontend" wordt `psadtfrontend-install.sh`. Niet hernoemen.
#
# Copyright (c) 2021-2026 community-scripts ORG
# License: MIT | https://github.com/community-scripts/ProxmoxVE/raw/main/LICENSE
# Source: https://github.com/Starf0x/PSADT-Frontend

source /dev/stdin <<<"$FUNCTIONS_FILE_PATH"
color
verb_ip6
catch_errors
setting_up_container
network_check
update_os

msg_info "Installing Dependencies"
$STD apt install -y git curl ca-certificates rsync python3 python3-venv
msg_ok "Installed Dependencies"

# Zelfde major als de Docker-build (node:22-alpine).
NODE_VERSION="22" setup_nodejs

msg_info "Fetching PSADT Frontend"
$STD git clone https://github.com/Starf0x/PSADT-Frontend.git /opt/psadt-frontend-src
cd /opt/psadt-frontend-src || exit
# Nieuwste release-tag in plaats van main.
NEWEST=$(git tag --sort=-v:refname | head -n 1)
if [[ -n "$NEWEST" ]]; then
  $STD git checkout "$NEWEST"
fi
echo "${NEWEST:-main}" >/opt/psadt-frontend_version.txt
msg_ok "Fetched ${NEWEST:-main}"

# Eén installatiepad voor LXC: lxc/install.sh (PowerShell 7, PSADT-toolkit met sha256-check,
# venv, frontend-build, systemd-unit). Zo blijven Docker en LXC gelijk.
msg_info "Installing PSADT Frontend (PowerShell, PSADT toolkit, build)"
PSADT_SKIP_FETCH=1 PSADT_COOKIE_SECURE=false $STD bash /opt/psadt-frontend-src/lxc/install.sh
msg_ok "Installed PSADT Frontend"

msg_info "Reading initial admin password"
PW=""
for _ in $(seq 1 30); do
  PW=$(journalctl -u psadt-frontend --no-pager 2>/dev/null | grep -o "admin-wachtwoord voor 'admin': .*" | tail -1 | sed "s/.*: //")
  [[ -n "$PW" ]] && break
  sleep 1
done
if [[ -n "$PW" ]]; then
  install -m 0600 /dev/null /root/psadt-frontend-admin.txt
  echo "$PW" >/root/psadt-frontend-admin.txt
fi
msg_ok "Admin password stored in /root/psadt-frontend-admin.txt"

motd_ssh
customize

msg_info "Cleaning up"
$STD apt -y autoremove
$STD apt -y autoclean
$STD apt -y clean
msg_ok "Cleaned"
