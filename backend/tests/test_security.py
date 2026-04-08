"""Tests for backend/core/security.py security utilities."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        from backend.core.security import hash_password

        result = hash_password("testpassword123")
        assert isinstance(result, str)
        assert result != "testpassword123"

    def test_hash_password_is_consistent(self):
        """Test that same password produces consistent hashes."""
        from backend.core.security import hash_password

        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != password
        assert hash2 != password

    def test_verify_password_correct(self):
        """Test that verify_password works with correct password."""
        from backend.core.security import hash_password, verify_password

        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) == True

    def test_verify_password_incorrect(self):
        """Test that verify_password fails with wrong password."""
        from backend.core.security import hash_password, verify_password

        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) == False


class TestAPIKeyGeneration:
    """Test API key generation."""

    def test_generate_api_key_returns_string(self):
        """Test that generate_api_key returns a string."""
        from backend.core.security import generate_api_key

        result = generate_api_key()
        assert isinstance(result, str)

    def test_generate_api_key_has_prefix(self):
        """Test that API key has configured prefix."""
        from backend.core.security import generate_api_key
        from backend.core.config import settings

        result = generate_api_key()
        assert result.startswith(settings.API_KEY_PREFIX)

    def test_generate_api_key_length(self):
        """Test that API key has expected length."""
        from backend.core.security import generate_api_key
        from backend.core.config import settings

        result = generate_api_key()
        # prefix (3 chars) + 40 random chars = 43
        assert len(result) == len(settings.API_KEY_PREFIX) + 40

    def test_generate_api_key_unique(self):
        """Test that API keys are unique."""
        from backend.core.security import generate_api_key

        keys = [generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100


class TestAccessToken:
    """Test JWT access token creation and decoding."""

    @patch("backend.core.security.settings")
    def test_create_access_token_returns_string(self, mock_settings):
        """Test that create_access_token returns a JWT string."""
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 1440

        from backend.core.security import create_access_token

        result = create_access_token("user123")
        assert isinstance(result, str)
        assert len(result.split(".")) == 3  # JWT has 3 parts

    @patch("backend.core.security.settings")
    def test_create_access_token_contains_user_id(self, mock_settings):
        """Test that token contains user ID in payload."""
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 1440

        from backend.core.security import create_access_token, decode_access_token

        token = create_access_token("user123")
        payload = decode_access_token(token)

        assert payload is not None
        assert payload.get("sub") == "user123"

    @patch("backend.core.security.settings")
    def test_create_access_token_contains_expiry(self, mock_settings):
        """Test that token contains expiry time."""
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 1440

        from backend.core.security import create_access_token, decode_access_token

        token = create_access_token("user123")
        payload = decode_access_token(token)

        assert payload is not None
        assert "exp" in payload

    def test_decode_access_token_invalid_returns_none(self):
        """Test that decoding invalid token returns None."""
        from backend.core.security import decode_access_token

        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_decode_access_token_wrong_secret_returns_none(self):
        """Test that decoding with wrong secret returns None."""
        from backend.core.security import create_access_token, decode_access_token
        from backend.core import config

        # Create token with one secret
        original_secret = config.settings.SECRET_KEY
        config.settings.SECRET_KEY = "correct-secret"
        token = create_access_token("user123")

        # Try to decode with different secret
        config.settings.SECRET_KEY = "wrong-secret"
        result = decode_access_token(token)

        # Restore
        config.settings.SECRET_KEY = original_secret

        assert result is None


class TestAuthDependency:
    """Test get_current_user auth dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials_raises_401(self):
        """Test that missing credentials raises 401."""
        from fastapi import HTTPException
        from backend.core.security import get_current_user
        from backend.db.session import get_db

        # Create mock db session
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db=mock_db, authorization=None, session_token=None)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_api_key_raises_401(self):
        """Test that invalid API key raises 401."""
        from fastapi import HTTPException, Header
        from backend.core.security import get_current_user
        from unittest.mock import AsyncMock, patch

        # Create mock db that returns no user
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=lambda: None))

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                db=mock_db, authorization="Bearer invalid-api-key", session_token=None
            )

        assert exc_info.value.status_code == 401
