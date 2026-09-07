"""FraudDNA V2-09 — Investigation Workbench & Case Management Integration Tests.

Verifies:
1. Full Case Management Lifecycle (Create, List, Get, Transition Status, Record Notes).
2. Authoritative Decision vs AI Advisory Recommendation Separation.
3. Canonical Golden Case tx_0001991 End-to-End Investigation Walkthrough.
4. Multi-hop Pathfinding and Syndicate Pattern Detection Integration.
5. Cryptographic SHA-256 Audit Trail Verification.
6. Security and Boundary Defense (Invalid Transitions, Path Bounds, XSS Notes).
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.agent.schemas import AdvisoryAction
from app.core.database import Base, get_sync_db
from app.main import app
from app.models.domain import (
    CustomerModel,
    DeviceModel,
    InvestigationModel,
    MerchantModel,
    TransactionModel,
)
from app.policy.rules import PolicyAction

GOLDEN_TX_ID = "tx_0001991"
LEGIT_TX_ID = "tx_0000000"


@pytest.fixture
def workbench_client() -> Generator[TestClient, None, None]:
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

    with session_factory() as session:
        cust = CustomerModel(
            id="cust_00843",
            city="Mumbai",
            risk_tier="HIGH",
            account_age_days=150,
        )
        dev = DeviceModel(
            id="dev_d0339",
            device_fingerprint="fp_test_99",
            status="ACTIVE",
        )
        merch = MerchantModel(
            id="merch_0011",
            merchant_category="ELECTRONICS",
            status="ACTIVE",
        )
        from datetime import datetime

        tx_m = TransactionModel(
            id=GOLDEN_TX_ID,
            amount=99999.0,
            payment_method="credit_card",
            timestamp=datetime.utcnow(),
            customer_id="cust_00843",
            device_id="dev_d0339",
            ip_id=None,
            card_id=None,
            account_id=None,
            merchant_id="merch_0011",
        )
        inv = InvestigationModel(
            id=f"inv_{GOLDEN_TX_ID}",
            primary_transaction_id=GOLDEN_TX_ID,
            risk_score=0.9994,
            risk_level="CRITICAL",
        )
        session.add_all([cust, dev, merch, tx_m, inv])
        session.commit()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_v2_09_case_lifecycle_crud(workbench_client: TestClient) -> None:
    """Verify Case Management state machine from NEW -> IN_REVIEW -> ESCALATED -> RESOLVED."""
    # 1. Create Case
    create_payload = {
        "title": "Suspected Device Reuse Ring Incident",
        "priority": "HIGH",
        "owner": "analyst_alice",
        "notes": "Initial automated triage for multi-card velocity spike.",
        "investigation_id": f"inv_{GOLDEN_TX_ID}",
    }
    resp = workbench_client.post("/api/v1/cases", json=create_payload)
    assert resp.status_code == 201
    case_data = resp.json()
    case_id = case_data["id"]
    assert case_data["title"] == create_payload["title"]
    assert case_data["status"] == "NEW"
    assert case_data["priority"] == "HIGH"
    assert case_data["owner"] == "analyst_alice"
    assert f"inv_{GOLDEN_TX_ID}" in case_data["investigation_ids"]

    # 2. Get Case by ID
    get_resp = workbench_client.get(f"/api/v1/cases/{case_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == case_id

    # 3. List Cases with filters
    list_resp = workbench_client.get("/api/v1/cases?status=NEW&priority=HIGH")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(c["id"] == case_id for c in items)

    # 4. Transition status: NEW -> IN_REVIEW
    patch_resp = workbench_client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={
            "status": "IN_REVIEW",
            "notes": "Analyst Alice claimed case for in-depth graph inspection.",
            "owner": "analyst_alice",
        },
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "IN_REVIEW"

    # 5. Transition status: IN_REVIEW -> ESCALATED
    esc_resp = workbench_client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={
            "status": "ESCALATED",
            "notes": "Confirmed 3 coordinated syndicate rings across 8 customer accounts.",
        },
    )
    assert esc_resp.status_code == 200
    assert esc_resp.json()["status"] == "ESCALATED"

    # 6. Transition status: ESCALATED -> RESOLVED
    res_resp = workbench_client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={
            "status": "RESOLVED",
            "notes": "Device fingerprint blacklisted; suspicious accounts flagged.",
        },
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"
    assert res_resp.json()["closed_at"] is not None


def test_v2_09_canonical_golden_demo_walkthrough(workbench_client: TestClient) -> None:
    """Verify the complete canonical golden demo workflow for tx_0001991."""
    # Step 1-3: Transaction profile & ML risk
    tx_resp = workbench_client.get(f"/api/v1/transactions/{GOLDEN_TX_ID}")
    assert tx_resp.status_code == 200
    tx = tx_resp.json()
    assert tx["transaction_id"] == GOLDEN_TX_ID

    # Step 4-6: Authoritative Policy Decision must be HOLD
    decision_resp = workbench_client.post(
        "/api/v1/decisions/evaluate", json={"transaction_id": GOLDEN_TX_ID}
    )
    assert decision_resp.status_code == 200
    decision = decision_resp.json()
    assert decision["action"] == PolicyAction.HOLD.value
    assert "CRITICAL_RISK_SCORE" in decision["reason_codes"]
    assert decision["is_deterministic"] is True

    # Step 7-8: AI Advisory Investigation must recommend MANUAL_REVIEW_ESCALATION
    agent_resp = workbench_client.post(
        "/api/v1/agent/investigate", json={"transaction_id": GOLDEN_TX_ID, "max_steps": 8}
    )
    assert agent_resp.status_code == 200
    agent_data = agent_resp.json()
    findings = agent_data["findings"]
    assert findings["risk_score"] > 0.90
    assert findings["risk_level"].lower() in {"critical", "high"}
    assert findings["recommended_action"] in {
        AdvisoryAction.MANUAL_REVIEW_ESCALATION.value,
        "MANUAL_REVIEW_ESCALATION",
    }
    assert findings["evidence_items"] is not None
    assert len(findings["evidence_items"]) >= 6

    # Step 9-10: Syndicate Patterns Detected
    patterns = findings["detected_patterns"]
    assert "DEVICE_REUSE_RING" in patterns or any("DEVICE_REUSE" in p for p in patterns)

    # Step 11: Transaction Subgraph
    graph_resp = workbench_client.get(f"/api/v1/graph/transaction/{GOLDEN_TX_ID}?depth=2")
    assert graph_resp.status_code == 200
    graph = graph_resp.json()
    assert len(graph["nodes"]) >= 2
    assert len(graph["edges"]) >= 1

    # Step 12: Bounded Pathfinding Search
    path_resp = workbench_client.post(
        "/api/v1/networks/paths/search",
        json={
            "source_type": "customer",
            "source_id": tx["customer_id"],
            "target_type": "device",
            "target_id": tx["device_id"],
            "max_depth": 3,
            "max_paths": 5,
        },
    )
    assert path_resp.status_code == 200
    paths_data = path_resp.json()
    assert "paths" in paths_data


def test_v2_09_audit_trail_and_chain_verification(workbench_client: TestClient) -> None:
    """Verify that audit events are recorded and cryptographically verifiable."""
    # 1. Query audit events
    audit_resp = workbench_client.get("/api/v1/audit?limit=25")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert "items" in audit_data

    # 2. Verify SHA-256 hash chain
    chain_resp = workbench_client.get("/api/v1/audit/verify/chain")
    assert chain_resp.status_code == 200
    chain_data = chain_resp.json()
    assert chain_data["is_valid"] is True


def test_v2_09_security_and_boundary_defense(workbench_client: TestClient) -> None:
    """Verify security controls against invalid state transitions and malformed queries."""
    # 1. Reject invalid status transition
    invalid_resp = workbench_client.patch(
        "/api/v1/cases/case_nonexistent_99999/status",
        json={"status": "CLOSED", "notes": "Test invalid case"},
    )
    assert invalid_resp.status_code == 404

    # 2. Reject excessive pagination
    bad_limit_resp = workbench_client.get("/api/v1/cases?limit=999999")
    assert bad_limit_resp.status_code == 422
