"""FairLens Platform — Core configuration via environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "FairLens"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./fairlens.db"

    # ── Redis (ARQ job queue) ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── Auth ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    API_KEY_PREFIX: str = "fl_"

    # ── File uploads ─────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 500

    # ── Paths ────────────────────────────────────────────────────────────
    STATIC_DIR: str = "./static"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
