"""AuditLog helpers."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import AuditLog, User


async def log_action(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: str,
    user: User | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
    )
    await db.flush()
