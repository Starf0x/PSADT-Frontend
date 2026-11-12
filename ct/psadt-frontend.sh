#!/usr/bin/env bash
# PSADT Frontend, als Proxmox VE Helper Script (zelfde opbouw als My Audiobook Collection).
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/ct/psadt-frontend.sh)"
#
# De engine (menu Default/Advanced, opslagkeuze, spinners, Notes) komt van community-scripts/core.
# COMMUNITY_SCRIPTS_URL wijst de engine naar deze repo, zodat hij install/psadtfrontend-install.sh
# hier ophaalt in plaats van uit hun repo (waar het niet bestaat).
# Let op: de engine haalt bestanden zonder token op, dus dit werkt alleen als de repo publiek is.
export COMMUNITY_SCRIPTS_URL="${COMMUNITY_SCRIPTS_URL:-https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main}"

_cs_boot="${COMMUNITY_SCRIPTS_CORE_DIR:-$(dirname "${BASH_SOURCE[0]}")/../../core}/core/build.func"
source "$_cs_boot" 2>/dev/null || source <(curl -fsSL "${COMMUNITY_SCRIPTS_CORE_URL:-https://raw.githubusercontent.com/community-scripts/core/main}/core/build.func")
# Copyright (c) 2021-2026 community-scripts ORG
# License: MIT | https://github.com/community-scripts/ProxmoxVE/raw/main/LICENSE
# Source: https://github.com/Starf0x/PSADT-Frontend

APP="PSADT Frontend"

# Eigen banner; de engine heeft geen header voor apps buiten zijn repo.
IFS= read -r -d '' _CS_FALLBACK_HEADER <<'ART' || true
 ____  ____    _    ____ _____   _____                _                 _
|  _ \/ ___|  / \  |  _ \_   _| |  ___| __ ___  _ __ | |_ ___ _ __   __| |
| |_) \___ \ / _ \ | | | || |   | |_ | '__/ _ \| '_ \| __/ _ \ '_ \ / _` |
|  __/ ___) / ___ \| |_| || |   |  _|| | | (_) | | | | ||  __/ | | | (_| |
|_|   |____/_/   \_\____/ |_|   |_|  |_|  \___/|_| |_|\__\___|_| |_|\__,_|
ART

var_tags="${var_tags:-deployment;windows}"
var_cpu="${var_cpu:-2}"
var_ram="${var_ram:-2048}"
var_disk="${var_disk:-16}"
var_os="${var_os:-debian}"
var_version="${var_version:-13}"
# Unprivileged: de app schrijft alleen in zijn eigen datamap, er zijn geen bind mounts nodig.
var_unprivileged="${var_unprivileged:-1}"

header_info "$APP"
variables
color
catch_errors

function update_script() {
  header_info
  check_container_storage
  check_container_resources

  if [[ ! -d /opt/psadt-frontend-src/.git ]]; then
    msg_error "No ${APP} Installation Found!"
    exit
  fi

  msg_info "Updating ${APP}"
  cd /opt/psadt-frontend-src || exit
  # Nieuwste release-tag, niet main: een tag heeft CI doorstaan en is gepubliceerd.
  $STD git fetch --tags --force
  newest=$(git tag --sort=-v:refname | head -n 1)
  if [[ -z "$newest" ]]; then
    msg_error "No released version found in the repository"
    exit
  fi
  if [[ "$(git describe --tags --exact-match 2>/dev/null)" == "$newest" ]]; then
    msg_ok "Already on ${newest}"
    exit
  fi
  $STD git checkout "$newest"
  PSADT_SKIP_FETCH=1 $STD bash /opt/psadt-frontend-src/lxc/install.sh
  echo "$newest" >/opt/psadt-frontend_version.txt
  msg_ok "Updated to ${newest}"
  exit
}

# Notes-paneel in de Proxmox-GUI (vervangt die van de engine, die naar een niet-bestaande pagina linkt).
description() {
  IP=$(pct exec "$CTID" ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)
  local repo="https://github.com/Starf0x/PSADT-Frontend"
  local notes
  notes=$(
    cat <<NOTES
<div align='center'>
  <h2 style='font-size: 24px; margin: 20px 0;'>${APP}</h2>
  <p style='margin: 16px 0;'>
    <a href='http://${IP}:8000' target='_blank' rel='noopener noreferrer' style='text-decoration: none; color: #00617f;'>http://${IP}:8000</a>
  </p>
  <span style='margin: 0 10px;'>
    <a href='${repo}' target='_blank' rel='noopener noreferrer' style='text-decoration: none; color: #00617f;'>GitHub</a>
  </span>
  <span style='margin: 0 10px;'>
    <a href='${repo}/issues' target='_blank' rel='noopener noreferrer' style='text-decoration: none; color: #00617f;'>Issues</a>
  </span>
</div>
NOTES
  )
  pct set "$CTID" -description "$notes"
}

start
build_container
description

PW=$(pct exec "$CTID" -- cat /root/psadt-frontend-admin.txt 2>/dev/null || true)

msg_ok "Completed successfully!\n"
echo -e "${CREATING}${GN}${APP} setup has been successfully initialized!${CL}"
echo -e "${INFO}${YW}Access it using the following URL:${CL}"
echo -e "${TAB}${GATEWAY}${BGN}http://${IP}:8000${CL}"
echo -e "${INFO}${YW}Login:${CL}"
echo -e "${TAB}${GATEWAY}${BGN}admin / ${PW:-see /root/psadt-frontend-admin.txt in the container}${CL}"
echo -e "${INFO}${YW}Settings (restart the service after editing):${CL}"
echo -e "${TAB}${GATEWAY}${BGN}/etc/psadt-frontend.env${CL}"
echo -e "${INFO}${YW}Cookies work over http:// now. For production put an HTTPS proxy in front and set PSADT_COOKIE_SECURE=true.${CL}"
