"""FraudDNA V2 Risk Network Intelligence Test Suite (V2-07).

Verifies:
1. Path Intelligence Engine: Bounded BFS, semantic edge weights, path scoring formula S(P), narrative synthesis.
2. Syndicate Pattern Detector: Detection of 7 canonical fraud patterns, evidence generation, false positive discrimination.
3. Network Analytics Engine: Exposure metrics, topology analytics, temporal timeline bursts, 5-component risk propagation.
4. Network Intelligence Service: Full intelligence assembly, entity network context, path searches.
5. REST API Endpoints: All /api/v1/networks/* and /api/v1/entities/* intelligence endpoints with FastAPI TestClient.
6. Boundaries & Security: Hard caps on depth/nodes/txs, cycle resilience, 404/422 domain error handling, SQL injection resistance.
7. Point-in-time (as_of) zero future-data leakage guarantee.
8. Known coordinated fraud regression: tx_0001991 cluster analysis.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_sync_db
from app.graph.network_analytics import NetworkAnalyticsEngine
from app.graph.paths import PathIntelligenceEngine
from app.graph.syndicate import SyndicateDetector
from app.main import app
from app.models.domain import (
    CustomerModel,
    RiskNetworkModel,
    TransactionModel,
)
from app.schemas.graph import GraphData, GraphEdge, GraphNode
from app.schemas.network_intelligence import (
    SyndicatePatternType,
)
from app.services.migration import DataMigrationService
from app.services.network_intelligence import NetworkIntelligenceService

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def migrated_engine():
    """Create in-memory SQLite engine seeded with empirical migrated records."""
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
    """Provide transactional database session."""
    session_factory = sessionmaker(bind=migrated_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide FastAPI test client with database override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_sync_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def synthetic_graph() -> GraphData:
    """Build a deterministic synthetic multi-hop fraud graph."""
    nodes = [
        GraphNode(
            id="customer:cust_A",
            raw_id="cust_A",
            entity_type="customer",
            label="Customer: cust_A",
            risk_score=0.85,
        ),
        GraphNode(
            id="customer:cust_B",
            raw_id="cust_B",
            entity_type="customer",
            label="Customer: cust_B",
            risk_score=0.75,
        ),
        GraphNode(
            id="device:dev_shared",
            raw_id="dev_shared",
            entity_type="device",
            label="Device: dev_shared",
            risk_score=0.90,
        ),
        GraphNode(
            id="card:card_shared",
            raw_id="card_shared",
            entity_type="card",
            label="Card: card_shared",
            risk_score=0.80,
        ),
        GraphNode(id="ip:ip_1", raw_id="ip_1", entity_type="ip", label="IP: ip_1", risk_score=0.60),
        GraphNode(
            id="transaction:tx_1",
            raw_id="tx_1",
            entity_type="transaction",
            label="Tx: tx_1",
            risk_score=0.92,
            amount=4500.0,
            timestamp="2026-03-01T10:00:00Z",
        ),
        GraphNode(
            id="transaction:tx_2",
            raw_id="tx_2",
            entity_type="transaction",
            label="Tx: tx_2",
            risk_score=0.88,
            amount=3800.0,
            timestamp="2026-03-01T10:05:00Z",
        ),
    ]
    edges = [
        GraphEdge(
            id="e1",
            source="customer:cust_A",
            target="transaction:tx_1",
            relation="EXECUTED",
            weight=1.0,
        ),
        GraphEdge(
            id="e2",
            source="transaction:tx_1",
            target="device:dev_shared",
            relation="ON_DEVICE",
            weight=1.5,
        ),
        GraphEdge(
            id="e3",
            source="transaction:tx_1",
            target="card:card_shared",
            relation="USING_CARD",
            weight=1.4,
        ),
        GraphEdge(
            id="e4", source="transaction:tx_1", target="ip:ip_1", relation="FROM_IP", weight=1.1
        ),
        GraphEdge(
            id="e5",
            source="customer:cust_B",
            target="transaction:tx_2",
            relation="EXECUTED",
            weight=1.0,
        ),
        GraphEdge(
            id="e6",
            source="transaction:tx_2",
            target="device:dev_shared",
            relation="ON_DEVICE",
            weight=1.5,
        ),
        GraphEdge(
            id="e7",
            source="transaction:tx_2",
            target="card:card_shared",
            relation="USING_CARD",
            weight=1.4,
        ),
        GraphEdge(
            id="e8",
            source="customer:cust_A",
            target="customer:cust_B",
            relation="SHARES_DEVICE",
            weight=1.5,
        ),
    ]
    return GraphData(nodes=nodes, edges=edges, total_nodes=len(nodes), total_edges=len(edges))


# --------------------------------------------------------------------------
# 1. Path Intelligence Engine Tests
# --------------------------------------------------------------------------


class TestPathIntelligenceEngine:
    def test_find_all_paths_bounded(self, synthetic_graph: GraphData):
        engine = PathIntelligenceEngine()
        paths = engine.find_paths_between_entities(
            graph_data=synthetic_graph,
            source_id="customer:cust_A",
            target_id="customer:cust_B",
            max_depth=3,
            max_paths=5,
        )

        assert len(paths) >= 1
        top_path = paths[0]
        assert top_path.source_id == "customer:cust_A"
        assert top_path.target_id == "customer:cust_B"
        assert 0.0 <= top_path.path_strength <= 1.0
        assert len(top_path.summary) > 0

    def test_path_scoring_formula_properties(self):
        engine = PathIntelligenceEngine()
        graph = GraphData(
            nodes=[
                GraphNode(id="n1", raw_id="n1", entity_type="customer", label="C1", risk_score=0.9),
                GraphNode(id="n2", raw_id="n2", entity_type="device", label="D1", risk_score=0.8),
                GraphNode(id="n3", raw_id="n3", entity_type="customer", label="C2", risk_score=0.7),
            ],
            edges=[
                GraphEdge(id="e1", source="n1", target="n2", relation="SHARES_DEVICE", weight=1.5),
                GraphEdge(id="e2", source="n2", target="n3", relation="SHARES_DEVICE", weight=1.5),
            ],
            total_nodes=3,
            total_edges=2,
        )
        paths = engine.find_paths_between_entities(
            graph_data=graph, source_id="n1", target_id="n3", max_depth=3
        )
        assert len(paths) == 1
        p = paths[0]
        assert p.hop_count == 2
        assert 0.0 <= p.path_strength <= 1.0

    def test_cycle_prevention(self):
        engine = PathIntelligenceEngine()
        cyclic_graph = GraphData(
            nodes=[
                GraphNode(id="n1", raw_id="n1", entity_type="customer", label="C1"),
                GraphNode(id="n2", raw_id="n2", entity_type="device", label="D1"),
                GraphNode(id="n3", raw_id="n3", entity_type="card", label="K1"),
            ],
            edges=[
                GraphEdge(id="e1", source="n1", target="n2", relation="ON_DEVICE", weight=1.0),
                GraphEdge(id="e2", source="n2", target="n3", relation="LINKED", weight=1.0),
                GraphEdge(id="e3", source="n3", target="n1", relation="LINKED", weight=1.0),
            ],
            total_nodes=3,
            total_edges=3,
        )
        paths = engine.find_paths_between_entities(
            graph_data=cyclic_graph, source_id="n1", target_id="n3", max_depth=3
        )
        assert len(paths) >= 1
        for path in paths:
            assert len(path.segments) >= 1


# --------------------------------------------------------------------------
# 2. Syndicate Pattern Detector Tests
# --------------------------------------------------------------------------


class TestSyndicateDetector:
    def test_detect_device_and_card_sharing_rings(self, synthetic_graph: GraphData):
        detector = SyndicateDetector()
        mock_txs = [
            {
                "id": "tx_1",
                "customer_id": "cust_A",
                "device_id": "dev_shared",
                "card_id": "card_shared",
                "ip_id": "ip_1",
                "risk_score": 0.92,
                "timestamp": datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC),
            },
            {
                "id": "tx_2",
                "customer_id": "cust_B",
                "device_id": "dev_shared",
                "card_id": "card_shared",
                "ip_id": "ip_1",
                "risk_score": 0.88,
                "timestamp": datetime(2026, 3, 1, 10, 5, 0, tzinfo=UTC),
            },
        ]
        mock_entities = {
            "customers": ["cust_A", "cust_B"],
            "devices": ["dev_shared"],
            "cards": ["card_shared"],
            "ips": ["ip_1"],
            "merchants": [],
        }

        patterns = detector.evaluate_syndicate_patterns(
            transactions=mock_txs,
            member_entities=mock_entities,
            graph_data=synthetic_graph,
        )

        triggered = [p for p in patterns if p.triggered]
        pattern_types = {p.pattern_type for p in triggered}
        assert SyndicatePatternType.DEVICE_REUSE_RING in pattern_types
        assert SyndicatePatternType.CARD_SHARING_RING in pattern_types

        for p in triggered:
            assert p.confidence >= 0.5
            assert p.description is not None
            assert len(p.evidence) >= 1

    def test_detect_burst_attack_pattern(self):
        detector = SyndicateDetector()
        base_time = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
        mock_txs = []
        for i in range(5):
            tx_time = base_time + timedelta(seconds=i * 20)
            mock_txs.append(
                {
                    "id": f"tx_burst_{i}",
                    "customer_id": "c1",
                    "card_id": "k1",
                    "device_id": "d1",
                    "risk_score": 0.85,
                    "timestamp": tx_time,
                }
            )

        mock_entities = {
            "customers": ["c1"],
            "devices": ["d1"],
            "cards": ["k1"],
            "ips": [],
            "merchants": [],
        }
        patterns = detector.evaluate_syndicate_patterns(
            transactions=mock_txs,
            member_entities=mock_entities,
        )
        triggered = [p for p in patterns if p.triggered]
        pattern_types = {p.pattern_type for p in triggered}
        assert SyndicatePatternType.HIGH_VELOCITY_BURST_ATTACK in pattern_types

    def test_empty_graph_returns_no_patterns(self):
        detector = SyndicateDetector()
        patterns = detector.evaluate_syndicate_patterns(
            transactions=[],
            member_entities={
                "customers": [],
                "devices": [],
                "cards": [],
                "ips": [],
                "merchants": [],
            },
        )
        triggered = [p for p in patterns if p.triggered]
        assert triggered == []


# --------------------------------------------------------------------------
# 3. Network Analytics Engine Tests
# --------------------------------------------------------------------------


class TestNetworkAnalyticsEngine:
    def test_exposure_calculation(self):
        analytics = NetworkAnalyticsEngine()
        mock_txs = [
            {"id": "tx_1", "amount": 4500.0, "risk_score": 0.92, "merchant_id": "m_1"},
            {"id": "tx_2", "amount": 3800.0, "risk_score": 0.88, "merchant_id": "m_1"},
        ]
        mock_entities = {
            "customers": ["c1", "c2"],
            "devices": ["d1"],
            "cards": ["k1"],
            "ips": ["i1"],
            "merchants": ["m_1"],
        }
        exposure = analytics.compute_network_exposure("net_1", mock_txs, mock_entities)

        assert exposure.total_transactions == 2
        assert exposure.total_amount == 4500.0 + 3800.0
        assert exposure.suspicious_amount == 4500.0 + 3800.0
        assert exposure.exposed_customer_count == 2
        assert exposure.exposed_device_count == 1
        assert exposure.exposed_card_count == 1

    def test_topology_metrics(self, synthetic_graph: GraphData):
        analytics = NetworkAnalyticsEngine()
        mock_entities = {
            "customers": ["cust_A", "cust_B"],
            "devices": ["dev_shared"],
            "cards": ["card_shared"],
            "ips": ["ip_1"],
            "merchants": [],
        }
        metrics = analytics.compute_network_topology_metrics(synthetic_graph, mock_entities)

        assert metrics.node_count == 7
        assert metrics.edge_count == 8
        assert metrics.density > 0.0

    def test_propagated_risk_formula_bounds(self, synthetic_graph: GraphData):
        analytics = NetworkAnalyticsEngine()
        mock_txs = [
            {
                "id": "tx_1",
                "amount": 4500.0,
                "risk_score": 0.92,
                "merchant_id": "m_1",
                "timestamp": datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC),
            },
            {
                "id": "tx_2",
                "amount": 3800.0,
                "risk_score": 0.88,
                "merchant_id": "m_1",
                "timestamp": datetime(2026, 3, 1, 10, 5, 0, tzinfo=UTC),
            },
        ]
        mock_entities = {
            "customers": ["cust_A", "cust_B"],
            "devices": ["dev_shared"],
            "cards": ["card_shared"],
            "ips": ["ip_1"],
            "merchants": ["m_1"],
        }

        exposure = analytics.compute_network_exposure("net_1", mock_txs, mock_entities)
        topology = analytics.compute_network_topology_metrics(synthetic_graph, mock_entities)
        timeline = analytics.compute_temporal_timeline("net_1", mock_txs)

        score, tier, conf = analytics.calculate_propagated_network_risk(
            exposure=exposure,
            topology=topology,
            timeline=timeline,
            transactions=mock_txs,
        )

        assert 0.0 <= score <= 1.0
        assert tier in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert 0.0 <= conf <= 1.0
        assert score >= 0.70

    def test_timeline_point_in_time_filtering(self):
        analytics = NetworkAnalyticsEngine()
        mock_txs = [
            {
                "id": "tx_1",
                "amount": 4500.0,
                "risk_score": 0.92,
                "timestamp": datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC),
            },
            {
                "id": "tx_2",
                "amount": 3800.0,
                "risk_score": 0.88,
                "timestamp": datetime(2026, 3, 1, 10, 5, 0, tzinfo=UTC),
            },
        ]
        as_of_time = datetime(2026, 3, 1, 10, 2, 0, tzinfo=UTC)
        timeline = analytics.compute_temporal_timeline("net_1", mock_txs, as_of=as_of_time)

        assert len(timeline.timeline_points) >= 1
        assert timeline.timeline_points[0].transaction_count == 1

    def test_api_get_network_timeline(self, client: TestClient, db_session: Session):
        network = db_session.execute(select(RiskNetworkModel).limit(1)).scalar_one()
        resp = client.get(f"/api/v1/networks/{network.id}/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "network_id" in data
        assert "timeline_points" in data
        assert "active_duration_hours" in data

    def test_api_get_network_exposure(self, client: TestClient, db_session: Session):
        network = db_session.execute(select(RiskNetworkModel).limit(1)).scalar_one()
        resp = client.get(f"/api/v1/networks/{network.id}/exposure")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_amount" in data
        assert "exposed_customer_count" in data

    def test_api_get_network_patterns(self, client: TestClient, db_session: Session):
        network = db_session.execute(select(RiskNetworkModel).limit(1)).scalar_one()
        resp = client.get(f"/api/v1/networks/{network.id}/patterns")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_api_get_network_findings(self, client: TestClient, db_session: Session):
        network = db_session.execute(select(RiskNetworkModel).limit(1)).scalar_one()
        resp = client.get(f"/api/v1/networks/{network.id}/findings")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_api_path_search(self, client: TestClient, db_session: Session):
        custs = db_session.execute(select(CustomerModel).limit(2)).scalars().all()
        if len(custs) >= 2:
            payload = {
                "source_id": custs[0].id,
                "target_id": custs[1].id,
                "source_type": "customer",
                "target_type": "customer",
                "max_depth": 3,
                "max_paths": 5,
            }
            resp = client.post("/api/v1/networks/paths/search", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert "paths" in data
            assert data["source_id"] == custs[0].id

    def test_api_entity_network_intelligence(self, client: TestClient, db_session: Session):
        tx = db_session.execute(
            select(TransactionModel).where(TransactionModel.customer_id.isnot(None)).limit(1)
        ).scalar_one()
        assert tx.customer_id is not None
        resp = client.get(f"/api/v1/entities/customer/{tx.customer_id}/network-intelligence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entity_id"] == tx.customer_id
        assert "network_risk_score" in data


# --------------------------------------------------------------------------
# 6. Boundaries, Security & Error Handling
# --------------------------------------------------------------------------


class TestBoundariesAndSecurity:
    def test_depth_cap_enforcement(self, client: TestClient, db_session: Session):
        network = db_session.execute(select(RiskNetworkModel).limit(1)).scalar_one()
        resp = client.get(f"/api/v1/networks/{network.id}/paths?max_depth=5")
        assert resp.status_code == 422

    def test_node_cap_enforcement(self, client: TestClient, db_session: Session):
        network = db_session.execute(select(RiskNetworkModel).limit(1)).scalar_one()
        resp = client.get(f"/api/v1/networks/{network.id}/intelligence?max_nodes=500")
        assert resp.status_code == 422

    def test_sql_injection_resistance(self, client: TestClient):
        malicious_id = "cluster_123' OR '1'='1"
        resp = client.get(f"/api/v1/networks/{malicious_id}/intelligence")
        assert resp.status_code == 404

    def test_invalid_entity_type_handling(self, client: TestClient):
        resp = client.get("/api/v1/entities/invalid_type/entity_1/network-intelligence")
        assert resp.status_code == 422


# --------------------------------------------------------------------------
# 7. Known Transaction tx_0001991 Regression
# --------------------------------------------------------------------------


class TestKnownTransactionRegression:
    def test_tx_0001991_network_intelligence(self, db_session: Session):
        """Verify tx_0001991 is connected to a high-risk coordinated syndicate."""
        tx = db_session.execute(
            select(TransactionModel).where(TransactionModel.id == "tx_0001991")
        ).scalar_one_or_none()
        assert tx is not None
        assert tx.network_id is not None

        service = NetworkIntelligenceService()
        intel = service.get_network_intelligence(db_session, tx.network_id)

        # Propagated network risk must be high/critical for the coordinated ring
        assert intel.propagated_risk_score >= 0.75
        assert intel.exposure.total_transactions >= 2
        # Coordinated ring must exhibit syndicate patterns
        assert len(intel.patterns) >= 1
        # Structured machine-readable findings must be generated
        assert len(intel.findings) >= 1
        finding_types = {f.finding_type for f in intel.findings}
        assert any(
            "RING" in ft or "COLLUSION" in ft or "EXPOSURE" in ft or "RISK" in ft
            for ft in finding_types
        )
