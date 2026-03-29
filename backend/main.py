import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.auth import hash_password
from backend.config import settings
from backend.database import Base, SessionLocal, engine
from backend.models import AdminConfig
from backend.routers import auth, domains, logs, status, users
from backend.services.log_watcher import LogWatcher


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log_watcher = LogWatcher()


def seed_admin(db: Session) -> None:
    entry = db.get(AdminConfig, "admin_password_hash")
    if not entry:
        db.add(AdminConfig(key="admin_password_hash", value=hash_password(settings.admin_password)))
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.client_output_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_admin(db)
    await log_watcher.start()
    yield
    await log_watcher.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(domains.router)
app.include_router(logs.router)
app.include_router(status.router)


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}


if settings.frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=settings.frontend_dir), name="static")


@app.get("/")
def serve_index():
    index = settings.frontend_dir / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": settings.app_name}


@app.get("/dashboard")
def serve_dashboard():
    page = settings.frontend_dir / "dashboard.html"
    if page.exists():
        return FileResponse(page)
    return {"message": "Dashboard not found"}

