"""FraudDNA Graph Entity and Relationship Types.

Defines stable entity types, edge relationships, and namespacing utilities.
"""

from enum import StrEnum


class EntityType(StrEnum):
    """Namespaced entity types in the FraudDNA relationship graph."""

    CUSTOMER = "customer"
    TRANSACTION = "transaction"
    DEVICE = "device"
    IP = "ip"
    CARD = "card"
    MERCHANT = "merchant"


class EdgeRelation(StrEnum):
    """Semantic relationship types connecting nodes in the FraudDNA graph."""

    EXECUTED = "EXECUTED"  # Customer -> Transaction
    ON_DEVICE = "ON_DEVICE"  # Transaction -> Device
    FROM_IP = "FROM_IP"  # Transaction -> IP
    USING_CARD = "USING_CARD"  # Transaction -> Card
    AT_MERCHANT = "AT_MERCHANT"  # Transaction -> Merchant
    SHARED_INFRASTRUCTURE = "SHARED_INFRASTRUCTURE"  # Direct shared entity relation


def make_node_id(entity_type: EntityType | str, raw_id: str) -> str:
    """Create a stable namespaced node identifier (e.g., 'customer:cust_00001')."""
    type_str = (
        entity_type.value if isinstance(entity_type, EntityType) else str(entity_type).lower()
    )
    raw_str = str(raw_id).strip()
    return f"{type_str}:{raw_str}"


def parse_node_id(node_id: str) -> tuple[str, str]:
    """Parse a namespaced node identifier into (entity_type, raw_id)."""
    if ":" not in node_id:
        raise ValueError(f"Invalid namespaced node ID: {node_id}")
    prefix, _, raw_id = node_id.partition(":")
    return prefix.lower(), raw_id
