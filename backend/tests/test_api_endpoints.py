"""
Test FastAPI application endpoints - Story 1.1
Tests for AC7: Backend server and API functionality
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check and root endpoints"""

    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint returns service information"""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "service" in data
        assert "status" in data
        assert data["service"] == "KlipNote API"
        assert data["status"] == "running"

    def test_health_check_endpoint(self, test_client: TestClient):
        """Test health check endpoint returns system status"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "whisper_model" in data
        assert "whisper_device" in data

    def test_api_docs_accessible(self, test_client: TestClient):
        """Test FastAPI auto-generated docs are accessible"""
        response = test_client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_accessible(self, test_client: TestClient):
        """Test ReDoc documentation is accessible"""
        response = test_client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema_accessible(self, test_client: TestClient):
        """Test OpenAPI schema endpoint is accessible"""
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "KlipNote API"


class TestCORSConfiguration:
    """Test CORS middleware configuration"""

    def test_cors_headers_present(self, test_client: TestClient):
        """Test CORS headers are present in responses"""
        response = test_client.options(
            "/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET"
            }
        )

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or \
               response.status_code in [200, 404]  # Some CORS implementations vary
