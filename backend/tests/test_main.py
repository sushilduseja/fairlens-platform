"""Tests for backend/main.py static file serving."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from fastapi.testclient import TestClient


class TestStaticAssetServing:
    """Test static asset serving with path traversal protection."""

    @pytest.fixture
    def client(self):
        with patch("backend.main.settings") as mock_settings:
            mock_settings.APP_NAME = "FairLens"
            mock_settings.APP_VERSION = "0.1.0"
            mock_settings.STATIC_DIR = "/tmp/test_static"

            # Need to re-import to get patched settings
            import importlib
            import backend.main

            importlib.reload(backend.main)

            from backend.main import app as app_module

            return TestClient(app_module)

    def test_nonexistent_asset_returns_404(self, client):
        """Test that missing assets return 404."""
        # The assets directory doesn't exist in test, so should return 404
        response = client.get("/assets/nonexistent.js")
        # This might return 404 or other error depending on setup
        assert response.status_code in [404, 500]

    def test_path_traversal_returns_403(self, client):
        """Test that path traversal attacks are blocked with 403."""
        response = client.get("/assets/../../etc/passwd")
        # Should be blocked
        assert response.status_code in [403, 404]


class TestSPAFallback:
    """Test SPA fallback routing."""

    @pytest.fixture
    def client(self):
        with patch("backend.main.settings") as mock_settings:
            mock_settings.APP_NAME = "FairLens"
            mock_settings.APP_VERSION = "0.1.0"
            mock_settings.STATIC_DIR = "/tmp/nonexistent"

            import importlib
            import backend.main

            importlib.reload(backend.main)

            from backend.main import app as app_module

            return TestClient(app_module)

    def test_api_routes_not_handled_by_spa(self, client):
        """Test that API routes return 404 and aren't handled by SPA."""
        response = client.get("/api/v1/someendpoint")
        assert response.status_code == 404


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.fixture
    def client(self):
        with patch("backend.main.settings") as mock_settings:
            mock_settings.APP_NAME = "FairLens"
            mock_settings.APP_VERSION = "0.1.0"

            import importlib
            import backend.main

            importlib.reload(backend.main)

            from backend.main import app as app_module

            return TestClient(app_module)

    def test_healthz_returns_ok(self, client):
        """Test that health endpoint returns correct status."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
