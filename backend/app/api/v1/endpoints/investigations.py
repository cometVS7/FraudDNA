import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_sync_db
from app.schemas.investigation import InvestigationRequest, InvestigationResponse
from app.services.investigation import (
    InvestigationService,
    TransactionNotFoundError,
    get_investigation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Risk Investigation",
    description=(
        "Executes a deterministic risk investigation for a given transaction ID, "
        "orchestrating ML risk scoring, Tree SHAP XAI factor attribution, FraudDNA "
        "graph neighborhood analysis, cluster lookup, and evidence synthesis."
    ),
)
def create_investigation(
    payload: InvestigationRequest,
    service: InvestigationService = Depends(get_investigation_service),
    db: Session = Depends(get_sync_db),
) -> InvestigationResponse:
    """Trigger a new structured risk investigation for a transaction."""
    try:
        if settings.ENABLE_PERSISTENT_STORAGE:
            return service.investigate_and_persist(
                session=db, transaction_id=payload.transaction_id
            )
        return service.investigate(transaction_id=payload.transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{exc.transaction_id}' not found in dataset or graph.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation failed unexpectedly: {str(exc)}",
        ) from exc


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Investigation by ID",
    description="Retrieves a previously computed risk investigation by its deterministic ID.",
)
def get_investigation(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
    db: Session = Depends(get_sync_db),
) -> InvestigationResponse:
    """Retrieve an existing investigation result."""
    result = service.get_investigation_by_id(investigation_id)
    if result is None and settings.ENABLE_PERSISTENT_STORAGE:
        try:
            persisted = service.get_persisted_investigation(db, investigation_id)
            if not persisted and not investigation_id.startswith("inv_"):
                persisted = service.get_persisted_investigation(db, f"inv_{investigation_id}")
            if persisted is not None:
                return service.investigate(persisted.primary_transaction_id)
        except Exception as exc:
            logger.warning(f"Persisted investigation lookup failed: {exc}")

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return result
