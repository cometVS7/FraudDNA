"""FraudDNA V2 API Endpoints Integration Tests.

Validates HTTP REST contracts for:
1. /api/v1/cases (CRUD, lifecycle transitions, validation errors)
2. /api/v1/audit (event listing, single event lookup, cryptographic chain verification)
3. /api/v1/entities (profile lookups, not found handling)
"""

from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_sync_db
from app.main import app
from app.models.domain import CustomerModel, DeviceModel


@pytest.fixture
def api_test_db():
    """Create isolated SQLite database for API testing and inject dependency override."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    def override_get_sync_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_sync_db] = override_get_sync_db

    # Seed an entity for entity tests
    with session_factory() as session:
        cust = CustomerModel(
            id="cust_api_1",
            city="Hyderabad",
            risk_tier="LOW",
            account_age_days=150,
        )
        dev = DeviceModel(
            id="dev_api_1",
            device_fingerprint="fp_api_1",
            status="ACTIVE",
        )
        session.add_all([cust, dev])
        session.commit()

    yield session_factory

    app.dependency_overrides.pop(get_sync_db, None)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.mark.asyncio
@pytest.mark.usefixtures("api_test_db")
async def test_cases_api_lifecycle() -> None:
    """Test POST /cases, GET /cases, and PATCH /cases/{id}/status endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a case
        create_payload = {
            "title": "Suspected mule account clustering",
            "priority": "HIGH",
            "owner": "analyst_arun",
            "notes": "Coordinated withdrawals within 5 minutes",
        }
        res = await client.post("/api/v1/cases", json=create_payload)
        assert res.status_code == 201
        case_data = res.json()
        case_id = case_data["id"]
        assert case_data["status"] == "NEW"
        assert case_data["priority"] == "HIGH"
        assert case_data["owner"] == "analyst_arun"

        # 2. Get case by ID
        res = await client.get(f"/api/v1/cases/{case_id}")
        assert res.status_code == 200
        assert res.json()["id"] == case_id

        # 3. List cases
        res = await client.get("/api/v1/cases?status=NEW")
        assert res.status_code == 200
        list_data = res.json()
        assert list_data["total_count"] >= 1
        assert any(c["id"] == case_id for c in list_data["items"])

        # 4. Valid status update: NEW -> IN_REVIEW
        update_payload = {
            "status": "IN_REVIEW",
            "notes": "Graph neighborhood under review",
        }
        res = await client.patch(f"/api/v1/cases/{case_id}/status", json=update_payload)
        assert res.status_code == 200
        assert res.json()["status"] == "IN_REVIEW"

        # 5. Invalid status transition: IN_REVIEW -> NEW (rejected by state machine)
        invalid_payload = {"status": "NEW"}
        res = await client.patch(f"/api/v1/cases/{case_id}/status", json=invalid_payload)
        assert res.status_code == 422
        assert "Invalid case status transition" in res.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("api_test_db")
async def test_audit_api_and_chain_verification() -> None:
    """Test GET /api/v1/audit, GET /api/v1/audit/{id}, and GET /api/v1/audit/verify/chain."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a case first to generate an audit entry
        await client.post(
            "/api/v1/cases",
            json={"title": "Audit test case", "priority": "LOW"},
        )

        # 1. List audit events
        res = await client.get("/api/v1/audit")
        assert res.status_code == 200
        audit_data = res.json()
        assert audit_data["total_count"] >= 1
        event = audit_data["items"][0]
        event_id = event["id"]

        # 2. Get specific event
        res = await client.get(f"/api/v1/audit/{event_id}")
        assert res.status_code == 200
        assert res.json()["id"] == event_id
        assert "payload_hash" in res.json()
        assert "event_hash" in res.json()

        # 3. Verify cryptographic chain
        res = await client.get("/api/v1/audit/verify/chain")
        assert res.status_code == 200
        verify_data = res.json()
        assert verify_data["is_valid"] is True
        assert verify_data["tampered_at_id"] is None


@pytest.mark.asyncio
@pytest.mark.usefixtures("api_test_db")
async def test_entities_api() -> None:
    """Test GET /api/v1/entities/{entity_type}/{entity_id}."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Existing customer
        res = await client.get("/api/v1/entities/customer/cust_api_1")
        assert res.status_code == 200
        cust = res.json()
        assert cust["id"] == "cust_api_1"
        assert cust["city"] == "Hyderabad"

        # 2. Existing device
        res = await client.get("/api/v1/entities/device/dev_api_1")
        assert res.status_code == 200
        dev = res.json()
        assert dev["id"] == "dev_api_1"
        assert dev["device_fingerprint"] == "fp_api_1"

        # 3. Nonexistent entity -> 404
        res = await client.get("/api/v1/entities/customer/cust_nonexistent")
        assert res.status_code == 404
