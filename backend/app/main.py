from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db as dbmod
from .config import settings
from .routers import auth

VERSION = (Path(__file__).resolve().parents[2] / "VERSION")
APP_VERSION = VERSION.read_text().strip() if VERSION.exists() else "0.0.50"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if dbmod.SessionLocal is None:
        dbmod.init_db()
    with dbmod.SessionLocal() as db:
        from .security import ensure_admin

        ensure_admin(db)
    yield


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
    return response


app.include_router(auth.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": APP_VERSION}


static_dir = settings.static_dir.resolve()
if (static_dir / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        return FileResponse(static_dir / "index.html")
