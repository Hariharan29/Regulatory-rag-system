"""
tests/test_health.py
─────────────────────
Phase 1 smoke test — verifies the /health endpoint returns 200 {"status": "ok"}.
Uses FastAPI's TestClient so no real server or database is needed.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    """GET /health should return HTTP 200 with status=ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_content_type_is_json() -> None:
    """Ensure the response content type is application/json."""
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
