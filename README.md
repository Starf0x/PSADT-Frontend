# PSADT Frontend

Een webinterface voor de [PowerShell App Deployment Toolkit](https://psappdeploytoolkit.com/) (PSADT v4). Draait als Docker-container of als losse LXC-installatie; beide werken identiek.

**Versie:** 0.0.72 (zie `VERSION`)

## Status en roadmap

| Stap | Inhoud | Status |
|------|--------|--------|
| 1 | Fundament: FastAPI + React, cookie-login, Docker, LXC | ✅ v0.0.50 |
| 2 | Package-editor op basis van het PSADT v4-template, uploads, live scriptpreview | ✅ v0.0.61 |
| 3 | Bouwen/exporteren: ZIP, `.intunewin`, detectieregels, snippetbibliotheek | ✅ v0.0.72 |
| 4 | Open source klaarmaken: rollen, CI, docs | gepland |

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

## Package-editor (stap 2)

- Pakket aanmaken: start met dezelfde stappen als het officiële v4-template (welkomstvenster + voortgang).
- Per fase (Voor / Hoofdactie / Na) van Installatie, Deïnstallatie en Reparatie stappen toevoegen, ordenen en verwijderen.
- Stap-types: MSI, EXE, applicatie verwijderen op naam, register zetten/verwijderen, bestand kopiëren, bestand/map verwijderen, welkomstvenster, voortgang, eigen PowerShell.
- Bestanden uploaden naar de map `Files` van het pakket (`/data/packages/<id>/Files`), met een whitelist van extensies.
- Tab *Script*: live preview, download (UTF-8 met BOM, CRLF) en syntaxcontrole via PowerShell 7 in de container.
- Veiligheid: alle invoer komt als letterlijke string (enkele quotes) in het script; bestandsnamen zijn gevalideerd; het script wordt op de server nooit uitgevoerd.

## Export (stap 3)

- **ZIP:** het officiële `PSAppDeployToolkit_Template_v4.zip` (4.1.8, sha256 gecontroleerd) met het gegenereerde `Invoke-AppDeployToolkit.ps1` en de geüploade bestanden in `Files/`.
- **.intunewin:** zelfde formaat als Microsofts IntuneWinAppUtil (AES-256-CBC + HMAC-SHA256, `Detection.xml`), gebouwd in Python, dus zonder Windows. Setup-bestand: `Invoke-AppDeployToolkit.exe`.
- **Detectie:** regels (MSI ProductCode, bestand met minimale versie, registerwaarde) worden een Intune-detectiescript (alle regels moeten kloppen).
- **Snippets:** ☆ op een stap slaat hem op; daarna kies je hem bij *Stap toevoegen*.
- Tijdelijke exportbestanden staan in `$PSADT_DATA_DIR/tmp` en worden na de download verwijderd.

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
- Stap 4: rollen/gebruikersbeheer, docs, open source klaarmaken.
- Nieuwe tabellen worden nu via `create_all` gemaakt; bij de eerste schemawijziging Alembic toevoegen.

## Licentie

MIT, zie `LICENSE`.
