"""Tests for backend/core/config.py."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSettings:
    """Test configuration settings."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch("backend.core.config.Settings") as MockSettings:
            from backend.core.config import settings

            assert settings.APP_NAME == "FairLens"
            assert settings.APP_VERSION == "0.1.0"
            assert settings.DEBUG == False

    def test_database_url_default(self):
        """Test default database URL."""
        from backend.core.config import settings

        assert settings.DATABASE_URL == "sqlite+aiosqlite:///./fairlens.db"

    def test_redis_url_default(self):
        """Test default Redis URL."""
        from backend.core.config import settings

        assert settings.REDIS_URL == "redis://localhost:6379"

    def test_static_dir_default(self):
        """Test default static directory."""
        from backend.core.config import settings

        assert settings.STATIC_DIR == "./static"

    def test_upload_dir_default(self):
        """Test default upload directory."""
        from backend.core.config import settings

        assert settings.UPLOAD_DIR == "./uploads"

    def test_secret_key_has_default(self):
        """Test that secret key has a default value."""
        from backend.core.config import settings

        assert len(settings.SECRET_KEY) > 0

    def test_access_token_expire_minutes_default(self):
        """Test default token expiry."""
        from backend.core.config import settings

        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440

    def test_upload_path_property_creates_directory(self, tmp_path):
        """Test that upload_path property creates directory if not exists."""
        with patch("backend.core.config.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path_instance.mkdir = MagicMock()
            mock_path.return_value = mock_path_instance

            from backend.core.config import settings

            settings.UPLOAD_DIR = str(tmp_path / "test_uploads")
            result = settings.upload_path
            mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)
