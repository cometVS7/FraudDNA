"""FraudDNA V2 Repositories Unit Tests.

Validates CRUD, bounded pagination, multi-dimensional filtering,
ordering, and constraint handling across all V2 repositories.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.domain import (
    AccountModel,
    AuditEventModel,
    CardModel,
    CaseModel,
    CustomerModel,
    DeviceModel,
    IPAddressModel,
    MerchantModel,
    ModelRegistryModel,
    RiskNetworkModel,
    TransactionModel,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.entity_repository import EntityRepository
from app.repositories.model_repository import ModelRegistryRepository
from app.repositories.transaction_repository import TransactionRepository


@pytest.fixture
def test_db_session():
    """Create in-memory SQLite engine and session for repository testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_transaction_repository_crud_and_filtering(test_db_session: Session) -> None:
    """Verify transaction querying, bounded limits, and multi-dimensional filters."""
    repo = TransactionRepository()
    now = datetime.now(UTC)

    # Insert prerequisites
    cust = CustomerModel(id="cust_repo_1", created_at=now, account_age_days=100, city="Mumbai")
    merch = MerchantModel(
        id="m_repo_1",
        merchant_category="GROCERY",
        status="ACTIVE",
        created_at=now,
    )
    dev = DeviceModel(
        id="dev_repo_1",
        device_fingerprint="fp_dev_1",
        status="ACTIVE",
        first_seen=now,
        last_seen=now,
    )
    test_db_session.add_all([cust, merch, dev])
    test_db_session.flush()

    # Insert 2 transactions
    tx1 = TransactionModel(
        id="tx_test_001",
        timestamp=now,
        amount=Decimal("1500.00"),
        currency="INR",
        payment_method="UPI",
        city="Mumbai",
        customer_id="cust_repo_1",
        merchant_id="m_repo_1",
        device_id="dev_repo_1",
        risk_score=0.15,
        risk_tier="LOW",
        decision_action="ALLOW",
        is_fraud=False,
    )
    tx2 = TransactionModel(
        id="tx_test_002",
        timestamp=now,
        amount=Decimal("85000.00"),
        currency="INR",
        payment_method="CREDIT_CARD",
        city="Mumbai",
        customer_id="cust_repo_1",
        merchant_id="m_repo_1",
        device_id="dev_repo_1",
        risk_score=0.88,
        risk_tier="CRITICAL",
        decision_action="HOLD",
        is_fraud=True,
    )
    test_db_session.add_all([tx1, tx2])
    test_db_session.commit()

    # 1. Get by ID
    found = repo.get_by_id(test_db_session, "tx_test_001")
    assert found is not None
    assert found.amount == Decimal("1500.00")
    assert found.risk_tier == "LOW"

    # 2. Missing ID
    missing = repo.get_by_id(test_db_session, "tx_nonexistent")
    assert missing is None

    # 3. Filter by risk_tier
    items, total = repo.list_transactions(test_db_session, risk_tier="CRITICAL")
    assert total == 1
    assert len(items) == 1
    assert items[0].id == "tx_test_002"

    # 4. Filter by decision_action
    items, total = repo.list_transactions(test_db_session, decision_action="ALLOW")
    assert total == 1
    assert items[0].id == "tx_test_001"

    # 5. Filter by min amount
    items, total = repo.list_transactions(test_db_session, min_amount=Decimal("50000.00"))
    assert total == 1
    assert items[0].id == "tx_test_002"

    # 6. Safe limit clamping (requesting 1000 should be bounded)
    items, total = repo.list_transactions(test_db_session, limit=1000)
    assert len(items) == 2


def test_entity_repository_lookups(test_db_session: Session) -> None:
    """Verify entity repository retrieval for all entity types."""
    repo = EntityRepository()
    now = datetime.now(UTC)

    cust = CustomerModel(id="cust_ent_1", created_at=now, city="Mumbai")
    acc = AccountModel(id="acc_ent_1", customer_id="cust_ent_1", created_at=now)
    card = CardModel(
        id="card_ent_1",
        card_type="CREDIT",
        status="ACTIVE",
        first_seen=now,
        last_seen=now,
    )
    dev = DeviceModel(
        id="dev_ent_1",
        device_fingerprint="fp_dev_2",
        status="ACTIVE",
        first_seen=now,
        last_seen=now,
    )
    ip = IPAddressModel(
        id="192.168.1.1",
        ip_address="192.168.1.1",
        status="ACTIVE",
        first_seen=now,
        last_seen=now,
    )
    merch = MerchantModel(
        id="m_ent_1",
        merchant_category="ELECTRONICS",
        status="ACTIVE",
        created_at=now,
    )
    net = RiskNetworkModel(
        id="net_ent_1",
        network_name="Sim Box Alpha",
        risk_score=0.85,
        is_suspicious=True,
    )
    test_db_session.add_all([cust, acc, card, dev, ip, merch, net])
    test_db_session.commit()

    assert repo.get_customer(test_db_session, "cust_ent_1") is not None
    assert repo.get_account(test_db_session, "acc_ent_1") is not None
    assert repo.get_card(test_db_session, "card_ent_1") is not None
    assert repo.get_device(test_db_session, "dev_ent_1") is not None
    assert repo.get_ip_address(test_db_session, "192.168.1.1") is not None
    assert repo.get_merchant(test_db_session, "m_ent_1") is not None
    assert repo.get_risk_network(test_db_session, "net_ent_1") is not None

    # Verify missing returns None
    assert repo.get_customer(test_db_session, "cust_missing") is None


def test_case_repository_operations(test_db_session: Session) -> None:
    """Verify CaseRepository create, update, and filtered pagination."""
    repo = CaseRepository()
    now = datetime.now(UTC)

    case1 = CaseModel(
        id="case_rep_1",
        title="High velocity fraud ring",
        status="NEW",
        priority="HIGH",
        owner="analyst_vikram",
        created_at=now,
        updated_at=now,
    )
    case2 = CaseModel(
        id="case_rep_2",
        title="Dormant account reactivation",
        status="IN_REVIEW",
        priority="MEDIUM",
        owner="analyst_priya",
        created_at=now,
        updated_at=now,
    )
    repo.create(test_db_session, case1)
    repo.create(test_db_session, case2)
    test_db_session.commit()

    # Get by ID
    fetched = repo.get_by_id(test_db_session, "case_rep_1")
    assert fetched is not None
    assert fetched.title == "High velocity fraud ring"

    # Update
    fetched.notes = "Escalating to financial crime unit"
    repo.update(test_db_session, fetched)
    test_db_session.commit()

    refetched = repo.get_by_id(test_db_session, "case_rep_1")
    assert refetched.notes == "Escalating to financial crime unit"

    # List with status filter
    items, total = repo.list_cases(test_db_session, status="IN_REVIEW")
    assert total == 1
    assert items[0].id == "case_rep_2"


def test_audit_repository_hash_chain(test_db_session: Session) -> None:
    """Verify AuditRepository append and retrieval of latest tip."""
    repo = AuditRepository()
    now = datetime.now(UTC)

    assert repo.get_latest_event(test_db_session) is None

    ev1 = AuditEventModel(
        id="aud_001",
        timestamp=now,
        actor="system",
        actor_type="SERVICE",
        event_type="SYSTEM_BOOT",
        entity_type="system",
        entity_id="frauddna_core",
        payload_hash="hash_p_1",
        previous_hash="0" * 64,
        event_hash="sig_1",
        payload={"boot": True},
    )
    repo.create(test_db_session, ev1)
    test_db_session.commit()

    latest = repo.get_latest_event(test_db_session)
    assert latest is not None
    assert latest.id == "aud_001"
    assert latest.event_hash == "sig_1"


def test_model_registry_repository(test_db_session: Session) -> None:
    """Verify ModelRegistryRepository active model retrieval and version lookup."""
    repo = ModelRegistryRepository()
    now = datetime.now(UTC)

    m1 = ModelRegistryModel(
        id="mdl_v1",
        model_name="LightGBM Fraud Risk",
        version="v1.0.0",
        model_type="lightgbm",
        status="ACTIVE",
        operating_threshold=0.37,
        feature_names=["f1", "f2"],
        feature_count=2,
        artifact_path="ml/models/v1.joblib",
        created_at=now,
    )
    m2 = ModelRegistryModel(
        id="mdl_v2",
        model_name="LightGBM Fraud Risk",
        version="v2.0.0-candidate",
        model_type="lightgbm",
        status="INACTIVE",
        operating_threshold=0.40,
        feature_names=["f1", "f2"],
        feature_count=2,
        artifact_path="ml/models/v2.joblib",
        created_at=now,
    )
    test_db_session.add_all([m1, m2])
    test_db_session.commit()

    active = repo.get_active_model(test_db_session, model_type="lightgbm")
    assert active is not None
    assert active.version == "v1.0.0"

    by_ver = repo.get_by_version(test_db_session, "v2.0.0-candidate")
    assert by_ver is not None
    assert by_ver.status == "INACTIVE"
