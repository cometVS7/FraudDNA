"""FraudDNA Entity Intelligence Endpoints.

GET /api/v1/entities/{entity_type}/{entity_id} - Retrieve entity profile
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.core.errors import ValidationDomainError
from app.schemas.entity import EntityType
from app.services.entity import EntityService, get_entity_service

router = APIRouter(prefix="/entities", tags=["Entities"])


@router.get(
    "/{entity_type}/{entity_id}",
    summary="Get Entity Profile",
    description="Retrieve entity profile and risk indicators for customer, device, ip, card, or merchant.",
)
def get_entity_profile(
    entity_type: EntityType,
    entity_id: str,
    db: Session = Depends(get_sync_db),
    entity_service: EntityService = Depends(get_entity_service),
) -> dict[str, Any]:
    """Retrieve profile for requested entity type and identifier."""
    if entity_type == EntityType.CUSTOMER:
        return entity_service.get_customer_profile(db, entity_id).model_dump()
    elif entity_type == EntityType.DEVICE:
        return entity_service.get_device_profile(db, entity_id).model_dump()
    elif entity_type == EntityType.IP:
        return entity_service.get_ip_profile(db, entity_id).model_dump()
    elif entity_type == EntityType.CARD:
        return entity_service.get_card_profile(db, entity_id).model_dump()
    elif entity_type == EntityType.MERCHANT:
        return entity_service.get_merchant_profile(db, entity_id).model_dump()
    else:
        raise ValidationDomainError(
            f"Unsupported entity type for direct profile lookup: '{entity_type.value}'",
            details={"entity_type": entity_type.value},
        )
