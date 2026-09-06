"""FraudDNA Entity Intelligence Endpoints.

GET /api/v1/entities/{entity_type}/{entity_id} - Retrieve entity profile
GET /api/v1/entities/{entity_type}/{entity_id}/transactions - Bounded entity transactions
GET /api/v1/entities/{entity_type}/{entity_id}/relationships - Direct semantic relationships
GET /api/v1/entities/{entity_type}/{entity_id}/graph - Database-backed React Flow neighborhood
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.core.errors import ValidationDomainError
from app.schemas.entity import (
    EntityRelationshipsResponse,
    EntityTransactionsResponse,
    EntityType,
)
from app.schemas.graph import GraphData
from app.services.entity import EntityService, get_entity_service

router = APIRouter(prefix="/entities", tags=["Entities"])


@router.get(
    "/{entity_type}/{entity_id}",
    summary="Get Entity Profile",
    description="Retrieve entity profile, risk aggregation, and behavioral velocity metrics.",
)
def get_entity_profile(
    entity_type: EntityType,
    entity_id: str,
    as_of: Annotated[
        datetime | None,
        Query(description="Point-in-time evaluation timestamp (UTC) to prevent future leakage"),
    ] = None,
    db: Session = Depends(get_sync_db),
    entity_service: EntityService = Depends(get_entity_service),
) -> dict[str, Any]:
    """Retrieve profile for requested entity type and identifier."""
    if entity_type == EntityType.CUSTOMER:
        return entity_service.get_customer_profile(db, entity_id, as_of=as_of).model_dump()
    elif entity_type == EntityType.ACCOUNT:
        return entity_service.get_account_profile(db, entity_id, as_of=as_of).model_dump()
    elif entity_type == EntityType.DEVICE:
        return entity_service.get_device_profile(db, entity_id, as_of=as_of).model_dump()
    elif entity_type == EntityType.IP:
        return entity_service.get_ip_profile(db, entity_id, as_of=as_of).model_dump()
    elif entity_type == EntityType.CARD:
        return entity_service.get_card_profile(db, entity_id, as_of=as_of).model_dump()
    elif entity_type == EntityType.MERCHANT:
        return entity_service.get_merchant_profile(db, entity_id, as_of=as_of).model_dump()
    else:
        raise ValidationDomainError(
            f"Unsupported entity type for direct profile lookup: '{entity_type.value}'",
            details={"entity_type": entity_type.value},
        )


@router.get(
    "/{entity_type}/{entity_id}/transactions",
    response_model=EntityTransactionsResponse,
    summary="Get Entity Transactions",
    description="Retrieve bounded, paginated transactions for a specific entity.",
)
def get_entity_transactions(
    entity_type: EntityType,
    entity_id: str,
    limit: Annotated[int, Query(ge=1, le=250, description="Page size limit")] = 50,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    as_of: Annotated[
        datetime | None,
        Query(description="Point-in-time evaluation timestamp (UTC)"),
    ] = None,
    db: Session = Depends(get_sync_db),
    entity_service: EntityService = Depends(get_entity_service),
) -> EntityTransactionsResponse:
    """Retrieve paginated transactions belonging to the entity."""
    return entity_service.get_entity_transactions(
        session=db,
        entity_type=entity_type.value,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
        as_of=as_of,
    )


@router.get(
    "/{entity_type}/{entity_id}/relationships",
    response_model=EntityRelationshipsResponse,
    summary="Get Entity Relationships",
    description="Retrieve direct typed semantic relationships connected to an entity.",
)
def get_entity_relationships(
    entity_type: EntityType,
    entity_id: str,
    limit: Annotated[int, Query(ge=1, le=200, description="Max relationships")] = 100,
    db: Session = Depends(get_sync_db),
    entity_service: EntityService = Depends(get_entity_service),
) -> EntityRelationshipsResponse:
    """Retrieve typed relationships for the entity."""
    return entity_service.get_entity_relationships(
        session=db,
        entity_type=entity_type.value,
        entity_id=entity_id,
        limit=limit,
    )


@router.get(
    "/{entity_type}/{entity_id}/graph",
    response_model=GraphData,
    summary="Get Entity Neighborhood Graph",
    description="Retrieve bounded, deterministic React Flow graph data directly from PostgreSQL.",
)
def get_entity_graph(
    entity_type: EntityType,
    entity_id: str,
    depth: Annotated[int, Query(ge=1, le=2, description="Traversal depth (1 or 2)")] = 1,
    max_nodes: Annotated[int, Query(ge=5, le=250, description="Maximum nodes in graph")] = 100,
    max_transactions: Annotated[
        int, Query(ge=5, le=250, description="Maximum transactions to traverse")
    ] = 100,
    db: Session = Depends(get_sync_db),
    entity_service: EntityService = Depends(get_entity_service),
) -> GraphData:
    """Retrieve bounded ego-graph around the entity."""
    return entity_service.get_entity_neighborhood_graph(
        session=db,
        entity_type=entity_type.value,
        entity_id=entity_id,
        depth=depth,
        max_nodes=max_nodes,
        max_transactions=max_transactions,
    )
