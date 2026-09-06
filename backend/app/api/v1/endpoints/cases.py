"""FraudDNA Case Management Endpoints.

POST /api/v1/cases               - Create an operational case
GET  /api/v1/cases               - List cases (paginated & filtered)
GET  /api/v1/cases/{case_id}     - Get case details
PATCH /api/v1/cases/{case_id}/status - Update case state machine
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.schemas.case import (
    CaseCreateRequest,
    CaseListResponse,
    CasePriority,
    CaseResponse,
    CaseStatus,
    CaseStatusUpdateRequest,
)
from app.services.case import CaseService, get_case_service

router = APIRouter(prefix="/cases", tags=["Case Management"])


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Case",
    description="Create a new operational case, optionally linking an investigation.",
)
def create_case(
    request: CaseCreateRequest,
    db: Session = Depends(get_sync_db),
    case_service: CaseService = Depends(get_case_service),
) -> CaseResponse:
    """Create an operational case with initial triage status NEW."""
    return case_service.create_case(session=db, request=request)


@router.get(
    "",
    response_model=CaseListResponse,
    summary="List Cases",
    description="Query bounded collection of operational cases.",
)
def list_cases(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: CaseStatus | None = None,
    priority: CasePriority | None = None,
    owner: Annotated[str | None, Query()] = None,
    db: Session = Depends(get_sync_db),
    case_service: CaseService = Depends(get_case_service),
) -> CaseListResponse:
    """Retrieve filtered, paginated case items."""
    return case_service.list_cases(
        session=db,
        limit=limit,
        offset=offset,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        owner=owner,
    )


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Get Case",
    description="Retrieve case details by primary ID.",
)
def get_case(
    case_id: str,
    db: Session = Depends(get_sync_db),
    case_service: CaseService = Depends(get_case_service),
) -> CaseResponse:
    """Retrieve single case record with linked investigation IDs."""
    return case_service.get_case(session=db, case_id=case_id)


@router.patch(
    "/{case_id}/status",
    response_model=CaseResponse,
    summary="Update Case Status",
    description="Transition case to a new operational status, enforcing state machine validation.",
)
def update_case_status(
    case_id: str,
    request: CaseStatusUpdateRequest,
    db: Session = Depends(get_sync_db),
    case_service: CaseService = Depends(get_case_service),
) -> CaseResponse:
    """Transition case status and record audit log."""
    return case_service.update_case_status(session=db, case_id=case_id, request=request)
