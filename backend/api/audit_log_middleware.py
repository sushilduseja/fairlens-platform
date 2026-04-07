"""Middleware for generic state-changing API request logging."""

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.db.models import AuditLog
from backend.db.session import async_session


class AuditLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/v1/"):
            async with async_session() as session:
                session.add(
                    AuditLog(
                        user_id=None,
                        action="api.state_change",
                        resource_type="APIRequest",
                        resource_id=getattr(request.state, "request_id", str(uuid4())),
                        details={"method": request.method, "path": request.url.path, "status": response.status_code},
                    )
                )
                await session.commit()
        return response
