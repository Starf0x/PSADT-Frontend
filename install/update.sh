#!/usr/bin/env bash
# Updates PSADT Frontend in place, as root, to the newest released version.
#
# Run it yourself:   psadt-frontend-update
# Or from the app:   System → "A newer version is available" → Install it
#
# The app runs as the unprivileged 'psadt' user and cannot write in /opt or restart
# its own unit, which is how it should be. It leaves a file in its data folder instead;
# the root path unit psadt-frontend-update.path sees it and starts this script, which
# only ever does this one fixed thing.
set -euo pipefail

SRC_DIR=/opt/psadt-frontend-src
DATA_DIR=/var/lib/psadt-frontend
UNIT=psadt-frontend.service
ASK="$DATA_DIR/update-wanted"
SAID="$DATA_DIR/update-said.json"
PROG="$DATA_DIR/update-progress.json"
STEPS=6

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
step() {
  printf '{"at":"%s","step":%s,"of":%s,"doing":"%s","done":false}\n' "$(date -Iseconds)" "$1" "$STEPS" "$2" >"$PROG"
  chown psadt:psadt "$PROG" 2>/dev/null || true
  say "$2"
}

[ "$(id -u)" -eq 0 ] || { printf 'Run this as root.\n' >&2; exit 1; }
[ -d "$SRC_DIR/.git" ] || { printf 'No git checkout at %s: this is not an LXC install.\n' "$SRC_DIR" >&2; exit 1; }

# Clear the request first, whatever happens next; left behind, the path unit would
# start this again the moment it exits.
rm -f "$ASK"

was=$(git -C "$SRC_DIR" describe --tags --exact-match 2>/dev/null || echo 'an unreleased checkout')
finish() {
  printf '{"at":"%s","from":"%s","to":"%s","ok":%s,"said":"%s"}\n' "$(date -Iseconds)" "$was" "${2:-$was}" "$1" "${3:-}" >"$SAID"
  printf '{"at":"%s","step":%s,"of":%s,"doing":"finished","done":true,"ok":%s,"to":"%s","said":"%s"}\n' \
    "$(date -Iseconds)" "$STEPS" "$STEPS" "$1" "${2:-$was}" "${3:-}" >"$PROG"
  chown psadt:psadt "$SAID" "$PROG" 2>/dev/null || true
}
# On failure: say so, and make sure the app is running again (on whatever is in place).
trap 'finish false "" "it stopped part way through; see journalctl -u psadt-frontend-update"; systemctl start "$UNIT" || true' ERR

step 1 "Looking for a newer version"
git -C "$SRC_DIR" fetch --tags --force --quiet
newest=$(git -C "$SRC_DIR" tag --sort=-v:refname | head -n 1)
if [ -z "$newest" ]; then
  finish false "" "no released version found in the repository"
  exit 1
fi
if [ "$was" = "$newest" ]; then
  say "Already on $newest"
  finish true "$newest" "already the newest"
  exit 0
fi

say "Updating $was to $newest"
step 2 "Stopping the app"
systemctl stop "$UNIT"
step 3 "Fetching the new version"
git -C "$SRC_DIR" checkout --quiet "$newest"
# Same install path as a fresh install and the Proxmox helper's update; it also puts
# the new version of this script and its units in place for the next run.
step 4 "Installing the new version (dependencies and build, this takes a few minutes)"
PSADT_SKIP_FETCH=1 bash "$SRC_DIR/lxc/install.sh"
step 5 "Starting the app"
systemctl start "$UNIT"
echo "$newest" >/opt/psadt-frontend_version.txt

# Started is not running: a unit that dies after a second leaves `systemctl start` happy.
step 6 "Checking it stays up"
sleep 3
if systemctl is-active --quiet "$UNIT"; then
  finish true "$newest" ""
  say "Now on $newest"
else
  finish false "$newest" "it updated but the service did not stay up; see journalctl -u $UNIT"
  journalctl -u "$UNIT" --no-pager -n 30 >&2 || true
  exit 1
fi
