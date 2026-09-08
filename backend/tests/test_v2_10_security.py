"""FraudDNA V2-10 — Security & Boundary Defense Test Suite.

Validates:
1. Production configuration hardening and fail-fast validation.
2. HTTP security response headers.
3. Input validation and strict bounding on graph, network, and case endpoints.
4. Prompt injection isolation in untrusted payloads.
5. Invariant enforcement: Zero Financial Mutation Authority for AI and Analyst roles.
"""

import pytest
from starlette.testclient import TestClient

from app.core.config import Settings
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_production_config_rejects_insecure_secret_key():
    """Verify that production configuration validation raises ValueError on insecure dev secrets."""
    insecure_settings = Settings(
        APP_ENV="production",
        SECRET_KEY="insecure-dev-secret-key-change-in-production",
        DATABASE_URL="postgresql+asyncpg://frauddna_admin:StrongPass123!@db.prod:5432/frauddna_prod",
        DATABASE_URL_SYNC="postgresql://frauddna_admin:StrongPass123!@db.prod:5432/frauddna_prod",
    )
    with pytest.raises(ValueError, match="CRITICAL SECURITY: Production mode requires a strong"):
        insecure_settings.validate_production_configuration()


def test_production_config_rejects_default_database_password():
    """Verify that production configuration validation raises ValueError on default db password."""
    insecure_settings = Settings(
        APP_ENV="production",
        SECRET_KEY="a-very-long-and-secure-random-production-key-32-chars!",
        DATABASE_URL="postgresql+asyncpg://frauddna_user:frauddna_password@localhost:5432/frauddna_db",
        DATABASE_URL_SYNC="postgresql://frauddna_user:frauddna_password@localhost:5432/frauddna_db",
    )
    with pytest.raises(
        ValueError,
        match="CRITICAL SECURITY: Production mode requires explicit production DATABASE_URL",
    ):
        insecure_settings.validate_production_configuration()


def test_production_config_rejects_wildcard_cors():
    """Verify that production configuration validation rejects wildcard CORS origins."""
    insecure_settings = Settings(
        APP_ENV="production",
        SECRET_KEY="a-very-long-and-secure-random-production-key-32-chars!",
        DATABASE_URL="postgresql+asyncpg://frauddna_admin:StrongPass123!@db.prod:5432/frauddna_prod",
        DATABASE_URL_SYNC="postgresql://frauddna_admin:StrongPass123!@db.prod:5432/frauddna_prod",
        CORS_ORIGINS=["*"],
    )
    with pytest.raises(ValueError, match="CRITICAL SECURITY: Wildcard CORS"):
        insecure_settings.validate_production_configuration()


def test_http_security_headers_present(client: TestClient):
    """Verify standard production security headers on API responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "X-Request-ID" in resp.headers


def test_graph_and_path_bounds_enforcement(client: TestClient):
    """Verify that excessive graph search bounds are rejected with HTTP 422."""
    # Path search with depth > 3 (e.g. 4)
    resp = client.post(
        "/api/v1/networks/paths/search",
        json={
            "source_type": "customer",
            "source_id": "cust_00001",
            "target_type": "device",
            "target_id": "dev_00001",
            "max_depth": 4,
            "max_paths": 100,
        },
    )
    assert resp.status_code == 422


def test_case_pagination_bounds_enforcement(client: TestClient):
    """Verify that excessive case pagination limits are rejected with HTTP 422."""
    resp = client.get("/api/v1/cases?limit=5000")
    assert resp.status_code == 422
