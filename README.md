# PSADT Frontend

Een webinterface voor de [PowerShell App Deployment Toolkit](https://psappdeploytoolkit.com/) (PSADT v4). Draait als Docker-container of als losse LXC-installatie; beide werken identiek.

**Versie:** 0.0.50 (zie `VERSION`)

## Status en roadmap

| Stap | Inhoud | Status |
|------|--------|--------|
| 1 | Fundament: FastAPI + React, cookie-login, Docker, LXC | ✅ v0.0.50 |
| 2 | Package-editor op basis van het PSADT v4-template, uploads, live scriptpreview | gepland |
| 3 | Bouwen/exporteren: ZIP, `.intunewin`, detectieregels, snippetbibliotheek | gepland |
| 4 | Open source klaarmaken: rollen, CI, docs | gepland |

## Architectuur

```
backend/   FastAPI (Python 3.12+), SQLAlchemy + SQLite, argon2
  app/config.py      instellingen via PSADT_* env-variabelen
  app/db.py          modellen: users, sessions
  app/security.py    wachtwoorden, sessies, CSRF, eerste admin
  app/routers/auth.py  /api/auth/login | logout | me | password
  app/main.py        app, security headers, serveert frontend/dist
  tests/             pytest
frontend/  React 18 + Vite (build -> frontend/dist)
lxc/install.sh       installer voor Debian LXC (systemd-service)
Dockerfile, docker-compose.yml
```

## Beveiliging (ingebouwd)

- Sessie in een `HttpOnly`, `Secure`, `SameSite=Strict` cookie; alleen de sha256-hash van het token staat in de database, dus uitloggen trekt de sessie echt in.
- CSRF-token (header `X-CSRF-Token`) verplicht op alle schrijfacties.
- argon2-wachtwoordhashing, lockout na 5 foute pogingen (15 min), timing-veilige login.
- Security headers: CSP, X-Frame-Options, nosniff, Referrer-Policy; geen `/docs` in productie.
- Container draait als niet-root, read-only filesystem, alle capabilities gedropt.
- Voor online gebruik: zet er een reverse proxy met HTTPS voor (Caddy/Traefik).

## Starten met Docker

```bash
cp .env.example .env        # pas aan
docker compose up -d --build
docker compose logs | grep admin-wachtwoord   # als PSADT_ADMIN_PASSWORD leeg was
```

Open `http://<host>:8000`. Zonder HTTPS lokaal testen: zet `PSADT_COOKIE_SECURE=false`.

## Installeren in een LXC-container

In een Debian 12/13 LXC (bijv. Proxmox), als root:

```bash
git clone https://github.com/Starf0x/PSADT-Frontend.git && cd PSADT-Frontend
bash lxc/install.sh
journalctl -u psadt-frontend | grep admin-wachtwoord
```

Configuratie staat in `/etc/psadt-frontend.env`, data in `/var/lib/psadt-frontend`. Updaten: `git pull && bash lxc/install.sh`.

## Configuratie

| Variabele | Standaard | Uitleg |
|-----------|-----------|--------|
| `PSADT_ADMIN_USERNAME` | `admin` | Eerste gebruiker |
| `PSADT_ADMIN_PASSWORD` | leeg | Leeg = gegenereerd en eenmalig gelogd |
| `PSADT_COOKIE_SECURE` | `true` | Alleen `false` voor lokaal http |
| `PSADT_SESSION_HOURS` | `12` | Geldigheid van een sessie |
| `PSADT_DATA_DIR` | `./data` (`/data` in Docker) | Database-locatie |

## Ontwikkelen

```bash
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt && pytest
PSADT_COOKIE_SECURE=false uvicorn app.main:app --reload    # :8000
cd ../frontend && npm install && npm run dev                # :5173, proxy naar /api
```

## Versiebeleid

Start op 0.0.50 en verhoogt per release met 11 (0.0.61, 0.0.72, ...). Bij 100 of meer wordt het 0.1.0.

## Notities voor verder werken

- Stap 2 voegt PowerShell 7 toe aan de Docker-image en aan `lxc/install.sh`, zodat beide gelijk blijven.
- Nieuwe tabellen worden nu via `create_all` gemaakt; bij de eerste schemawijziging Alembic toevoegen.

## Licentie

MIT, zie `LICENSE`.
