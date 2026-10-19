"""Stable public model imports retained for existing application code."""

from core.models.affix import (
    AffixCategory,
    AffixDefinition,
    AffixGroup,
    AffixInstance,
    TierOption,
)
from core.models.base import BaseDefinition
from core.models.equipment import (
    MAX_ITEM_LEVEL,
    MIN_ITEM_LEVEL,
    SCHEMA_VERSION,
    EquipmentItem,
    new_equipment,
)

__all__ = [
    "AffixCategory",
    "AffixDefinition",
    "AffixGroup",
    "AffixInstance",
    "BaseDefinition",
    "EquipmentItem",
    "MAX_ITEM_LEVEL",
    "MIN_ITEM_LEVEL",
    "SCHEMA_VERSION",
    "TierOption",
    "new_equipment",
]
