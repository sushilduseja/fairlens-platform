"""Root API router."""

from fastapi import APIRouter

from backend.api import audits, auth, metrics, models

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
