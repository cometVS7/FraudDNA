"""FraudDNA V2 Services Unit Tests.

Validates domain business services:
1. CaseService state machine, lifecycle transitions, and audit generation
2. AuditService SHA-256 hash chaining, verification, and tamper detection
3. DecisionService deterministic policy evaluation, persistence, and ALLOW/REVIEW/HOLD vocabulary
4. TransactionService detail enrichment and bounded queries
5. EntityService profile retrieval
6. ModelService model registry lookups
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.core.errors import NotFoundDomainError, ValidationDomainError
from app.models.domain import (
    CustomerModel,
    DeviceModel,
    MerchantModel,
    ModelRegistryModel,
    TransactionModel,
)
from app.schemas.case import (
    CaseCreateRequest,
    CasePriority,
    CaseStatus,
    CaseStatusUpdateRequest,
)
from app.services.audit import AuditService
from app.services.case import CaseService
from app.services.decision import DecisionService
from app.services.entity import EntityService
from app.services.model import ModelService
from app.services.transaction_service import TransactionService


@pytest.fixture
def service_test_session():
    """Create isolated in-memory SQLite session for service tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_case_service_lifecycle_and_state_machine(service_test_session: Session) -> None:
    """Validate case creation, valid transition sequence, and invalid transition rejection."""
    case_service = CaseService()
    audit_service = AuditService()

    # 1. Create a case
    req = CaseCreateRequest(
        title="Unusual IP Hopping Investigation",
        priority=CasePriority.HIGH,
        owner="analyst_1",
        notes="Multiple logins across 3 countries within 1 hour",
    )
    created = case_service.create_case(service_test_session, req, actor="analyst_1")
    service_test_session.commit()

    assert created.status == CaseStatus.NEW.value
    assert created.priority == CasePriority.HIGH.value
    assert created.owner == "analyst_1"

    # Verify audit event for creation
    events = audit_service.list_events(
        service_test_session, entity_type="case", entity_id=created.id
    )
    assert events.total_count == 1
    assert events.items[0].event_type == "CASE_CREATED"

    # 2. Valid transition: NEW -> IN_REVIEW
    update_req = CaseStatusUpdateRequest(
        status=CaseStatus.IN_REVIEW,
        notes="Beginning graph neighborhood inspection",
    )
    in_review = case_service.update_case_status(
        service_test_session, created.id, update_req, actor="analyst_1"
    )
    service_test_session.commit()
    assert in_review.status == CaseStatus.IN_REVIEW.value

    # 3. Invalid transition: IN_REVIEW -> NEW (cannot revert to NEW)
    invalid_req = CaseStatusUpdateRequest(status=CaseStatus.NEW)
    with pytest.raises(ValidationDomainError) as exc_info:
        case_service.update_case_status(
            service_test_session, created.id, invalid_req, actor="analyst_1"
        )
    assert "Invalid case status transition" in str(exc_info.value.message)

    # 4. Valid transition: IN_REVIEW -> ESCALATED
    esc_req = CaseStatusUpdateRequest(
        status=CaseStatus.ESCALATED, notes="Escalating to fraud operations manager"
    )
    escalated = case_service.update_case_status(
        service_test_session, created.id, esc_req, actor="analyst_1"
    )
    service_test_session.commit()
    assert escalated.status == CaseStatus.ESCALATED.value

    # 5. Valid transition: ESCALATED -> RESOLVED
    res_req = CaseStatusUpdateRequest(
        status=CaseStatus.RESOLVED, notes="Confirmed fraudulent proxy farm"
    )
    resolved = case_service.update_case_status(
        service_test_session, created.id, res_req, actor="manager_2"
    )
    service_test_session.commit()
    assert resolved.status == CaseStatus.RESOLVED.value

    # 6. Valid transition: RESOLVED -> CLOSED
    close_req = CaseStatusUpdateRequest(
        status=CaseStatus.CLOSED, notes="Accounts frozen, reported to FIU"
    )
    closed = case_service.update_case_status(
        service_test_session, created.id, close_req, actor="manager_2"
    )
    service_test_session.commit()
    assert closed.status == CaseStatus.CLOSED.value
    assert closed.closed_at is not None

    # Verify audit chain now contains all transition events
    audit_chain = audit_service.list_events(
        service_test_session, entity_type="case", entity_id=created.id
    )
    assert audit_chain.total_count == 5  # 1 create + 4 status updates


def test_audit_service_cryptographic_chain_and_tamper_detection(
    service_test_session: Session,
) -> None:
    """Validate SHA-256 hash chaining and verify tamper detection."""
    audit_service = AuditService()
    now = datetime.now(UTC)

    # Record 3 events
    ev1 = audit_service.record_event(
        session=service_test_session,
        actor="svc_auth",
        actor_type="SERVICE",
        event_type="LOGIN_SUCCESS",
        entity_type="user",
        entity_id="u_001",
        payload={"ip": "10.0.0.1"},
        timestamp=now,
    )
    ev2 = audit_service.record_event(
        session=service_test_session,
        actor="svc_policy",
        actor_type="SERVICE",
        event_type="POLICY_EVALUATION",
        entity_type="transaction",
        entity_id="tx_001",
        payload={"action": "ALLOW", "risk_score": 0.12},
        timestamp=now,
    )
    ev3 = audit_service.record_event(
        session=service_test_session,
        actor="analyst_1",
        actor_type="USER",
        event_type="NOTE_ADDED",
        entity_type="case",
        entity_id="case_001",
        payload={"note": "Review completed"},
        timestamp=now,
    )
    service_test_session.commit()

    # Genesis previous_hash must be 64 zeros
    assert ev1.previous_hash == "0" * 64
    # Second event must link to first event's signature
    assert ev2.previous_hash == ev1.event_hash
    # Third event must link to second event's signature
    assert ev3.previous_hash == ev2.event_hash

    # Verification must succeed
    verification = audit_service.verify_audit_chain(service_test_session)
    assert verification.is_valid is True
    assert verification.total_events == 3
    assert verification.verified_events == 3
    assert verification.tampered_at_id is None

    # Artificially tamper with ev2's payload in database
    ev2.payload = {"action": "HOLD", "risk_score": 0.99}  # Tampered!
    service_test_session.commit()

    tampered_verification = audit_service.verify_audit_chain(service_test_session)
    assert tampered_verification.is_valid is False
    assert tampered_verification.tampered_at_id == ev2.id
    assert "Payload tampering detected" in tampered_verification.verification_message


def test_decision_service_deterministic_vocabulary_and_persistence(
    service_test_session: Session,
) -> None:
    """Verify DecisionService adheres to ALLOW / REVIEW / HOLD and persists records."""
    decision_service = DecisionService()

    # Seed transaction in session
    now = datetime.now(UTC)
    cust = CustomerModel(id="cust_dec_1", created_at=now, city="Mumbai")
    merch = MerchantModel(
        id="m_dec_1",
        merchant_category="RETAIL",
        status="ACTIVE",
        created_at=now,
    )
    dev = DeviceModel(
        id="dev_dec_1",
        device_fingerprint="fp_dec_1",
        status="ACTIVE",
        first_seen=now,
        last_seen=now,
    )
    service_test_session.add_all([cust, merch, dev])

    tx = TransactionModel(
        id="tx_0001991",
        timestamp=now,
        amount=Decimal("12500.00"),
        currency="INR",
        payment_method="UPI",
        city="Mumbai",
        customer_id="cust_dec_1",
        merchant_id="m_dec_1",
        device_id="dev_dec_1",
        risk_score=0.20,
        risk_tier="LOW",
    )
    service_test_session.add(tx)
    service_test_session.commit()

    # Evaluate and persist
    decision = decision_service.evaluate_and_persist(
        service_test_session, transaction_id="tx_0001991"
    )
    service_test_session.commit()

    # Must be one of ALLOW, REVIEW, HOLD
    assert decision.action.value in {"ALLOW", "REVIEW", "HOLD"}

    # Must be retrievable from database
    persisted_dec = decision_service.get_decision(service_test_session, decision.decision_id)
    assert persisted_dec.id == decision.decision_id
    assert persisted_dec.action in {"ALLOW", "REVIEW", "HOLD"}


def test_transaction_service_and_entity_service(service_test_session: Session) -> None:
    """Verify TransactionService and EntityService retrieval and error handling."""
    tx_service = TransactionService()
    entity_service = EntityService()
    now = datetime.now(UTC)

    cust = CustomerModel(
        id="cust_srv_1",
        created_at=now,
        city="Bengaluru",
        risk_tier="LOW",
        account_age_days=60,
    )
    merch = MerchantModel(
        id="m_srv_1",
        merchant_category="GROCERY",
        status="ACTIVE",
        created_at=now,
    )
    tx = TransactionModel(
        id="tx_srv_001",
        timestamp=now,
        amount=Decimal("2500.00"),
        currency="INR",
        payment_method="CARD",
        city="Bengaluru",
        customer_id="cust_srv_1",
        merchant_id="m_srv_1",
        risk_score=0.18,
        risk_tier="LOW",
    )
    service_test_session.add_all([cust, merch, tx])
    service_test_session.commit()

    # Transaction retrieval
    tx_detail = tx_service.get_transaction(service_test_session, "tx_srv_001")
    assert tx_detail.customer_city == "Bengaluru"
    assert tx_detail.merchant_category == "GROCERY"

    # Customer profile
    cust_profile = entity_service.get_customer_profile(service_test_session, "cust_srv_1")
    assert cust_profile.city == "Bengaluru"
    assert cust_profile.total_transactions == 1

    # Missing entity error
    with pytest.raises(NotFoundDomainError):
        entity_service.get_customer_profile(service_test_session, "cust_ghost")


def test_model_service_registry(service_test_session: Session) -> None:
    """Verify ModelService active model lookup and version resolution."""
    model_service = ModelService()
    now = datetime.now(UTC)

    m = ModelRegistryModel(
        id="mdl_prod",
        model_name="LightGBM Production Risk",
        version="v1.0.0",
        model_type="lightgbm",
        status="ACTIVE",
        operating_threshold=0.37,
        feature_names=["amt", "velocity"],
        feature_count=2,
        artifact_path="ml/models/fraud_detection_model.joblib",
        created_at=now,
    )
    service_test_session.add(m)
    service_test_session.commit()

    active = model_service.get_active_model(service_test_session, "lightgbm")
    assert active.version == "v1.0.0"
    assert active.operating_threshold == 0.37

    with pytest.raises(NotFoundDomainError):
        model_service.get_model_by_version(service_test_session, "v999.0.0")
