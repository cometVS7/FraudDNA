"""FraudDNA V2 Entity Intelligence & Advanced Graph Integration Test Suite.

Verifies:
1. Entity profiles across all supported types (Customer, Account, Device, IP, Card, Merchant).
2. Deterministic entity risk aggregation formula, tiering, and explainability.
3. Point-in-time behavioral velocity metrics and zero future-data leakage.
4. Direct semantic relationship retrieval and collusion edge discovery.
5. Database-backed bounded neighborhood graph retrieval (depth 1 & 2, caps, deterministic sorting).
6. Risk network intelligence: lookup, members, member transactions, and subgraph.
7. Security boundaries: injection prevention, traversal depth caps, type validation.
8. Known coordinated fraud transaction regression: tx_0001991 (score >= 0.90, CRITICAL, HOLD).
"""

from collections.abc import Generator
from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_sync_db
from app.core.errors import NotFoundDomainError, ValidationDomainError
from app.main import app
from app.models.domain import (
    CustomerModel,
    DeviceModel,
    IPAddressModel,
    RiskNetworkModel,
    TransactionModel,
)
from app.repositories.entity_repository import EntityRepository
from app.services.decision import DecisionService
from app.services.entity import EntityService, compute_deterministic_entity_risk
from app.services.migration import DataMigrationService
from app.services.network import NetworkService


@pytest.fixture(scope="module")
def migrated_engine():
    """Create in-memory SQLite engine and seed with empirical migrated records."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    migrator = DataMigrationService()
    # Migrate first 2,000 rows (contains the coordinated cluster and tx_0001991)
    migrator.migrate_sync(
        session=session,
        batch_size=500,
        compute_risk=True,
        compute_signals=True,
        limit=2000,
    )
    session.close()

    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(migrated_engine) -> Generator[Session, None, None]:
    """Provide a database session connected to the migrated engine."""
    session_factory = sessionmaker(bind=migrated_engine)
    session = session_factory()
    yield session
    session.close()


# ==============================================================================
# 1. ENTITY INTELLIGENCE PROFILES & RISK AGGREGATION
# ==============================================================================


def test_entity_customer_profile(db_session: Session):
    """Verify customer profile synthesis with behavioral metrics and risk aggregation."""
    entity_service = EntityService()
    # Find any customer with transactions
    cust = db_session.execute(select(CustomerModel).limit(1)).scalar_one()

    profile = entity_service.get_customer_profile(db_session, cust.id)
    assert profile.id == cust.id
    assert profile.total_transactions >= 1
    assert profile.total_amount > 0.0
    assert profile.risk_aggregation is not None
    assert 0.0 <= profile.risk_aggregation.risk_score <= 1.0
    assert profile.risk_aggregation.risk_tier in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert profile.behavioral_metrics is not None
    assert profile.behavioral_metrics.tx_count_24h >= 0
    assert len(profile.recent_transactions) <= 5
    assert "accounts_count" in profile.connected_entities_summary


def test_entity_device_and_ip_profiles(db_session: Session):
    """Verify device and IP address profiles with sharing count intelligence."""
    entity_service = EntityService()
    dev = db_session.execute(select(DeviceModel).limit(1)).scalar_one()
    ip = db_session.execute(select(IPAddressModel).limit(1)).scalar_one()

    dev_prof = entity_service.get_device_profile(db_session, dev.id)
    assert dev_prof.id == dev.id
    assert dev_prof.risk_aggregation is not None
    assert dev_prof.connected_customers_count >= 1

    ip_prof = entity_service.get_ip_profile(db_session, ip.id)
    assert ip_prof.id == ip.id
    assert ip_prof.risk_aggregation is not None
    assert ip_prof.connected_customers_count >= 1


def test_entity_not_found(db_session: Session):
    """Verify NotFoundDomainError is raised for non-existent entities."""
    entity_service = EntityService()
    with pytest.raises(NotFoundDomainError) as exc_info:
        entity_service.get_customer_profile(db_session, "non_existent_customer_999999")
    assert "non_existent_customer_999999" in str(exc_info.value)


def test_deterministic_entity_risk_formula():
    """Verify deterministic risk formula computation, tiering, and explainability."""
    # Test high-risk / critical input
    agg = compute_deterministic_entity_risk(
        max_tx_risk=0.98,
        avg_top3_tx_risk=0.92,
        network_exposure=1.0,
        sharing_anomaly=0.6,
        entity_name="Test Entity",
    )
    # 0.40*0.98 + 0.20*0.92 + 0.25*1.0 + 0.15*0.6 = 0.392 + 0.184 + 0.25 + 0.09 = 0.916
    assert agg.risk_score == 0.9160
    assert agg.risk_tier == "CRITICAL"
    assert "CRITICAL" in agg.explanation
    assert "max tx risk (0.98)" in agg.explanation
    assert "network exposure (1.00)" in agg.explanation

    # Test low-risk input
    agg_low = compute_deterministic_entity_risk(
        max_tx_risk=0.10,
        avg_top3_tx_risk=0.08,
        network_exposure=0.0,
        sharing_anomaly=0.0,
        entity_name="Test Legit",
    )
    # 0.40*0.10 + 0.20*0.08 + 0.0 + 0.0 = 0.056
    assert agg_low.risk_score == 0.0560
    assert agg_low.risk_tier == "LOW"


def test_point_in_time_behavioral_no_future_leakage(db_session: Session):
    """Verify point-in-time behavioral velocity evaluation prevents future-data leakage."""
    entity_service = EntityService()
    # Pick a customer with transactions
    tx_stmt = select(TransactionModel).order_by(TransactionModel.timestamp.asc()).limit(1)
    first_tx = db_session.execute(tx_stmt).scalar_one()

    # Query with as_of set to first_tx timestamp
    as_of_time = first_tx.timestamp
    metrics_at_first = entity_service.repo.get_behavioral_metrics(
        session=db_session,
        entity_type="customer",
        entity_id=first_tx.customer_id,
        as_of=as_of_time,
    )

    # Metrics evaluated at first_tx timestamp must only observe transactions <= first_tx.timestamp
    assert metrics_at_first["as_of"] == as_of_time
    assert metrics_at_first["tx_count_24h"] >= 1

    # Query with as_of set to 1 hour before first_tx -> should be 0 transactions
    past_time = as_of_time - timedelta(hours=2)
    metrics_in_past = entity_service.repo.get_behavioral_metrics(
        session=db_session,
        entity_type="customer",
        entity_id=first_tx.customer_id,
        as_of=past_time,
    )
    assert metrics_in_past["tx_count_24h"] == 0
    assert metrics_in_past["amount_24h"] == 0.0


# ==============================================================================
# 2. BOUNDED RELATIONSHIPS & GRAPH TRAVERSAL
# ==============================================================================


def test_direct_relationships_retrieval(db_session: Session):
    """Verify direct semantic relationship extraction."""
    entity_service = EntityService()
    cust = db_session.execute(select(CustomerModel).limit(1)).scalar_one()

    resp = entity_service.get_entity_relationships(db_session, "customer", cust.id)
    assert resp.entity_id == cust.id
    assert resp.total_relationships > 0

    rel_types = {r.relationship_type for r in resp.relationships}
    # Should at minimum contain OWNS (for accounts) or EXECUTED / ON_DEVICE / USING_CARD
    assert len(rel_types) >= 1
    for r in resp.relationships:
        assert r.source_id.startswith("customer:")
        assert ":" in r.target_id


def test_bounded_neighborhood_depth_1(db_session: Session):
    """Verify depth-1 ego-graph bounded neighborhood."""
    entity_service = EntityService()
    cust = db_session.execute(select(CustomerModel).limit(1)).scalar_one()

    graph = entity_service.get_entity_neighborhood_graph(
        session=db_session,
        entity_type="customer",
        entity_id=cust.id,
        depth=1,
        max_nodes=50,
        max_transactions=20,
    )
    assert graph.total_nodes > 0
    assert graph.total_nodes <= 50
    assert graph.total_edges >= 0

    node_ids = {n.id for n in graph.nodes}
    assert f"customer:{cust.id}" in node_ids

    # Nodes must be sorted deterministically: risk_score desc, id asc
    for i in range(len(graph.nodes) - 1):
        curr = graph.nodes[i]
        nxt = graph.nodes[i + 1]
        assert (curr.risk_score > nxt.risk_score) or (
            curr.risk_score == nxt.risk_score and curr.id <= nxt.id
        )


def test_bounded_neighborhood_depth_2_and_shared_collusion(db_session: Session):
    """Verify depth-2 graph expands to second-hop entities and collusive shared edges."""
    entity_service = EntityService()
    # Find a customer belonging to a suspicious cluster
    tx = db_session.execute(
        select(TransactionModel)
        .where(TransactionModel.network_id.is_not(None), TransactionModel.risk_score >= 0.70)
        .limit(1)
    ).scalar_one()

    graph = entity_service.get_entity_neighborhood_graph(
        session=db_session,
        entity_type="customer",
        entity_id=tx.customer_id,
        depth=2,
        max_nodes=100,
        max_transactions=50,
    )
    assert graph.total_nodes > 0
    assert graph.total_nodes <= 100

    # Verify edge relations include semantic types
    relations = {e.relation for e in graph.edges}
    assert len(relations) > 0


def test_invalid_depth_rejection(db_session: Session):
    """Verify server rejects depth > 2 or < 1 with ValidationDomainError."""
    entity_service = EntityService()
    cust = db_session.execute(select(CustomerModel).limit(1)).scalar_one()

    # Valid depths
    g1 = entity_service.get_entity_neighborhood_graph(
        session=db_session, entity_type="customer", entity_id=cust.id, depth=1
    )
    assert g1.total_nodes > 0
    g2 = entity_service.get_entity_neighborhood_graph(
        session=db_session, entity_type="customer", entity_id=cust.id, depth=2
    )
    assert g2.total_nodes > 0

    # Invalid depths: <= 0 or > 2
    for invalid_depth in [-1, 0, 3, 100]:
        with pytest.raises(ValidationDomainError):
            entity_service.get_entity_neighborhood_graph(
                session=db_session,
                entity_type="customer",
                entity_id=cust.id,
                depth=invalid_depth,
            )


def test_node_and_transaction_caps_validation(db_session: Session):
    """Verify server strictly enforces node and transaction caps in [5, 250]."""
    entity_service = EntityService()
    net_service = NetworkService()
    cust = db_session.execute(select(CustomerModel).limit(1)).scalar_one()
    net = db_session.execute(select(RiskNetworkModel).limit(1)).scalar_one()

    # Valid bounds: 5, 50, 250
    for valid_cap in [5, 50, 250]:
        g = entity_service.get_entity_neighborhood_graph(
            session=db_session,
            entity_type="customer",
            entity_id=cust.id,
            max_nodes=valid_cap,
            max_transactions=valid_cap,
        )
        assert g.total_nodes <= valid_cap

        ng = net_service.get_network_graph(
            session=db_session,
            network_id=net.id,
            max_nodes=valid_cap,
            max_transactions=valid_cap,
        )
        assert ng.total_nodes <= valid_cap

    # Invalid node caps: < 5 or > 250
    for invalid_node_cap in [4, 251, 1000]:
        with pytest.raises(ValidationDomainError):
            entity_service.get_entity_neighborhood_graph(
                session=db_session,
                entity_type="customer",
                entity_id=cust.id,
                max_nodes=invalid_node_cap,
            )
        with pytest.raises(ValidationDomainError):
            net_service.get_network_graph(
                session=db_session,
                network_id=net.id,
                max_nodes=invalid_node_cap,
            )

    # Invalid transaction caps: < 5 or > 250
    for invalid_tx_cap in [4, 251, 1000]:
        with pytest.raises(ValidationDomainError):
            entity_service.get_entity_neighborhood_graph(
                session=db_session,
                entity_type="customer",
                entity_id=cust.id,
                max_transactions=invalid_tx_cap,
            )
        with pytest.raises(ValidationDomainError):
            net_service.get_network_graph(
                session=db_session,
                network_id=net.id,
                max_transactions=invalid_tx_cap,
            )


# ==============================================================================
# 3. NETWORK INTELLIGENCE & SUBGRAPHS
# ==============================================================================


def test_risk_network_service(db_session: Session):
    """Verify network lookup, member entities, transactions, and bounded subgraph."""
    net_service = NetworkService()
    # Find a network in database
    net = db_session.execute(select(RiskNetworkModel).limit(1)).scalar_one()

    # 1. Lookup
    retrieved = net_service.get_network(db_session, net.id)
    assert retrieved.id == net.id

    # 2. Member entities
    members = net_service.get_network_members(db_session, net.id)
    assert members.network_id == net.id
    assert members.total_members > 0
    assert len(members.customer_ids) > 0

    # 3. Member transactions
    tx_resp = net_service.get_network_transactions(db_session, net.id, limit=10)
    assert tx_resp.network_id == net.id
    assert tx_resp.total_transactions > 0
    assert len(tx_resp.transactions) <= 10

    # 4. Network graph
    graph_resp = net_service.get_network_graph(db_session, net.id, max_nodes=50)
    assert graph_resp.total_nodes > 0
    assert graph_resp.total_nodes <= 50
    assert any(n.entity_type == "network" for n in graph_resp.nodes)

    # 5. ClusterDetail synthesis
    detail = net_service.get_network_detail(db_session, net.id)
    assert detail.cluster_id == net.id
    assert len(detail.member_transaction_ids) > 0
    assert len(detail.explanation) > 0


# ==============================================================================
# 4. API ENDPOINTS & SECURITY BOUNDARIES
# ==============================================================================


def test_api_entity_and_network_endpoints(migrated_engine):
    """Verify HTTP API endpoints for entities and networks."""
    session_factory = sessionmaker(bind=migrated_engine)

    def override_get_sync_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_sync_db] = override_get_sync_db

    try:
        with patch.object(settings, "ENABLE_PERSISTENT_STORAGE", True):
            client = TestClient(app)

            # 1. Customer profile
            session = session_factory()
            cust_id = session.execute(select(CustomerModel.id).limit(1)).scalar_one()
            session.close()

            resp = client.get(f"/api/v1/entities/customer/{cust_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == cust_id
            assert "risk_aggregation" in data
            assert "behavioral_metrics" in data

            # 2. Entity transactions
            resp_txs = client.get(f"/api/v1/entities/customer/{cust_id}/transactions?limit=5")
            assert resp_txs.status_code == 200
            assert len(resp_txs.json()["transactions"]) <= 5

            # 3. Entity relationships
            resp_rels = client.get(f"/api/v1/entities/customer/{cust_id}/relationships")
            assert resp_rels.status_code == 200
            assert resp_rels.json()["total_relationships"] > 0

            # 4. Entity graph
            resp_graph = client.get(
                f"/api/v1/entities/customer/{cust_id}/graph?depth=2&max_nodes=30"
            )
            assert resp_graph.status_code == 200
            assert resp_graph.json()["total_nodes"] <= 30

            # 5. Networks API
            session = session_factory()
            net_id = session.execute(select(RiskNetworkModel.id).limit(1)).scalar_one()
            session.close()

            resp_net = client.get(f"/api/v1/networks/{net_id}")
            assert resp_net.status_code == 200
            assert resp_net.json()["cluster_id"] == net_id

            resp_members = client.get(f"/api/v1/networks/{net_id}/members")
            assert resp_members.status_code == 200
            assert resp_members.json()["total_members"] > 0

            resp_net_graph = client.get(f"/api/v1/networks/{net_id}/graph")
            assert resp_net_graph.status_code == 200
            assert resp_net_graph.json()["total_nodes"] > 0
    finally:
        app.dependency_overrides.pop(get_sync_db, None)


def test_api_security_boundaries(migrated_engine):
    """Verify security controls against SQL injection, depth abuse, and malformed inputs."""
    session_factory = sessionmaker(bind=migrated_engine)

    def override_get_sync_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_sync_db] = override_get_sync_db

    try:
        client = TestClient(app)

        # 1. SQL Injection attempt in entity_id
        sqli_id = "'; DROP TABLE customers; --"
        resp_sqli = client.get(f"/api/v1/entities/customer/{sqli_id}")
        assert resp_sqli.status_code == 404

        # 2. Depth abuse (depth=5 exceeds max 2)
        resp_depth = client.get("/api/v1/entities/customer/cust_0000001/graph?depth=5")
        assert resp_depth.status_code == 422

        # 3. Invalid entity category
        resp_type = client.get("/api/v1/entities/unsupported_type/123")
        assert resp_type.status_code == 422
    finally:
        app.dependency_overrides.pop(get_sync_db, None)


# ==============================================================================
# 5. KNOWN FRAUD TRANSACTION REGRESSION (tx_0001991)
# ==============================================================================


def test_tx_0001991_known_fraud_regression(db_session: Session):
    """Verify tx_0001991 preserves all empirical coordinated fraud attributes and lineage."""
    # 1. Transaction persistence & risk score
    tx = db_session.execute(
        select(TransactionModel).where(TransactionModel.id == "tx_0001991")
    ).scalar_one()

    assert tx.risk_score >= 0.90
    assert tx.risk_tier == "CRITICAL"
    assert tx.network_id is not None
    assert tx.network_id.startswith("cluster_")

    # 2. Risk Network persistence & suspicious flag
    net = db_session.execute(
        select(RiskNetworkModel).where(RiskNetworkModel.id == tx.network_id)
    ).scalar_one()
    assert net.is_suspicious is True
    assert net.risk_score >= 0.85
    assert net.customer_count > 1
    assert net.device_count > 0

    # 3. Bounded graph neighborhood from PostgreSQL
    entity_repo = EntityRepository()
    graph = entity_repo.get_bounded_neighborhood(
        session=db_session,
        entity_type="transaction",
        entity_id="tx_0001991",
        depth=2,
        max_nodes=100,
        max_transactions=50,
    )
    assert graph.total_nodes >= 5
    node_types = {n.entity_type for n in graph.nodes}
    assert "transaction" in node_types
    assert "customer" in node_types
    assert "device" in node_types
    assert "ip" in node_types

    # 4. Deterministic decision engine evaluates HOLD
    decision_service = DecisionService()
    decision = decision_service.evaluate_and_persist(
        session=db_session,
        transaction_id="tx_0001991",
        actor="regression_tester_v2",
    )
    assert decision.action.value == "HOLD"
    assert "CRITICAL_RISK_SCORE" in decision.reason_codes
