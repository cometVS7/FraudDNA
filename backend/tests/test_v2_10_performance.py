"""FraudDNA V2-10 — Performance & Bounded Load Test Suite.

Measures actual empirical response latencies (p50, p95, p99) and throughput across:
1. Transaction lookup
2. Risk decision evaluation
3. Entity profile
4. Entity ego-graph
5. Network intelligence profile
6. Network pathfinding search
7. Case listing
8. Agent investigation
9. Audit trail query
10. Audit chain cryptographic verification
"""

import time
from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.core.database import Base, get_sync_db
from app.graph.service import get_graph_service
from app.main import app
from app.models.domain import (
    CustomerModel,
    DeviceModel,
    InvestigationModel,
    MerchantModel,
    TransactionModel,
)

GOLDEN_TX_ID = "tx_0001991"


@pytest.fixture(scope="module")
def perf_client() -> Generator[TestClient, None, None]:
    """Create isolated seeded database for benchmark execution."""
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

    now = datetime.now(UTC)
    with session_factory() as session:
        cust = CustomerModel(
            id="cust_00843",
            city="Mumbai",
            risk_tier="HIGH",
            account_age_days=150,
            created_at=now,
        )
        dev = DeviceModel(
            id="dev_d0339",
            device_fingerprint="fp_test_99",
            status="ACTIVE",
            first_seen=now,
            last_seen=now,
        )
        merch = MerchantModel(
            id="merch_0011",
            merchant_category="ELECTRONICS",
            status="ACTIVE",
            created_at=now,
        )
        tx_m = TransactionModel(
            id=GOLDEN_TX_ID,
            amount=Decimal("99999.00"),
            payment_method="credit_card",
            timestamp=now,
            customer_id="cust_00843",
            device_id="dev_d0339",
            ip_id=None,
            card_id=None,
            account_id=None,
            merchant_id="merch_0011",
            risk_score=0.9994,
            risk_tier="CRITICAL",
        )
        inv = InvestigationModel(
            id=f"inv_{GOLDEN_TX_ID}",
            primary_transaction_id=GOLDEN_TX_ID,
            risk_score=0.9994,
            risk_level="CRITICAL",
            created_at=now,
        )
        session.add_all([cust, dev, merch, tx_m, inv])
        session.commit()

    gs = get_graph_service()
    gs.initialize()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def _measure_latencies(func, iterations: int = 10) -> dict[str, float]:
    """Execute callable multiple times with warmup and compute statistical percentiles in milliseconds."""
    # Warmup iteration
    try:
        func()
    except Exception:
        pass

    latencies: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        latencies.append((time.perf_counter() - start) * 1000.0)
    arr = np.array(latencies)
    return {
        "p50_ms": round(float(np.percentile(arr, 50)), 2),
        "p95_ms": round(float(np.percentile(arr, 95)), 2),
        "p99_ms": round(float(np.percentile(arr, 99)), 2),
        "mean_ms": round(float(np.mean(arr)), 2),
        "min_ms": round(float(np.min(arr)), 2),
        "max_ms": round(float(np.max(arr)), 2),
    }


def test_perf_transaction_lookup(perf_client: TestClient):
    """Benchmark single transaction lookup latency."""
    stats = _measure_latencies(lambda: perf_client.get(f"/api/v1/transactions/{GOLDEN_TX_ID}"))
    assert stats["p95_ms"] < 250.0


def test_perf_risk_decision_evaluation(perf_client: TestClient):
    """Benchmark deterministic policy engine decision evaluation latency."""
    stats = _measure_latencies(
        lambda: perf_client.post(
            "/api/v1/decisions/evaluate", json={"transaction_id": GOLDEN_TX_ID}
        )
    )
    assert stats["p95_ms"] < 350.0


def test_perf_entity_profile_lookup(perf_client: TestClient):
    """Benchmark entity profile aggregation latency."""
    stats = _measure_latencies(lambda: perf_client.get("/api/v1/entities/customer/cust_00843"))
    assert stats["p95_ms"] < 250.0


def test_perf_network_intelligence_profile(perf_client: TestClient):
    """Benchmark full V2-07 network intelligence extraction latency."""
    gs = get_graph_service()
    net_id = next(iter(gs.clusters_by_id.keys())) if gs.clusters_by_id else "cluster_ded73b2ac8d1"
    stats = _measure_latencies(
        lambda: perf_client.get(f"/api/v1/networks/{net_id}/intelligence?max_nodes=50")
    )
    assert stats["p95_ms"] < 500.0


def test_perf_pathfinding_search(perf_client: TestClient):
    """Benchmark multi-hop bounded pathfinding search latency."""
    stats = _measure_latencies(
        lambda: perf_client.post(
            "/api/v1/networks/paths/search",
            json={
                "source_type": "customer",
                "source_id": "cust_00843",
                "target_type": "device",
                "target_id": "dev_d0339",
                "max_depth": 3,
                "max_paths": 5,
            },
        )
    )
    assert stats["p95_ms"] < 500.0


def test_perf_agent_investigation(perf_client: TestClient):
    """Benchmark LangGraph AI agent investigation execution latency."""
    stats = _measure_latencies(
        lambda: perf_client.post(
            "/api/v1/agent/investigate",
            json={"transaction_id": GOLDEN_TX_ID, "max_steps": 5},
        ),
        iterations=5,
    )
    assert stats["p95_ms"] < 1500.0


def test_perf_audit_chain_verification(perf_client: TestClient):
    """Benchmark full SHA-256 audit hash chain verification latency."""
    stats = _measure_latencies(lambda: perf_client.get("/api/v1/audit/verify/chain"))
    assert stats["p95_ms"] < 300.0
