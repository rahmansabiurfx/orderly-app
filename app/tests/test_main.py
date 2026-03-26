"""
Tests for the Orderly App.

Run locally with: pytest app/tests/ -v
"""

from fastapi.testclient import TestClient
from app.main import app


# ──────────────────────────────────────────────
# Create a test client
# ──────────────────────────────────────────────

client = TestClient(app)


# ──────────────────────────────────────────────
# Test: Root Endpoint
# ──────────────────────────────────────────────

def test_root_returns_200():
    response = client.get("/")
    
    assert response.status_code == 200

def test_root_contains_app_info():
    response = client.get("/")
    data = response.json()
    
    assert "application" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "message" in data
    
    assert data["application"] == "orderly-app"
    assert data["message"] == "Welcome to the Orderly App!"


# ──────────────────────────────────────────────
# Test: Health Endpoint (Liveness Probe)
# ──────────────────────────────────────────────

def test_health_returns_200():
    """Test that the liveness probe returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_healthy_status():
    """Test that the liveness probe reports healthy status."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"


# ──────────────────────────────────────────────
# Test: Ready Endpoint (Readiness Probe)
# ──────────────────────────────────────────────

def test_ready_returns_200():
    """Test that the readiness probe returns HTTP 200."""
    response = client.get("/ready")
    assert response.status_code == 200


def test_ready_returns_ready_status():
    """Test that the readiness probe reports ready status."""
    response = client.get("/ready")
    data = response.json()
    assert data["status"] == "ready"


# ──────────────────────────────────────────────
# Test: Info Endpoint
# ──────────────────────────────────────────────

def test_info_returns_200():
    """Test that GET /info returns HTTP 200."""
    response = client.get("/info")
    assert response.status_code == 200


def test_info_contains_hostname():
    """Test that /info returns hostname and runtime info."""
    response = client.get("/info")
    data = response.json()

    assert "hostname" in data
    assert "platform" in data
    assert "python_version" in data
    assert "app_name" in data
    assert "app_version" in data
    assert "environment" in data


# ──────────────────────────────────────────────
# Test: Non-existent Route
# ──────────────────────────────────────────────

def test_nonexistent_route_returns_404():
    """
    Test that requesting a route that doesn't exist returns 404.
    This verifies FastAPI's default error handling works correctly.
    """
    response = client.get("/this-does-not-exist")
    
    assert response.status_code == 404