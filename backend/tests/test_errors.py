"""Tests for backend/core/errors.py."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from unittest.mock import MagicMock, patch


def create_test_app():
    """Create a test FastAPI app with error handlers."""
    from backend.core.errors import register_error_handlers, RequestIDMiddleware

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    register_error_handlers(app)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


class TestRequestIDMiddleware:
    """Test request ID middleware."""

    def test_request_id_header_added(self):
        """Test that X-Request-ID header is added to responses."""
        app = create_test_app()
        client = TestClient(app)
        response = client.get("/test")

        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_request_id_is_uuid_format(self):
        """Test that request ID is a valid UUID."""
        import uuid

        app = create_test_app()
        client = TestClient(app)
        response = client.get("/test")

        request_id = response.headers["x-request-id"]
        uuid.UUID(request_id)


class TestUnhandledExceptionHandler:
    """Test unhandled exception handling."""

    def test_unhandled_exception_returns_500(self):
        """Test that unhandled exceptions return 500."""
        app = create_test_app()

        @app.get("/raise-error")
        async def raise_error():
            raise ValueError("Test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/raise-error")

        assert response.status_code == 500

    def test_unhandled_exception_response_format(self):
        """Test that unhandled exception has correct format."""
        app = create_test_app()

        @app.get("/raise-error")
        async def raise_error():
            raise ValueError("Test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/raise-error")

        data = response.json()
        assert "error" in data
        assert "detail" in data
        assert data["error"] == "internal_server_error"
        assert data["detail"] == "Unexpected error occurred."

    def test_unhandled_exception_includes_request_id(self):
        """Test that unhandled exception includes request ID."""
        app = create_test_app()

        @app.get("/raise-error")
        async def raise_error():
            raise ValueError("Test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/raise-error")

        data = response.json()
        assert "request_id" in data
        assert data["request_id"] is not None


class TestErrorHandlersRegistered:
    """Test that error handlers are properly registered."""

    def test_validation_handler_returns_422_for_missing_body(self):
        """Test that missing required body returns 422."""
        from pydantic import BaseModel

        app = create_test_app()

        class Item(BaseModel):
            name: str
            price: float

        @app.post("/items")
        async def create_item(item: Item):
            return item

        client = TestClient(app, raise_server_exceptions=False)

        # Send invalid body (empty)
        response = client.post("/items", json={})

        # Should get validation error
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"] == "validation_error"
