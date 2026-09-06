"""FraudDNA V2 Data Migration & Persistence Integration Test Suite.

Verifies:
1. Source artifact validation
2. Deterministic & idempotent database migration
3. Entity foreign key referential integrity
4. Network and cluster persistence
5. Point-in-time RiskAssessment and Tree SHAP RiskSignal persistence
6. Investigation and decision lineage
7. Known transaction behaviors (tx_0001991)
8. API behavior under ENABLE_PERSISTENT_STORAGE=True
"""

from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_sync_db
from app.main import app
from app.models.domain import (
    AuditEventModel,
    CustomerModel,
    DecisionModel,
    EvidenceModel,
    InvestigationModel,
    ModelRegistryModel,
    PolicyModel,
    RiskAssessmentModel,
    RiskSignalModel,
    TransactionModel,
)
from app.services.migration import DataMigrationService


@pytest.fixture(scope="module")
def migration_engine():
    """Create in-memory SQLite engine with StaticPool for migration tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def migration_session(migration_engine) -> Generator[Session, None, None]:
    """Provide a session connected to the migration engine."""
    session_factory = sessionmaker(bind=migration_engine)
    session = session_factory()
    yield session
    session.close()


def test_validate_source_artifacts():
    """Verify that source artifacts exist and validate successfully."""
    migrator = DataMigrationService()
    status = migrator.validate_source_artifacts()
    assert status["transactions_csv"] is True
    assert status["model_metadata"] is True
    assert status["lightgbm_model"] is True
    assert status["feature_pipeline"] is True
    assert status["knowledge_dir"] is True


def test_initial_migration_execution(migration_session: Session):
    """Execute migration on a 2,000-row subset and verify all domain entities are persisted."""
    migrator = DataMigrationService()
    # Migrate first 2,000 rows (which includes the known cluster and tx_0001991)
    result = migrator.migrate_sync(
        session=migration_session,
        batch_size=500,
        compute_risk=True,
        compute_signals=True,
        limit=2000,
    )

    assert result.total_processed == 2000
    assert result.transactions_count == 2000
    assert result.customers_count > 0
    assert result.accounts_count > 0
    assert result.cards_count > 0
    assert result.devices_count > 0
    assert result.ips_count > 0
    assert result.merchants_count > 0
    assert result.models_count == 1
    assert result.policies_count == 1
    assert result.sources_count > 0
    assert result.assessments_count == 2000
    assert result.signals_count > 0

    # Verify ModelRegistry entry
    model_reg = migration_session.execute(
        select(ModelRegistryModel).where(ModelRegistryModel.id == "mdl_lightgbm_v010")
    ).scalar_one()
    assert model_reg.status == "ACTIVE"
    assert model_reg.operating_threshold == 0.37
    assert model_reg.feature_count == 18

    # Verify Policy entry
    policy = migration_session.execute(
        select(PolicyModel).where(PolicyModel.id == "pol_2025_1")
    ).scalar_one()
    assert policy.version == "2025.1"
    assert policy.rules_config["hold_risk_threshold"] == 0.90


def test_referential_integrity_verification(migration_session: Session):
    """Verify that all 11 referential integrity and consistency checks pass."""
    migrator = DataMigrationService()
    integrity = migrator.verify_integrity(migration_session)

    assert integrity.is_valid is True
    assert integrity.checks_failed == 0
    assert integrity.checks_passed >= 10
    assert integrity.details["transaction_count_positive"] == "PASSED"
    assert integrity.details["customer_fk_integrity"] == "PASSED"
    assert integrity.details["merchant_fk_integrity"] == "PASSED"
    assert integrity.details["card_fk_integrity"] == "PASSED"
    assert integrity.details["device_fk_integrity"] == "PASSED"
    assert integrity.details["ip_fk_integrity"] == "PASSED"
    assert integrity.details["network_fk_integrity"] == "PASSED"
    assert integrity.details["assessment_fk_integrity"] == "PASSED"
    assert integrity.details["signal_fk_integrity"] == "PASSED"
    assert integrity.details["transaction_risk_score_bounds"] == "PASSED"


def test_known_transaction_behavior(migration_session: Session):
    """Verify known critical transaction tx_0001991 maintains high risk, critical tier, and HOLD action."""
    tx = migration_session.execute(
        select(TransactionModel).where(TransactionModel.id == "tx_0001991")
    ).scalar_one_or_none()

    assert tx is not None
    assert tx.risk_score >= 0.90
    assert tx.risk_tier == "CRITICAL"
    assert tx.decision_action == "HOLD"
    assert tx.network_id is not None  # Belong to detected cluster

    # Verify corresponding RiskAssessment
    ras = migration_session.execute(
        select(RiskAssessmentModel).where(RiskAssessmentModel.transaction_id == "tx_0001991")
    ).scalar_one()
    assert ras.risk_score >= 0.90
    assert ras.risk_tier == "CRITICAL"

    # Verify structured Tree SHAP signals exist
    signals = list(
        migration_session.execute(
            select(RiskSignalModel).where(RiskSignalModel.assessment_id == ras.id)
        )
        .scalars()
        .all()
    )
    assert len(signals) > 0
    assert len(signals) <= 5  # Bounded Top-5 policy
    ranks = [s.rank for s in signals]
    assert ranks == list(range(1, len(signals) + 1))
    for s in signals:
        assert s.feature_name != ""
        assert s.direction in ("INCREASES_RISK", "DECREASES_RISK", "NEUTRAL")


def test_migration_idempotency(migration_session: Session):
    """Running migration a second time must produce 0 duplicate records and preserve counts."""
    migrator = DataMigrationService()

    # Capture pre-counts
    tx_before = migration_session.execute(select(func.count(TransactionModel.id))).scalar()
    cust_before = migration_session.execute(select(func.count(CustomerModel.id))).scalar()
    ras_before = migration_session.execute(select(func.count(RiskAssessmentModel.id))).scalar()
    sig_before = migration_session.execute(select(func.count(RiskSignalModel.id))).scalar()

    # Rerun migration
    result2 = migrator.migrate_sync(
        session=migration_session,
        batch_size=500,
        compute_risk=True,
        compute_signals=True,
        limit=2000,
    )

    # All inserted counts for new records must be zero
    assert result2.transactions_count == 0
    assert result2.assessments_count == 0
    assert result2.signals_count == 0
    assert result2.networks_count == 0
    assert result2.customers_count == 0
    assert result2.accounts_count == 0
    assert result2.cards_count == 0
    assert result2.devices_count == 0
    assert result2.ips_count == 0
    assert result2.merchants_count == 0
    assert result2.models_count == 0
    assert result2.policies_count == 0
    assert result2.sources_count == 0

    # Post-counts must match exactly
    tx_after = migration_session.execute(select(func.count(TransactionModel.id))).scalar()
    cust_after = migration_session.execute(select(func.count(CustomerModel.id))).scalar()
    ras_after = migration_session.execute(select(func.count(RiskAssessmentModel.id))).scalar()
    sig_after = migration_session.execute(select(func.count(RiskSignalModel.id))).scalar()

    assert tx_after == tx_before
    assert cust_after == cust_before
    assert ras_after == ras_before
    assert sig_after == sig_before


def test_complete_investigation_lineage(migration_session: Session):
    """Verify complete lineage: Transaction -> Assessment -> Signal -> Network -> Investigation -> Evidence -> Decision -> Audit."""
    from app.services.audit import AuditService
    from app.services.decision import DecisionService
    from app.services.investigation import InvestigationService

    inv_service = InvestigationService()
    decision_service = DecisionService()
    audit_service = AuditService()

    # 1. Investigate and persist tx_0001991
    inv_resp = inv_service.investigate_and_persist(
        session=migration_session,
        transaction_id="tx_0001991",
    )
    assert inv_resp.risk_score >= 0.90
    assert inv_resp.risk_level.value == "critical"

    # Verify InvestigationModel in DB
    inv_model = migration_session.execute(
        select(InvestigationModel).where(InvestigationModel.primary_transaction_id == "tx_0001991")
    ).scalar_one()
    assert inv_model.risk_level == "CRITICAL"
    assert inv_model.primary_network_id is not None

    # Verify EvidenceModel in DB
    evidence_records = list(
        migration_session.execute(
            select(EvidenceModel).where(EvidenceModel.investigation_id == inv_model.id)
        )
        .scalars()
        .all()
    )
    assert len(evidence_records) > 0

    # 2. Evaluate policy and persist decision
    decision_resp = decision_service.evaluate_and_persist(
        session=migration_session,
        transaction_id="tx_0001991",
        actor="lead_investigator_v2",
    )
    assert decision_resp.action.value == "HOLD"

    # Verify DecisionModel in DB
    dec_model = migration_session.execute(
        select(DecisionModel).where(DecisionModel.transaction_id == "tx_0001991")
    ).scalar_one()
    assert dec_model.action == "HOLD"
    assert "CRITICAL_RISK_SCORE" in dec_model.reason_codes

    # Verify AuditEventModel in DB
    audit_events = list(
        migration_session.execute(
            select(AuditEventModel).where(
                AuditEventModel.entity_type == "transaction",
                AuditEventModel.entity_id == "tx_0001991",
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_events) > 0
    assert audit_events[-1].event_hash != ""

    # Verify audit chain integrity
    chain_report = audit_service.verify_audit_chain(migration_session)
    assert chain_report.is_valid is True
    assert chain_report.verified_events >= 1


def test_api_persistent_path_transactions(migration_engine):
    """Verify /transactions and /transactions/{id} serve from DB when ENABLE_PERSISTENT_STORAGE=True."""
    session_factory = sessionmaker(bind=migration_engine)

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

            # 1. List transactions from DB
            resp = client.get("/api/v1/transactions?limit=10")
            assert resp.status_code == 200
            data = resp.json()
            assert data["limit"] == 10
            assert len(data["transactions"]) == 10
            assert "transaction_id" in data["transactions"][0]

            # 2. Detail lookup for tx_0001991 from DB
            resp_detail = client.get("/api/v1/transactions/tx_0001991")
            assert resp_detail.status_code == 200
            detail = resp_detail.json()
            assert detail["transaction_id"] == "tx_0001991"
            assert detail["risk_score"] >= 0.90
            assert detail["risk_level"] == "critical"
            assert detail["cluster_id"] is not None
    finally:
        app.dependency_overrides.pop(get_sync_db, None)
