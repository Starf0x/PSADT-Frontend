# PSADT Frontend

> **English:** A self-hosted web UI for building [PSAppDeployToolkit](https://psappdeploytoolkit.com/) v4 packages: edit install/uninstall/repair steps in a browser, upload installers, preview the generated `Invoke-AppDeployToolkit.ps1`, and export a ready-to-deploy ZIP or Intune `.intunewin` — no Windows build machine needed. Runs as a Docker container or in a Debian LXC. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

Een webinterface voor de [PowerShell App Deployment Toolkit](https://psappdeploytoolkit.com/) (PSADT v4). Draait als Docker-container of als losse LXC-installatie; beide werken identiek.

**Versie:** 0.1.0 (zie `VERSION`)

## Status en roadmap

| Stap | Inhoud | Status |
|------|--------|--------|
| 1 | Fundament: FastAPI + React, cookie-login, Docker, LXC | ✅ v0.0.50 |
| 2 | Package-editor op basis van het PSADT v4-template, uploads, live scriptpreview | ✅ v0.0.61 |
| 3 | Bouwen/exporteren: ZIP, `.intunewin`, detectieregels, snippetbibliotheek | ✅ v0.0.72 |
| 4 | Open source klaarmaken: rollen, gebruikersbeheer, docs, GHCR-image | ✅ v0.0.83 |

## Architectuur

```
backend/   FastAPI (Python 3.12+), SQLAlchemy + SQLite, argon2
  app/config.py      instellingen via PSADT_* env-variabelen
  app/db.py          modellen: users, sessions
  app/security.py    wachtwoorden, sessies, CSRF, eerste admin
  app/routers/auth.py  /api/auth/login | logout | me | password
  app/routers/packages.py  /api/packages CRUD, /script, /check, /files
  app/psadt/schema.py      toegestane stap-types + validatie (whitelist)
  app/psadt/generator.py   bouwt Invoke-AppDeployToolkit.ps1
  app/psadt/template_*.ps1 kop/staart van het officiële PSADT 4.1.8-template
  app/psadt/check.ps1      syntaxcontrole met de PowerShell-parser (voert niets uit)
  app/psadt/export.py      ZIP (officieel PSADT-pakket + script + Files) en .intunewin
  app/psadt/detection.py   Intune-detectiescript uit detectieregels
  app/routers/snippets.py  /api/snippets (herbruikbare stappen)
  app/routers/users.py     /api/users (alleen beheerders)
  app/main.py        app, security headers, serveert frontend/dist
  tests/             pytest
frontend/  React 18 + Vite (build -> frontend/dist); src/Packages.jsx, Editor.jsx, steps.js
.github/workflows/  ci.yml (tests + build), release.yml (tag + release uit VERSION)
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

## Rollen

| Rol | Mag |
|-----|-----|
| Beheerder | alles, plus gebruikers beheren (aanmaken, rol, wachtwoord, ontgrendelen, verwijderen) |
| Bewerker | pakketten en snippets maken, wijzigen en verwijderen |
| Alleen lezen | alles bekijken, scripts controleren en exporteren |

Bij een rol- of wachtwoordwijziging worden de sessies van die gebruiker ingetrokken. De laatste beheerder kan niet worden gedegradeerd of verwijderd.

## Starten met Docker

Kant-en-klare image (na elke release): `ghcr.io/starf0x/psadt-frontend:latest` (zet in `docker-compose.yml` `image:` in plaats van `build:`).

```bash
cp .env.example .env        # pas aan
docker compose up -d --build
docker compose logs | grep admin-wachtwoord   # als PSADT_ADMIN_PASSWORD leeg was
```

Open `http://<host>:8000`. Zonder HTTPS lokaal testen: zet `PSADT_COOKIE_SECURE=false`.

## Installeren in een LXC-container (Proxmox)

**Op de Proxmox-host** (maakt zelf een Debian 12-LXC aan en installeert de app erin):

```bash
# Zolang de repo privé is: fine-grained token, alleen deze repo, Repository permissions → Contents: Read-only
export GITHUB_TOKEN=<token>
bash -c "$(curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.raw" https://api.github.com/repos/Starf0x/PSADT-Frontend/contents/lxc/proxmox-create.sh)"

# Als de repo publiek is:
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/lxc/proxmox-create.sh)"
```

Aanpasbaar met variabelen, bijv. `CTID=120 IP=192.168.1.50/24 GW=192.168.1.1 STORAGE=local-zfs MEMORY=4096`. Standaard: DHCP, `vmbr0`, 2 cores, 2 GB RAM, 16 GB disk, unprivileged met nesting; opslag wordt automatisch gekozen: lokale opslag (geen NFS/CIFS) met de meeste vrije ruimte, zie `pvesm status -content rootdir`. Aan het eind toont het script de URL en het admin-wachtwoord.

Let op: gebruik de **raw**-link (`raw.githubusercontent.com`), niet de `github.com/.../blob/...`-link; die geeft HTML (of 404 bij een privé-repo).

**In een bestaande Debian-LXC** (als root, niet op de host):

```bash
GITHUB_TOKEN=<token> PSADT_COOKIE_SECURE=false bash -c "$(curl -fsSL -H "Authorization: Bearer <token>" -H "Accept: application/vnd.github.raw" https://api.github.com/repos/Starf0x/PSADT-Frontend/contents/lxc/install.sh)"
journalctl -u psadt-frontend | grep admin-wachtwoord
```

Configuratie staat in `/etc/psadt-frontend.env`, data in `/var/lib/psadt-frontend`, broncode in `/opt/psadt-frontend-src`.
Updaten: `GITHUB_TOKEN=<token> bash /opt/psadt-frontend-src/lxc/install.sh` (zonder token zodra de repo publiek is).

`PSADT_COOKIE_SECURE=false` is nodig zolang je via `http://` werkt; zet hem op `true` zodra er een HTTPS-proxy voor staat.

## Configuratie

| Variabele | Standaard | Uitleg |
|-----------|-----------|--------|
| `PSADT_ADMIN_USERNAME` | `admin` | Eerste gebruiker |
| `PSADT_ADMIN_PASSWORD` | leeg | Leeg = gegenereerd en eenmalig gelogd |
| `PSADT_COOKIE_SECURE` | `true` | Alleen `false` voor lokaal http |
| `PSADT_SESSION_HOURS` | `12` | Geldigheid van een sessie |
| `PSADT_DATA_DIR` | `./data` (`/data` in Docker) | Database en uploads |
| `PSADT_MAX_UPLOAD_MB` | `4096` | Maximale uploadgrootte |
| `PSADT_TOOLKIT_ZIP` | `/opt/psadt/PSAppDeployToolkit_Template_v4.zip` | Officieel PSADT-pakket voor export |
| `PSADT_PWSH_PATH` | `pwsh` (`/opt/pwsh/pwsh` in Docker/LXC) | PowerShell 7 voor syntaxcontrole |

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

- PowerShell 7.4.6 staat in de Docker-image én via `lxc/install.sh` in `/opt/pwsh`; versie op beide plekken gelijk houden.
- Nieuw PSADT-template: kop/staart opnieuw uit `src/PSAppDeployToolkit/Frontend/v4/Invoke-AppDeployToolkit.ps1` halen (pad `..\..\..\PSAppDeployToolkit` vervangen door `PSAppDeployToolkit`) en `PSADT_VERSION` in `schema.py` aanpassen.
- Releases: verhoog `VERSION` (+11) en `frontend/package.json`; na merge maakt `release.yml` de tag en release.
- Nieuwe PSADT-versie: `PSADT_VERSION` + `PSADT_SHA256` in Dockerfile én `lxc/install.sh`, plus kop/staart van het template en `PSADT_VERSION` in `schema.py`.
- De .intunewin is cryptografisch getest (roundtrip), maar nog niet daadwerkelijk in Intune geüpload: eerste keer controleren.
- Lokaal ontwikkelen zonder `/opt/psadt`: download de template-zip en zet `PSADT_TOOLKIT_ZIP`.
- Open source maken: repo op *Public* zetten, en het GHCR-package op *Public* (Package settings). Alle docs (CONTRIBUTING, SECURITY, NOTICE, issue templates, Dependabot) staan klaar.
- Mogelijke vervolgstappen: 2FA (TOTP), audit-log, Alembic-migraties, Engelstalige UI.
- Nieuwe tabellen worden nu via `create_all` gemaakt; bij de eerste schemawijziging Alembic toevoegen.

## Licentie

MIT, zie `LICENSE`. PSADT-onderdelen: LGPL-3.0, zie `NOTICE.md`.
