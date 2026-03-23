from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import dashboard, jobs, ranking, referrals, resumes, settings as settings_router
from app.core.config import get_settings
from app.db import Base, SessionLocal, engine
from app.services.bootstrap_service import seed_dictionary

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_dictionary(session)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(resumes.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(ranking.router, prefix=settings.api_prefix)
app.include_router(referrals.router, prefix=settings.api_prefix)
app.include_router(settings_router.router, prefix=settings.api_prefix)

if settings.frontend_dist.exists():
    assets_dir = settings.frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    def _frontend_index() -> Path:
        index_file = settings.frontend_dist / "index.html"
        if not index_file.exists():
            raise HTTPException(status_code=404, detail="Frontend build not found")
        return index_file

    @app.get("/", include_in_schema=False)
    def serve_frontend_root() -> FileResponse:
        return FileResponse(_frontend_index())

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_app(full_path: str) -> FileResponse:
        if full_path.startswith(("api/", "docs", "openapi.json", "redoc", "health")):
            raise HTTPException(status_code=404, detail="Not found")

        requested_file = settings.frontend_dist / full_path
        if requested_file.exists() and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(_frontend_index())
