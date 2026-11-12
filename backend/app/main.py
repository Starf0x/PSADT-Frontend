import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db as dbmod
from .config import settings
from .routers import auth, packages, snippets, stats, system, users

# VERSION sits next to backend/ in the repo and LXC install, and in /app in the Docker image.
_here = Path(__file__).resolve()
VERSION = next((d / "VERSION" for d in (_here.parents[1], _here.parents[2]) if (d / "VERSION").is_file()), _here.parents[2] / "VERSION")
APP_VERSION = VERSION.read_text().strip() if VERSION.exists() else "0.0.50"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if dbmod.SessionLocal is None:
        dbmod.init_db()
    with dbmod.SessionLocal() as db:
        from .security import ensure_admin

        ensure_admin(db)
    task = asyncio.create_task(_purge_loop())
    yield
    task.cancel()


async def _purge_loop():
    """Hourly: remove old uploads (retention on the System page) and send the daily usage check-in."""
    from .retention import purge_old_uploads

    from .usage import report_once

    while True:
        try:
            with dbmod.SessionLocal() as db:
                purge_old_uploads(db)
        except Exception as e:  # noqa: BLE001 - keep the loop alive
            print(f"[psadt-frontend] upload cleanup failed: {e}", flush=True)
        try:
            with dbmod.SessionLocal() as db:
                await asyncio.to_thread(report_once, db, APP_VERSION)
        except Exception as e:  # noqa: BLE001
            print(f"[psadt-frontend] usage check-in failed: {e}", flush=True)
        await asyncio.sleep(3600)


app = FastAPI(title="PSADT Frontend", version=APP_VERSION, lifespan=lifespan, docs_url=None, redoc_url=None)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    h = response.headers
    h["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    h["X-Frame-Options"] = "DENY"
    h["X-Content-Type-Options"] = "nosniff"
    h["Referrer-Policy"] = "no-referrer"
    h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        h["Cache-Control"] = "no-store"
    elif request.url.path.startswith("/assets/"):
        h["Cache-Control"] = "public, max-age=31536000, immutable"  # file names change with every build
    else:
        h["Cache-Control"] = "no-cache"  # always ask for the newest page, so an update shows at once
    return response


app.include_router(auth.router)
app.include_router(packages.router)
app.include_router(snippets.router)
app.include_router(users.router)
app.include_router(system.router)
app.include_router(stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": APP_VERSION}


static_dir = settings.static_dir.resolve()
if (static_dir / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        # Files in the root of dist (favicon.svg, apple-touch-icon.png); everything else is the SPA.
        f = (static_dir / path).resolve()
        if path and "/" not in path and f.parent == static_dir and f.is_file():
            return FileResponse(f)
        return FileResponse(static_dir / "index.html")
