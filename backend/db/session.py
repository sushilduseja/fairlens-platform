"""Database engine, session factory, and base model."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables. Used for dev/prototype; Alembic for production migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        dialect = conn.dialect.name
        if dialect == "sqlite":
            await conn.exec_driver_sql(
                """
                CREATE TRIGGER IF NOT EXISTS audit_logs_no_update
                BEFORE UPDATE ON audit_logs
                BEGIN
                    SELECT RAISE(FAIL, 'audit_logs is append-only');
                END;
                """
            )
            await conn.exec_driver_sql(
                """
                CREATE TRIGGER IF NOT EXISTS audit_logs_no_delete
                BEFORE DELETE ON audit_logs
                BEGIN
                    SELECT RAISE(FAIL, 'audit_logs is append-only');
                END;
                """
            )
        elif dialect == "postgresql":
            await conn.exec_driver_sql(
                """
                CREATE OR REPLACE FUNCTION protect_audit_logs_append_only()
                RETURNS trigger AS $$
                BEGIN
                    RAISE EXCEPTION 'audit_logs is append-only';
                END;
                $$ LANGUAGE plpgsql;
                """
            )
            await conn.exec_driver_sql(
                """
                DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs;
                CREATE TRIGGER audit_logs_no_update
                BEFORE UPDATE ON audit_logs
                FOR EACH ROW EXECUTE FUNCTION protect_audit_logs_append_only();
                """
            )
            await conn.exec_driver_sql(
                """
                DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs;
                CREATE TRIGGER audit_logs_no_delete
                BEFORE DELETE ON audit_logs
                FOR EACH ROW EXECUTE FUNCTION protect_audit_logs_append_only();
                """
            )
