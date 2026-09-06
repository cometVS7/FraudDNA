"""FraudDNA Audit Trail Endpoints.

GET /api/v1/audit              - Query paginated audit events
GET /api/v1/audit/{event_id}   - Retrieve single audit event
GET /api/v1/audit/verify/chain - Verify cryptographic SHA-256 hash chain
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.schemas.audit import AuditChainVerifyResponse, AuditEventListResponse, AuditEventResponse
from app.services.audit import AuditService, get_audit_service

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get(
    "",
    response_model=AuditEventListResponse,
    summary="List Audit Events",
    description="Query bounded, filtered immutable audit events.",
)
def list_audit_events(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    entity_type: Annotated[str | None, Query()] = None,
    entity_id: Annotated[str | None, Query()] = None,
    event_type: Annotated[str | None, Query()] = None,
    actor: Annotated[str | None, Query()] = None,
    db: Session = Depends(get_sync_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditEventListResponse:
    """Retrieve audit log items."""
    return audit_service.list_events(
        session=db,
        limit=limit,
        offset=offset,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        actor=actor,
    )


@router.get(
    "/verify/chain",
    response_model=AuditChainVerifyResponse,
    summary="Verify Audit Chain Integrity",
    description="Cryptographically verifies every block signature and previous-hash linkage in the audit ledger.",
)
def verify_audit_chain(
    db: Session = Depends(get_sync_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditChainVerifyResponse:
    """Verify cryptographic audit chain."""
    return audit_service.verify_audit_chain(session=db)


@router.get(
    "/{event_id}",
    response_model=AuditEventResponse,
    summary="Get Audit Event",
    description="Retrieve single audit event by primary ID.",
)
def get_audit_event(
    event_id: str,
    db: Session = Depends(get_sync_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditEventResponse:
    """Retrieve audit event detail."""
    return audit_service.get_event(session=db, event_id=event_id)
