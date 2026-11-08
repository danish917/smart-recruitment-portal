import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify health check endpoint returns 200 and expected healthy status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "smart-recruitment-portal-backend"
    assert "version" in data
    assert "database" in data


def test_database_health():
    """Verify dedicated database health endpoint."""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["engine"] == "Neon PostgreSQL"


def test_root_endpoint():
    """Verify root endpoint returns welcome message and endpoint pointers."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome to Smart Recruitment Portal API" in data["message"]
    assert data["health_url"] == "/health"
    assert data["docs_url"] == "/docs"
