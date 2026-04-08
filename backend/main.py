"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

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

    app.include_router(api_router)

    static_dir = Path(settings.STATIC_DIR)
    static_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = static_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/assets/{file_path:path}")
    async def serve_assets(file_path: str):
        full_path = assets_dir / file_path
        if not full_path.is_file():
            raise HTTPException(status_code=404, detail="Not found")

        resolved = full_path.resolve()
        if not resolved.is_relative_to(assets_dir.resolve()):
            raise HTTPException(status_code=403, detail="Forbidden")

        return FileResponse(full_path)

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        if path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")

        index_file = static_dir / "index.html"
        if index_file.is_file():
            return HTMLResponse(content=index_file.read_text(), media_type="text/html")

        raise HTTPException(status_code=404, detail="Not found")

    @app.on_event("startup")
    async def startup_event() -> None:
        await init_db()

    return app


app = create_app()
