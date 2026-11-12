# Installation

PSADT Frontend runs on Linux, either as a Docker container or in a Debian LXC (for example on Proxmox). Both installs behave the same. The official PSADT 4.1.8 template is downloaded automatically during the install.

## Option 1: Proxmox helper script (recommended)

Run this **on the Proxmox host** (not inside a container):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/ct/psadt-frontend.sh)"
```

You get the familiar community-scripts menu. Choose **Default** for a Debian 13 container with 2 cores, 2 GB RAM and a 16 GB disk, or **Advanced** to pick storage, network and resources yourself. At the end the script shows the address and the admin password. The password is also saved in `/root/psadt-frontend-admin.txt` inside the container.

## Option 2: Docker

```bash
git clone https://github.com/Starf0x/PSADT-Frontend.git
cd PSADT-Frontend
cp .env.example .env        # adjust the settings
docker compose up -d --build
docker compose logs | grep 'admin password'
```

A ready-made image is also available: `ghcr.io/starf0x/psadt-frontend:latest`. Put it under `image:` instead of `build:` in `docker-compose.yml`. To update, run `docker compose pull && docker compose up -d`.

## Option 3: an existing Debian LXC

Run this as root **inside** the container:

```bash
PSADT_COOKIE_SECURE=false bash -c "$(curl -fsSL https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/lxc/install.sh)"
journalctl -u psadt-frontend | grep 'admin password'
```

## Opening the app

Open `http://<address>:8000` and sign in with the user `admin` and the password from the install. Change the password straight away under [Account](Account-and-language).

## Settings

Settings are environment variables (in `.env` for Docker, in the systemd service for the LXC).

| Variable | Default | Meaning |
|----------|---------|---------|
| `PSADT_ADMIN_USERNAME` | `admin` | Login name of the first administrator |
| `PSADT_ADMIN_PASSWORD` | empty | Empty: a password is generated at the first start and written to the log |
| `PSADT_COOKIE_SECURE` | `true` | Keep `true` behind HTTPS. Set `false` only when you open the app over plain `http://` |
| `PSADT_SESSION_HOURS` | `12` | How long a sign-in stays valid |
| `PSADT_MAX_UPLOAD_MB` | `4096` | Largest file you can upload |
| `PSADT_DATA_DIR` | `./data` | Where the database and uploads are stored |
| `PSADT_USAGE_OPTOUT` | empty | Set to `1` to turn off the anonymous daily check-in (version, Docker/LXC, number of days, a random id; nothing about your packages or users) |

> **Tip:** if you can't sign in over `http://`, `PSADT_COOKIE_SECURE` is probably still `true`. The browser then refuses the session cookie.

## HTTPS

For use outside your own network, put a reverse proxy with HTTPS in front of the app, such as Caddy, Traefik or Nginx Proxy Manager, and keep `PSADT_COOKIE_SECURE=true`.
