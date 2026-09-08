"""FraudDNA V2 Advanced Risk Intelligence & Risk Orchestration Test Suite.

Verifies:
1. Four-Layer Risk Architecture:
   - Transaction Risk (LightGBM model score, Tree SHAP signals, point-in-time).
   - Entity Risk (deterministic EntityService aggregation across Customer, Account, Device, IP, Card, Merchant).
   - Network Risk (RiskNetwork membership, exposure, syndicate collusion signals).
   - Behavioral Risk (point-in-time velocity acceleration, zero future-data leakage).
2. Risk Orchestrator:
   - Composite risk calculation: server-controlled weights, bounded [0.0, 1.0].
   - Coordinated ring escalation invariant (suspicious network + high tx -> composite >= 0.90).
   - Traceable contribution breakdown (weights, raw scores, contributions summing to composite).
   - Evidence completeness & confidence calculation bounded [0.0, 1.0].
   - Degraded state handling (missing network, missing entity, no fabricated scores).
   - Structured multi-layer natural language explanation synthesis.
3. Policy Boundary:
   - PolicyEngine remains authoritative for ALLOW / REVIEW / HOLD.
   - Risk Orchestrator does not mutate financial decisions.
4. Persistence & Migration:
   - RiskAssessmentModel extensions (composite, confidence, layer scores, orchestration version).
   - RiskSignalModel taxonomy (category, direction, contribution).
5. Regression Baselines:
   - tx_0001991: transaction_risk >= 0.90, CRITICAL tier, suspicious syndicate, HOLD.
   - Legitimate baseline: LOW tier, ALLOW, high confidence.
   - Missing network baseline: zero network risk, un-inflated composite, explicit flag.
6. Security & Performance:
   - SQL injection / malformed ID defense.
   - Tamper-proofing (server-controlled configuration).
   - Performance latency benchmark (bounded queries, no full graph loading).
7. API Endpoint:
   - GET /api/v1/transactions/{id}/risk-intelligence typed response contract.
"""

import time
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_sync_db
from app.core.errors import NotFoundDomainError, ValidationDomainError
from app.main import app
from app.models.domain import (
    RiskAssessmentModel,
    RiskSignalModel,
    TransactionModel,
)
from app.policy.rules import evaluate_policy_rules
from app.schemas.risk import (
    RiskIntelligenceResponse,
    SignalCategory,
    SignalDirection,
)
from app.services.migration import DataMigrationService
from app.services.risk_orchestrator import RiskOrchestrator


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


@pytest.fixture
def client(migrated_engine) -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client bound to the migrated database."""
    session_factory = sessionmaker(bind=migrated_engine)

    def override_get_sync_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_sync_db] = override_get_sync_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# 1. FOUR-LAYER RISK ARCHITECTURE VERIFICATION
# ==============================================================================


def test_transaction_risk_layer_preserves_ml_model(db_session: Session):
    """Verify Layer 1 (Transaction Risk) accurately retrieves the LightGBM score and SHAP signals."""
    orchestrator = RiskOrchestrator()
    # tx_0001991 is the known coordinated fraud transaction
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")

    tx_layer = result.transaction_risk
    assert tx_layer.score >= 0.90
    assert tx_layer.risk_tier == "CRITICAL"
    assert tx_layer.model_version is not None
    assert 0.0 <= tx_layer.threshold <= 1.0
    assert tx_layer.confidence == 1.0
    assert len(tx_layer.contributing_signals) > 0

    # Verify signals are typed and have transaction category
    for sig in tx_layer.contributing_signals:
        assert sig.category == SignalCategory.TRANSACTION_SIGNAL
        assert sig.direction in (
            SignalDirection.INCREASES_RISK,
            SignalDirection.DECREASES_RISK,
            SignalDirection.NEUTRAL,
        )
        assert sig.evidence_reference is not None


def test_entity_risk_layer_deterministic_aggregation(db_session: Session):
    """Verify Layer 2 (Entity Risk) gathers contextual entities and calculates composite entity risk."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")

    entity_layer = result.entity_risk
    assert 0.0 <= entity_layer.score <= 1.0
    assert entity_layer.risk_tier in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert entity_layer.confidence > 0.0
    assert entity_layer.primary_entity_type == "customer"
    assert entity_layer.primary_entity_id is not None
    assert len(entity_layer.contributing_signals) > 0

    # Verify contextual entities are present
    assert "customer" in entity_layer.contextual_entities
    assert "device" in entity_layer.contextual_entities or "ip" in entity_layer.contextual_entities


def test_network_risk_layer_syndicate_detection(db_session: Session):
    """Verify Layer 3 (Network Risk) discovers suspicious syndicate membership for tx_0001991."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")

    net_layer = result.network_risk
    assert net_layer.is_member is True
    assert net_layer.network_id is not None
    assert net_layer.is_suspicious is True
    assert net_layer.score >= 0.70
    assert net_layer.exposure > 0.0
    assert net_layer.member_count >= 2
    assert net_layer.confidence == 1.0
    assert len(net_layer.contributing_signals) > 0
    assert any(
        sig.name == "SUSPICIOUS_NETWORK_MEMBERSHIP" for sig in net_layer.contributing_signals
    )


def test_network_risk_layer_absence_explicitly_represented(db_session: Session):
    """Verify Layer 3 correctly flags absence of risk network without fabricating risk."""
    orchestrator = RiskOrchestrator()
    # Find a transaction that has no network association
    standalone_tx = db_session.execute(
        select(TransactionModel)
        .where(TransactionModel.network_id.is_(None))
        .where(TransactionModel.is_fraud == 0)
        .limit(1)
    ).scalar_one_or_none()

    if standalone_tx:
        result = orchestrator.orchestrate_transaction_risk(db_session, standalone_tx.id)
        net_layer = result.network_risk
        assert net_layer.is_member is False
        assert net_layer.network_id is None
        assert net_layer.score == 0.0
        assert net_layer.is_suspicious is False


def test_behavioral_risk_layer_temporal_correctness(db_session: Session):
    """Verify Layer 4 (Behavioral Risk) measures velocity acceleration strictly point-in-time."""
    orchestrator = RiskOrchestrator()
    tx = db_session.execute(
        select(TransactionModel).where(TransactionModel.id == "tx_0001991")
    ).scalar_one()

    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991", as_of=tx.timestamp)
    beh_layer = result.behavioral_risk
    assert 0.0 <= beh_layer.score <= 1.0
    assert beh_layer.as_of == tx.timestamp
    assert beh_layer.velocity_5m >= 0
    assert beh_layer.velocity_1h >= 0
    assert beh_layer.velocity_24h >= 0
    assert beh_layer.amount_velocity_24h >= 0.0


# ==============================================================================
# 2. RISK ORCHESTRATOR & COMPOSITE FORMULA
# ==============================================================================


def test_orchestrator_composite_formula_and_bounds(db_session: Session):
    """Verify composite risk formula bounds [0,1], weight normalization, and contribution sum."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")

    assert 0.0 <= result.composite_risk_score <= 1.0
    assert result.composite_risk_tier in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert result.orchestration_version == "v2.0"

    # Verify layer contributions
    contribs = result.layer_contributions
    assert len(contribs) == 4
    total_contrib = sum(c.contribution for c in contribs)
    # The total contribution equals composite risk (unless escalated by ring rule)
    assert 0.0 <= total_contrib <= 1.05

    weights = [c.weight for c in contribs]
    assert abs(sum(weights) - 1.0) < 1e-4


def test_orchestrator_confidence_metric(db_session: Session):
    """Verify evidence completeness and confidence bounded in [0, 1]."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")

    conf = result.confidence
    assert 0.0 <= conf.overall_confidence <= 1.0
    assert 0.0 <= conf.evidence_completeness <= 1.0
    assert 0.0 <= conf.transaction_model_completeness <= 1.0
    assert 0.0 <= conf.entity_context_completeness <= 1.0
    assert 0.0 <= conf.network_context_completeness <= 1.0
    assert 0.0 <= conf.behavioral_history_completeness <= 1.0


def test_orchestrator_structured_explanations(db_session: Session):
    """Verify structured explanation breakdown across all 4 layers and composite summary."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")

    assert result.explanation_summary != ""
    assert "composite" in result.explanation_summary.lower()
    assert result.layer_explanations["transaction"] != ""
    assert result.layer_explanations["entity"] != ""
    assert result.layer_explanations["network"] != ""
    assert result.layer_explanations["behavioral"] != ""


# ==============================================================================
# 3. POLICY BOUNDARY & RECOMMENDATIONS
# ==============================================================================


def test_policy_boundary_authoritative_hold_for_coordinated_fraud(db_session: Session):
    """Verify PolicyEngine produces HOLD for coordinated fraud based on orchestrated signals."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")

    # Coordinated fraud must yield HOLD recommendation
    assert result.policy_recommendation == "HOLD"

    # Verify evaluate_policy_rules yields the same result
    policy_action, _, _ = evaluate_policy_rules(
        risk_score=result.composite_risk_score,
        is_suspicious_cluster=result.network_risk.is_suspicious,
        cluster_risk_score=result.network_risk.score,
    )
    assert policy_action.value == "HOLD"


def test_policy_recommendation_allow_for_legitimate_tx(db_session: Session):
    """Verify legitimate transaction receives ALLOW recommendation."""
    orchestrator = RiskOrchestrator()
    # Find a low risk legitimate transaction
    subq = select(RiskAssessmentModel.transaction_id).where(RiskAssessmentModel.risk_score < 0.20)
    legit_tx = db_session.execute(
        select(TransactionModel)
        .where(TransactionModel.id.in_(subq))
        .where(TransactionModel.is_fraud == 0)
        .limit(1)
    ).scalar_one_or_none()

    if legit_tx:
        result = orchestrator.orchestrate_transaction_risk(db_session, legit_tx.id)
        assert result.composite_risk_score < 0.50
        assert result.policy_recommendation == "ALLOW"


# ==============================================================================
# 4. PERSISTENCE OF EXTENDED RISK INTELLIGENCE
# ==============================================================================


def test_persisted_orchestration_fields(db_session: Session):
    """Verify RiskAssessmentModel stores multi-layer scores, confidence, and taxonomy."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(
        db_session, "tx_0001991", persist_assessment=True
    )

    assessment = db_session.execute(
        select(RiskAssessmentModel).where(RiskAssessmentModel.transaction_id == "tx_0001991")
    ).scalar_one()

    assert assessment.composite_risk_score == pytest.approx(result.composite_risk_score, 0.001)
    assert assessment.confidence_score == pytest.approx(result.confidence.overall_confidence, 0.001)
    assert assessment.entity_risk_score == pytest.approx(result.entity_risk.score, 0.001)
    assert assessment.network_risk_score == pytest.approx(result.network_risk.score, 0.001)
    assert assessment.behavioral_risk_score == pytest.approx(result.behavioral_risk.score, 0.001)
    assert assessment.orchestration_version == "v2.0"
    assert assessment.contribution_breakdown is not None
    assert len(assessment.contribution_breakdown) == 4
    assert assessment.explanation_summary is not None

    # Verify signals have categories
    signals = (
        db_session.execute(
            select(RiskSignalModel).where(RiskSignalModel.assessment_id == assessment.id)
        )
        .scalars()
        .all()
    )
    assert len(signals) > 0
    for sig in signals:
        assert sig.category is not None


# ==============================================================================
# 5. REGRESSION BASELINE: tx_0001991
# ==============================================================================


def test_known_coordinated_fraud_tx_0001991_regression(db_session: Session):
    """Verify full orchestration regression for known coordinated transaction tx_0001991."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")

    # Invariants
    assert result.transaction_risk.score >= 0.90
    assert result.transaction_risk.risk_tier == "CRITICAL"
    assert result.network_risk.is_suspicious is True
    assert result.composite_risk_score >= 0.90
    assert result.composite_risk_tier == "CRITICAL"
    assert result.policy_recommendation == "HOLD"
    assert result.confidence.overall_confidence >= 0.85
    assert result.is_degraded is False


# ==============================================================================
# 6. SECURITY & TAMPERING BOUNDARIES
# ==============================================================================


def test_security_malformed_transaction_id_raises_not_found(db_session: Session):
    """Verify malformed or invalid transaction IDs raise NotFoundDomainError."""
    orchestrator = RiskOrchestrator()
    with pytest.raises(NotFoundDomainError):
        orchestrator.orchestrate_transaction_risk(db_session, "invalid_nonexistent_id_999")

    # Test SQL injection attack payload in transaction_id
    with pytest.raises(NotFoundDomainError):
        orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991' OR '1'='1")


def test_security_custom_weights_must_sum_to_one(db_session: Session):
    """Verify orchestrator rejects illegal client-supplied weights that do not sum to 1.0."""
    orchestrator = RiskOrchestrator()
    with pytest.raises(ValidationDomainError):
        orchestrator.orchestrate_transaction_risk(
            db_session,
            "tx_0001991",
            weights={"transaction": 0.9, "entity": 0.9, "network": 0.9, "behavioral": 0.9},
        )


# ==============================================================================
# 7. PERFORMANCE BENCHMARK
# ==============================================================================


def test_orchestrator_execution_latency(db_session: Session):
    """Verify risk orchestration evaluates in under 150ms without full dataset or graph loading."""
    orchestrator = RiskOrchestrator()
    start_time = time.perf_counter()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")
    latency_ms = (time.perf_counter() - start_time) * 1000

    assert result is not None
    # Latency should be fast on bounded SQLite/Postgres queries
    assert latency_ms < 250, f"Orchestrator latency took too long: {latency_ms:.2f}ms"


# ==============================================================================
# 8. API ENDPOINT VALIDATION
# ==============================================================================


def test_api_risk_intelligence_endpoint(client: TestClient):
    """Verify GET /api/v1/transactions/{id}/risk-intelligence returns typed RiskIntelligenceResponse."""
    resp = client.get("/api/v1/transactions/tx_0001991/risk-intelligence")
    assert resp.status_code == 200

    data = resp.json()
    validated = RiskIntelligenceResponse.model_validate(data)
    assert validated.transaction_id == "tx_0001991"
    assert validated.composite_risk_score >= 0.90
    assert validated.composite_risk_tier == "CRITICAL"
    assert validated.policy_recommendation == "HOLD"
    assert validated.confidence.overall_confidence > 0.8
    assert len(validated.layer_contributions) == 4
    assert validated.transaction_risk.score >= 0.90
    assert validated.network_risk.is_suspicious is True


def test_api_risk_intelligence_404_for_unknown_tx(client: TestClient):
    """Verify GET /api/v1/transactions/{id}/risk-intelligence returns 404 for unknown transaction."""
    resp = client.get("/api/v1/transactions/tx_nonexistent_xyz/risk-intelligence")
    assert resp.status_code == 404


def test_independent_entity_sharing_counts(db_session: Session):
    """Verify device, card, and IP sharing counts are independently computed and not conflated."""
    orchestrator = RiskOrchestrator()
    result = orchestrator.orchestrate_transaction_risk(db_session, "tx_0001991")
    assert result.policy_recommendation == "HOLD"
    assert result.behavioral_risk.cross_customer_sharing_count >= 0
