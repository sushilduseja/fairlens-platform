"""ARQ enqueue helpers."""

from arq import create_pool
from arq.connections import RedisSettings

from backend.core.config import settings


async def enqueue_audit_job(audit_id: str) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    try:
        await redis.enqueue_job("process_audit", audit_id)
    finally:
        await redis.close()
