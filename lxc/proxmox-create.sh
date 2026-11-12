#!/usr/bin/env bash
# Draai dit op de Proxmox VE-host (als root). Maakt een Debian 12-LXC aan en installeert PSADT Frontend erin.
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/lxc/proxmox-create.sh)"
#
# Zolang de repo privé is (fine-grained token met Contents: Read-only op de repo):
#   export GITHUB_TOKEN=<token>
#   bash -c "$(curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.raw" https://api.github.com/repos/Starf0x/PSADT-Frontend/contents/lxc/proxmox-create.sh)"
#
# Alles is aan te passen via omgevingsvariabelen, bijv. CTID=120 IP=192.168.1.50/24 GW=192.168.1.1 bash ...
set -euo pipefail

REPO="${PSADT_REPO:-Starf0x/PSADT-Frontend}"
BRANCH="${PSADT_BRANCH:-main}"
CTID="${CTID:-$(pvesh get /cluster/nextid)}"
CT_HOSTNAME="${CT_HOSTNAME:-psadt-frontend}"
STORAGE="${STORAGE:-}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
CORES="${CORES:-2}"
MEMORY="${MEMORY:-2048}"
DISK="${DISK:-16}"
BRIDGE="${BRIDGE:-vmbr0}"
IP="${IP:-dhcp}"
GW="${GW:-}"
# Zonder HTTPS-proxy ervoor moet dit false zijn, anders kan de browser niet inloggen via http://
COOKIE_SECURE="${COOKIE_SECURE:-false}"

command -v pct >/dev/null || { echo "Dit script moet op een Proxmox VE-host draaien."; exit 1; }
[ "$(id -u)" -eq 0 ] || { echo "Draai dit script als root."; exit 1; }
if pct status "$CTID" >/dev/null 2>&1; then echo "CT $CTID bestaat al; kies een andere CTID."; exit 1; fi

# Opslag voor de container: opgegeven, anders de lokale opslag (geen nfs/cifs) met de meeste vrije ruimte (min. 2x DISK)
PVESM=$(pvesm status -content rootdir 2>/dev/null | awk 'NR>1 && $3=="active"')
ROOTDIR_STORES=$(echo "$PVESM" | awk '{print $1}')
if [ -z "$STORAGE" ]; then
  STORAGE=$(echo "$PVESM" | awk -v need=$((DISK * 2 * 1024 * 1024)) '$2!="nfs" && $2!="cifs" && $6>=need {print $6, $1}' | sort -nr | head -1 | cut -d" " -f2)
fi
if [ -z "$STORAGE" ] || ! echo "$ROOTDIR_STORES" | grep -qx "$STORAGE"; then
  echo "Geen geschikte opslag gevonden. Beschikbaar voor containers:"
  echo "$PVESM" | awk '{printf "  %-12s %-8s %6.0f GB vrij\n", $1, $2, $6/1048576}'
  echo "Kies er een met: STORAGE=<naam> bash ..."
  exit 1
fi
echo "==> Opslag: $STORAGE"

echo "==> Debian 12-template zoeken"
pveam update >/dev/null
TEMPLATE=$(pveam available --section system | awk '/debian-12-standard/ {print $2}' | sort -V | tail -1)
[ -n "$TEMPLATE" ] || { echo "Geen debian-12-standard template gevonden."; exit 1; }
if ! pveam list "$TEMPLATE_STORAGE" | grep -q "$TEMPLATE"; then
  pveam download "$TEMPLATE_STORAGE" "$TEMPLATE"
fi

NET="name=eth0,bridge=$BRIDGE,ip=$IP"
[ -n "$GW" ] && NET="$NET,gw=$GW"

echo "==> LXC $CTID ($CT_HOSTNAME) aanmaken"
pct create "$CTID" "$TEMPLATE_STORAGE:vztmpl/$TEMPLATE" \
  --hostname "$CT_HOSTNAME" --cores "$CORES" --memory "$MEMORY" --swap 512 \
  --rootfs "$STORAGE:$DISK" --net0 "$NET" \
  --unprivileged 1 --features nesting=1 --onboot 1 --ostype debian
pct start "$CTID"

echo "==> Wachten op netwerk"
for _ in $(seq 1 60); do
  pct exec "$CTID" -- getent hosts github.com >/dev/null 2>&1 && break
  sleep 2
done

echo "==> PSADT Frontend installeren (dit duurt een paar minuten)"
TOKEN_FILE=$(mktemp)
chmod 600 "$TOKEN_FILE"
printf '%s' "${GITHUB_TOKEN:-}" > "$TOKEN_FILE"
pct push "$CTID" "$TOKEN_FILE" /root/.psadt-token --perms 600
rm -f "$TOKEN_FILE"
pct exec "$CTID" -- bash -c "
  set -e
  apt-get update -qq && apt-get install -y -qq curl ca-certificates git >/dev/null
  T=\$(cat /root/.psadt-token); rm -f /root/.psadt-token
  URL=https://github.com/$REPO.git
  [ -n \"\$T\" ] && URL=https://x-access-token:\$T@github.com/$REPO.git
  rm -rf /opt/psadt-frontend-src
  git clone -q --depth 1 -b $BRANCH \"\$URL\" /opt/psadt-frontend-src
  git -C /opt/psadt-frontend-src remote set-url origin https://github.com/$REPO.git
  PSADT_COOKIE_SECURE=$COOKIE_SECURE bash /opt/psadt-frontend-src/lxc/install.sh
"

CT_IP=$(pct exec "$CTID" -- hostname -I | awk '{print $1}')
PW=$(pct exec "$CTID" -- journalctl -u psadt-frontend --no-pager | grep -o "admin-wachtwoord voor 'admin': .*" | tail -1 | sed "s/.*: //")
echo
echo "Klaar! PSADT Frontend draait in CT $CTID."
echo "  URL:        http://$CT_IP:8000"
echo "  Gebruiker:  admin"
echo "  Wachtwoord: ${PW:-zie: pct exec $CTID -- journalctl -u psadt-frontend | grep admin-wachtwoord}"
[ "$COOKIE_SECURE" = "false" ] && echo "  Let op: cookies werken nu over http. Zet er voor productie een HTTPS-proxy voor en zet PSADT_COOKIE_SECURE=true in /etc/psadt-frontend.env."
echo "Updaten: pct exec $CTID -- bash /opt/psadt-frontend-src/lxc/install.sh"
