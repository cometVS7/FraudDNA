"""FraudDNA Audit Trail Application Service.

Provides append-only, tamper-evident cryptographic audit logging and chain verification.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError
from app.models.domain import AuditEventModel
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditChainVerifyResponse, AuditEventListResponse, AuditEventResponse

logger = logging.getLogger(__name__)

GENESIS_PREVIOUS_HASH = "0" * 64
_audit_counter: int = 0


def normalize_timestamp(dt: datetime) -> str:
    """Normalize datetime into standard UTC ISO 8601 string for deterministic hashing."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    utc_dt = dt.astimezone(UTC)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class AuditService:
    """Coordinates tamper-evident audit logging and verification."""

    def __init__(self, audit_repo: AuditRepository | None = None) -> None:
        self.repo = audit_repo or AuditRepository()

    def record_event(
        self,
        session: Session,
        actor: str,
        actor_type: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        payload: dict[str, Any],
        timestamp: datetime | None = None,
    ) -> AuditEventModel:
        """Append an immutable, cryptographically chained audit event to the ledger."""
        event_ts = timestamp or datetime.now(UTC)
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        # Retrieve current chain tip for previous_hash
        latest = self.repo.get_latest_event(session)
        previous_hash = latest.event_hash if latest else GENESIS_PREVIOUS_HASH

        # Calculate deterministic event_hash
        ts_str = normalize_timestamp(event_ts)
        raw_signature = (
            f"{ts_str}:{actor}:{event_type}:{entity_type}:"
            f"{entity_id}:{payload_hash}:{previous_hash}"
        )
        event_hash = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()

        global _audit_counter
        _audit_counter = (_audit_counter + 1) % 1000000
        event_id = (
            f"aud_{int(event_ts.timestamp() * 1000):013d}_{_audit_counter:06d}_{event_hash[:8]}"
        )

        audit_event = AuditEventModel(
            id=event_id,
            timestamp=event_ts,
            actor=actor,
            actor_type=actor_type,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_hash=payload_hash,
            previous_hash=previous_hash,
            event_hash=event_hash,
            payload=payload,
        )

        return self.repo.create(session, audit_event)

    def get_event(self, session: Session, event_id: str) -> AuditEventResponse:
        """Retrieve a specific audit event by ID or raise NotFoundDomainError."""
        event = self.repo.get_by_id(session, event_id)
        if not event:
            raise NotFoundDomainError(
                f"Audit event '{event_id}' not found.",
                details={"event_id": event_id},
            )
        return AuditEventResponse.model_validate(event)

    def list_events(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
        entity_type: str | None = None,
        entity_id: str | None = None,
        event_type: str | None = None,
        actor: str | None = None,
    ) -> AuditEventListResponse:
        """Query bounded, filtered audit records."""
        items, total = self.repo.list_events(
            session=session,
            limit=limit,
            offset=offset,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor=actor,
        )
        responses = [AuditEventResponse.model_validate(item) for item in items]
        return AuditEventListResponse(
            items=responses,
            total_count=total,
            limit=limit,
            offset=offset,
        )

    def verify_audit_chain(self, session: Session) -> AuditChainVerifyResponse:
        """Cryptographically verify the entire historical audit hash chain."""
        events = self.repo.get_all_ordered_ascending(session)
        total = len(events)
        if total == 0:
            return AuditChainVerifyResponse(
                is_valid=True,
                total_events=0,
                verified_events=0,
                verification_message="Audit log is empty; chain is valid by definition.",
            )

        expected_prev = GENESIS_PREVIOUS_HASH
        for idx, event in enumerate(events):
            # 1. Verify previous_hash linkage
            if (idx == 0 and event.previous_hash != GENESIS_PREVIOUS_HASH) or (
                idx > 0 and event.previous_hash != expected_prev
            ):
                return AuditChainVerifyResponse(
                    is_valid=False,
                    total_events=total,
                    verified_events=idx,
                    tampered_at_id=event.id,
                    verification_message=(
                        f"Previous hash broken at event '{event.id}' (index {idx}). "
                        f"Expected {expected_prev}, found {event.previous_hash}."
                    ),
                )

            # 2. Verify payload hash integrity
            payload_str = json.dumps(event.payload, sort_keys=True, default=str)
            computed_payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
            if computed_payload_hash != event.payload_hash:
                return AuditChainVerifyResponse(
                    is_valid=False,
                    total_events=total,
                    verified_events=idx,
                    tampered_at_id=event.id,
                    verification_message=(
                        f"Payload tampering detected at event '{event.id}' (index {idx}). "
                        f"Expected payload hash {event.payload_hash}, computed {computed_payload_hash}."
                    ),
                )

            # 3. Verify event signature hash
            ts_str = normalize_timestamp(event.timestamp)
            raw_signature = (
                f"{ts_str}:{event.actor}:{event.event_type}:"
                f"{event.entity_type}:{event.entity_id}:{event.payload_hash}:{event.previous_hash}"
            )
            computed_event_hash = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()
            if computed_event_hash != event.event_hash:
                return AuditChainVerifyResponse(
                    is_valid=False,
                    total_events=total,
                    verified_events=idx,
                    tampered_at_id=event.id,
                    verification_message=(
                        f"Signature mismatch at event '{event.id}' (index {idx}). "
                        f"Stored {event.event_hash}, computed {computed_event_hash}."
                    ),
                )

            expected_prev = event.event_hash

        return AuditChainVerifyResponse(
            is_valid=True,
            total_events=total,
            verified_events=total,
            verification_message="Cryptographic audit chain fully verified; 0 tampering detected.",
        )


_audit_service_instance: AuditService | None = None


def get_audit_service() -> AuditService:
    """Dependency provider for AuditService."""
    global _audit_service_instance
    if _audit_service_instance is None:
        _audit_service_instance = AuditService()
    return _audit_service_instance
