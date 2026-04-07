"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.audit_log_middleware import AuditLogMiddleware
from backend.api.router import api_router
from backend.core.config import settings
from backend.core.errors import RequestIDMiddleware, register_error_handlers
from backend.db.session import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AuditLogMiddleware)
    register_error_handlers(app)

    static_dir = Path(settings.STATIC_DIR)
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        return HTMLResponse(content=(static_dir / "index.html").read_text(), media_type="text/html")

    app.include_router(api_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.on_event("startup")
    async def startup_event() -> None:
        await init_db()

    return app


app = create_app()
