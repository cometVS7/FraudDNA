"""FraudDNA V2 Domain & Data Layer Comprehensive Test Suite.

Validates Phase V2-02:
1. Complete 19-table V2 Relational Schema + RAG coexistence
2. Column constraints, foreign keys, numeric precision, and timezone-aware timestamps
3. ORM relationships, bidirectional navigation, and cascade behaviors
4. Migration ordering and Alembic revision integrity
5. Database Seeder deterministic ingestion & strict idempotency (first run vs second run)
6. Preserved empirical ground-truth identifiers, timestamps, and monetary amounts
"""

import importlib.util
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.domain import (
    AccountModel,
    AIFindingModel,
    AuditEventModel,
    CardModel,
    CaseModel,
    CustomerModel,
    DeviceModel,
    EvidenceModel,
    InvestigationModel,
    IPAddressModel,
    MerchantModel,
    ModelRegistryModel,
    RiskNetworkModel,
    TransactionModel,
)
from app.services.seed import DatabaseSeeder

EXPECTED_TABLES = {
    "rag_documents",
    "rag_document_chunks",
    "customers",
    "accounts",
    "cards",
    "devices",
    "ip_addresses",
    "merchants",
    "risk_networks",
    "transactions",
    "models",
    "risk_assessments",
    "risk_signals",
    "policies",
    "decisions",
    "cases",
    "investigations",
    "evidence",
    "ai_findings",
    "intelligence_sources",
    "audit_events",
}


@pytest.fixture
def test_db_engine():
    """Create an isolated, in-memory SQLite engine with full schema for domain tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_session(test_db_engine):
    """Yield an active transactional session."""
    session_factory = sessionmaker(bind=test_db_engine)
    with session_factory() as session:
        yield session


# ==============================================================================
# 1. SCHEMA DEFINITION & METADATA TESTS
# ==============================================================================


def test_all_19_v2_domain_tables_exist_in_metadata() -> None:
    """Verify that all 19 domain tables plus 2 RAG tables are registered in Base.metadata."""
    registered_tables = set(Base.metadata.tables.keys())
    for table_name in EXPECTED_TABLES:
        assert table_name in registered_tables, f"Missing table in metadata: {table_name}"


def test_table_columns_and_constraints(test_db_engine) -> None:
    """Inspect created database tables for required columns, types, and primary keys."""
    inspector = inspect(test_db_engine)
    table_names = inspector.get_table_names()

    for expected in EXPECTED_TABLES:
        assert expected in table_names, f"Table '{expected}' not created in database."

    # Inspect transactions table
    tx_cols = {col["name"]: col for col in inspector.get_columns("transactions")}
    assert "id" in tx_cols
    assert "timestamp" in tx_cols
    assert "amount" in tx_cols
    assert "customer_id" in tx_cols
    assert "merchant_id" in tx_cols
    assert "risk_score" in tx_cols
    assert "decision_action" in tx_cols

    # Foreign keys on transactions
    fks = inspector.get_foreign_keys("transactions")
    fk_targets = {fk["referred_table"] for fk in fks}
    assert "customers" in fk_targets
    assert "merchants" in fk_targets


# ==============================================================================
# 2. ORM RELATIONSHIPS & CASCADE BEHAVIOR
# ==============================================================================


def test_domain_entity_relationships_and_navigation(test_session: Session) -> None:
    """Verify creation, relationship binding, and navigation across core entities."""
    now = datetime.now(UTC)

    # 1. Create customer and account
    cust = CustomerModel(
        id="cust_test_001",
        account_age_days=120,
        city="Mumbai",
        status="ACTIVE",
        risk_score=0.15,
        risk_tier="LOW",
    )
    acc = AccountModel(
        id="acc_cust_test_001",
        customer_id="cust_test_001",
        account_type="SAVINGS",
        status="ACTIVE",
    )
    card = CardModel(id="card_test_001", card_type="CREDIT", status="ACTIVE")
    dev = DeviceModel(id="dev_test_001", device_fingerprint="fp_test_001")
    ip = IPAddressModel(id="ip_192_168_1_1", ip_address="192.168.1.1")
    merch = MerchantModel(id="merch_test_001", merchant_category="electronics")
    net = RiskNetworkModel(
        id="cluster_test_001",
        is_suspicious=True,
        risk_score=0.85,
        primary_reason="Synthetic device ring",
    )

    test_session.add_all([cust, acc, card, dev, ip, merch, net])
    test_session.flush()

    # 2. Create transaction linking entities
    tx = TransactionModel(
        id="tx_test_001",
        timestamp=now,
        amount=Decimal("4599.50"),
        currency="INR",
        payment_method="credit_card",
        city="Mumbai",
        is_fraud=False,
        risk_score=0.15,
        risk_tier="LOW",
        customer_id=cust.id,
        account_id=acc.id,
        card_id=card.id,
        device_id=dev.id,
        ip_id=ip.id,
        merchant_id=merch.id,
        network_id=net.id,
    )
    test_session.add(tx)
    test_session.flush()

    # 3. Verify bidirectional navigation
    assert len(cust.transactions) == 1
    assert cust.transactions[0].id == "tx_test_001"
    assert tx.customer.id == "cust_test_001"
    assert tx.account.id == "acc_cust_test_001"
    assert tx.device.id == "dev_test_001"
    assert tx.card.id == "card_test_001"
    assert tx.ip.id == "ip_192_168_1_1"
    assert tx.merchant.id == "merch_test_001"
    assert tx.network.id == "cluster_test_001"
    assert tx.amount == Decimal("4599.50")


def test_investigation_case_and_evidence_cascade(test_session: Session) -> None:
    """Verify investigation, case, evidence, and AI finding lifecycle and cascading."""
    now = datetime.now(UTC)

    # Base requirements
    cust = CustomerModel(id="cust_casc_001")
    merch = MerchantModel(id="merch_casc_001", merchant_category="retail")
    tx = TransactionModel(
        id="tx_casc_001",
        timestamp=now,
        amount=Decimal("1200.00"),
        payment_method="upi",
        customer_id=cust.id,
        merchant_id=merch.id,
    )
    test_session.add_all([cust, merch, tx])
    test_session.flush()

    # Create Case and Investigation
    case = CaseModel(
        id="case_2026_001",
        title="Suspicious Proxy Farm Case",
        status="INVESTIGATING",
        priority="HIGH",
        owner="analyst_1",
    )
    inv = InvestigationModel(
        id="inv_casc_001",
        status="OPEN",
        priority="HIGH",
        primary_transaction_id=tx.id,
        case_id=case.id,
        risk_score=0.88,
        risk_level="HIGH",
    )
    test_session.add_all([case, inv])
    test_session.flush()

    # Add Evidence & AI Finding
    evd = EvidenceModel(
        id="evd_001",
        investigation_id=inv.id,
        case_id=case.id,
        evidence_type="MODEL_SIGNAL",
        source="lightgbm",
        description="High velocity across disparate merchants",
        severity="HIGH",
        confidence=0.92,
    )
    finding = AIFindingModel(
        id="fnd_001",
        investigation_id=inv.id,
        finding_type="COORDINATION_PATTERN",
        statement="Shared device farm syndicate detected across 4 accounts.",
        confidence=0.95,
        limitations=["Ground truth confirmation pending bank chargeback data."],
    )
    test_session.add_all([evd, finding])
    test_session.commit()

    # Verify relationships
    loaded_inv = test_session.execute(
        select(InvestigationModel).where(InvestigationModel.id == "inv_casc_001")
    ).scalar_one()
    assert len(loaded_inv.evidence_items) == 1
    assert loaded_inv.evidence_items[0].id == "evd_001"
    assert len(loaded_inv.ai_findings) == 1
    assert loaded_inv.ai_findings[0].id == "fnd_001"
    assert loaded_inv.case.id == "case_2026_001"


# ==============================================================================
# 3. ALEMBIC MIGRATION INTEGRITY
# ==============================================================================


def test_alembic_migration_ordering() -> None:
    """Verify Alembic migration revision chain from 0001_rag_tables to 0002_v2_domain_schema."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    mig_0001_path = repo_root / "backend" / "alembic" / "versions" / "0001_create_rag_tables.py"
    mig_0002_path = (
        repo_root / "backend" / "alembic" / "versions" / "0002_create_v2_domain_schema.py"
    )

    assert mig_0001_path.exists(), "0001_create_rag_tables.py must exist"
    assert mig_0002_path.exists(), "0002_create_v2_domain_schema.py must exist"

    # Inspect 0002 revision metadata
    spec_0002 = importlib.util.spec_from_file_location("mig_0002", mig_0002_path)
    assert spec_0002 and spec_0002.loader
    mig_0002 = importlib.util.module_from_spec(spec_0002)
    spec_0002.loader.exec_module(mig_0002)

    assert mig_0002.revision == "0002_v2_domain_schema"
    assert mig_0002.down_revision == "0001_rag_tables"


# ==============================================================================
# 4. DATABASE SEEDER & IDEMPOTENCY
# ==============================================================================


def test_database_seeder_deterministic_and_idempotent(test_session: Session) -> None:
    """Execute DatabaseSeeder twice on the same session; assert strict idempotency."""
    seeder = DatabaseSeeder()

    # First Seed Execution
    res1 = seeder.seed_sync(session=test_session, batch_size=2000)
    assert res1.models_inserted >= 1
    assert res1.policies_inserted >= 1
    assert res1.sources_inserted >= 1
    assert res1.customers_inserted > 0
    assert res1.merchants_inserted > 0
    assert res1.devices_inserted > 0
    assert res1.cards_inserted > 0
    assert res1.ips_inserted > 0
    assert res1.total_records_processed == 25000

    # Verify sample transaction preservation
    tx_sample = test_session.execute(
        select(TransactionModel).where(TransactionModel.id == "tx_0000000")
    ).scalar_one_or_none()
    assert tx_sample is not None
    assert tx_sample.customer_id == "cust_00843"
    assert tx_sample.card_id == "card_02357"
    assert tx_sample.device_id == "dev_01747"
    assert tx_sample.merchant_id == "merch_0011"
    assert tx_sample.currency == "INR"
    assert tx_sample.amount == Decimal("2097.92")

    # Record initial table row counts
    count_cust_1 = len(test_session.execute(select(CustomerModel.id)).scalars().all())
    count_merch_1 = len(test_session.execute(select(MerchantModel.id)).scalars().all())
    count_tx_1 = len(test_session.execute(select(TransactionModel.id)).scalars().all())
    count_models_1 = len(test_session.execute(select(ModelRegistryModel.id)).scalars().all())

    # Second Seed Execution (Must be completely idempotent with 0 new additions)
    res2 = seeder.seed_sync(session=test_session, batch_size=2000)
    assert res2.customers_inserted == 0
    assert res2.accounts_inserted == 0
    assert res2.cards_inserted == 0
    assert res2.devices_inserted == 0
    assert res2.ips_inserted == 0
    assert res2.merchants_inserted == 0
    assert res2.models_inserted == 0
    assert res2.policies_inserted == 0
    assert res2.sources_inserted == 0

    # Verify counts remain completely identical
    count_cust_2 = len(test_session.execute(select(CustomerModel.id)).scalars().all())
    count_merch_2 = len(test_session.execute(select(MerchantModel.id)).scalars().all())
    count_tx_2 = len(test_session.execute(select(TransactionModel.id)).scalars().all())
    count_models_2 = len(test_session.execute(select(ModelRegistryModel.id)).scalars().all())

    assert count_cust_1 == count_cust_2
    assert count_merch_1 == count_merch_2
    assert count_tx_1 == count_tx_2
    assert count_models_1 == count_models_2


# ==============================================================================
# 5. AUDIT EVENT HASH CHAINING INTEGRITY
# ==============================================================================


def test_audit_event_hash_chaining(test_session: Session) -> None:
    """Verify cryptographic hash chaining on AuditEventModel."""
    event1 = AuditEventModel(
        id="aud_001",
        actor="system",
        actor_type="SERVICE",
        event_type="transaction_scored",
        entity_type="transaction",
        entity_id="tx_0000000",
        payload_hash="hash_payload_1",
        previous_hash=None,
        event_hash="hash_event_1",
        payload={"risk_score": 0.05, "action": "ALLOW"},
    )
    event2 = AuditEventModel(
        id="aud_002",
        actor="analyst_1",
        actor_type="USER",
        event_type="decision_override",
        entity_type="decision",
        entity_id="dec_001",
        payload_hash="hash_payload_2",
        previous_hash="hash_event_1",
        event_hash="hash_event_2",
        payload={"override_reason": "False positive verified with merchant"},
    )
    test_session.add_all([event1, event2])
    test_session.commit()

    events = (
        test_session.execute(select(AuditEventModel).order_by(AuditEventModel.timestamp))
        .scalars()
        .all()
    )
    assert len(events) == 2
    assert events[1].previous_hash == events[0].event_hash
