"""Backend authentication tests."""

import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_valid_returns_201(self, client: AsyncClient):
        """Test that valid registration returns 201."""
        unique_email = f"test-{uuid4().hex[:8]}@example.com"
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "name": "Test User", "password": "password123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert "api_key" in data
        assert data["api_key"].startswith("fl_")

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, client: AsyncClient):
        """Test that duplicate email registration returns 409."""
        unique_email = f"test-{uuid4().hex[:8]}@example.com"
        await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "name": "Test", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "name": "Test", "password": "password123"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_login_invalid_credentials_returns_401(self, client: AsyncClient):
        """Test that invalid credentials return 401."""
        response = await client.post(
            "/api/v1/auth/login", json={"email": "wrong@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test protected endpoint access control."""

    @pytest.mark.asyncio
    async def test_audits_requires_auth(self, client: AsyncClient):
        """Test that /audits endpoint requires authentication."""
        response = await client.get("/api/v1/audits")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_models_requires_auth(self, client: AsyncClient):
        """Test that /models endpoint requires authentication."""
        response = await client.get("/api/v1/models")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self, client: AsyncClient):
        """Test that health endpoint doesn't require auth."""
        response = await client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestTokenValidation:
    """Test JWT token validation."""

    def test_decode_invalid_token_returns_none(self):
        """Test that decoding invalid token returns None."""
        from backend.core.security import decode_access_token

        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_decode_valid_token_returns_payload(self):
        """Test that valid token returns payload."""
        from backend.core.security import create_access_token, decode_access_token

        token = create_access_token("user-123")
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == "user-123"
        assert "exp" in payload
        assert "iat" in payload


class TestAPIKeyValidation:
    """Test API key validation."""

    def test_generate_api_key_has_prefix(self):
        """Test that generated API key has configured prefix."""
        from backend.core.security import generate_api_key
        from backend.core.config import settings

        key = generate_api_key()
        assert key.startswith(settings.API_KEY_PREFIX)

    def test_generate_api_key_is_unique(self):
        """Test that generated API keys are unique."""
        from backend.core.security import generate_api_key

        keys = [generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100
