"""Typed models for editable Torchlight equipment."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 1
MIN_ITEM_LEVEL = 1
MAX_ITEM_LEVEL = 100


class AffixGroup(StrEnum):
    PREFIX = "prefix"
    SUFFIX = "suffix"


class AffixCategory(StrEnum):
    BASIC = "Basic"
    ADVANCED = "Advanced"
    ULTIMATE = "Ultimate"


@dataclass(frozen=True, slots=True)
class TierOption:
    id: str
    item_level_required: int | None
    value_range: str
    verification_status: str = "community_reference_season_unverified"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TierOption":
        return cls(
            id=str(data["id"]),
            item_level_required=(
                int(data["item_level_required"])
                if data.get("item_level_required") is not None
                else None
            ),
            value_range=str(data["value_range"]),
            verification_status=str(
                data.get("verification_status", "community_reference_season_unverified")
            ),
        )


@dataclass(frozen=True, slots=True)
class BaseDefinition:
    id: str
    name: str
    category: str
    subcategory: str
    equipment_type: str
    hands: int | None
    character_level_requirement: int | None
    minimum_item_level: int | None
    prefix_limit: int | None
    suffix_limit: int | None
    limit_status: str
    restrictions: tuple[str, ...] = ()
    source_id: str = ""
    verification_status: str = "community_reference_season_unverified"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseDefinition":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            category=str(data["category"]),
            subcategory=str(data["subcategory"]),
            equipment_type=str(data["equipment_type"]),
            hands=int(data["hands"]) if data.get("hands") is not None else None,
            character_level_requirement=(
                int(data["character_level_requirement"])
                if data.get("character_level_requirement") is not None
                else None
            ),
            minimum_item_level=(
                int(data["minimum_item_level"])
                if data.get("minimum_item_level") is not None
                else None
            ),
            prefix_limit=(
                int(data["prefix_limit"]) if data.get("prefix_limit") is not None else None
            ),
            suffix_limit=(
                int(data["suffix_limit"]) if data.get("suffix_limit") is not None else None
            ),
            limit_status=str(data.get("limit_status", "unknown")),
            restrictions=tuple(str(value) for value in data.get("restrictions", [])),
            source_id=str(data.get("source_id", "")),
            verification_status=str(
                data.get("verification_status", "community_reference_season_unverified")
            ),
        )


@dataclass(frozen=True, slots=True)
class AffixDefinition:
    id: str
    name: str
    group: AffixGroup
    category: AffixCategory
    base_ids: tuple[str, ...]
    tiers: tuple[TierOption, ...]
    value_editable: bool
    source_id: str
    verification_status: str = "community_reference_season_unverified"
    compatibility_status: str = "provisional"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AffixDefinition":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            group=AffixGroup(str(data["group"])),
            category=AffixCategory(str(data["category"])),
            base_ids=tuple(str(value) for value in data.get("base_ids", [])),
            tiers=tuple(TierOption.from_dict(value) for value in data.get("tiers", [])),
            value_editable=bool(data.get("value_editable", True)),
            source_id=str(data.get("source_id", "")),
            verification_status=str(
                data.get("verification_status", "community_reference_season_unverified")
            ),
            compatibility_status=str(data.get("compatibility_status", "provisional")),
        )


@dataclass(slots=True)
class AffixInstance:
    id: str
    definition_id: str
    group: AffixGroup
    category: AffixCategory
    tier_id: str
    value: str
    verification_status: str = "community_reference_season_unverified"

    @classmethod
    def create(
        cls,
        definition: AffixDefinition,
        tier: TierOption,
        value: str | None = None,
    ) -> "AffixInstance":
        return cls(
            id=f"affix-{uuid4().hex}",
            definition_id=definition.id,
            group=definition.group,
            category=definition.category,
            tier_id=tier.id,
            value=value if value is not None else tier.value_range,
            verification_status=definition.verification_status,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AffixInstance":
        if not isinstance(data, dict):
            raise TypeError("Affix records must be objects.")
        for key in ("id", "definition_id", "group", "category", "tier_id"):
            if not isinstance(data.get(key), str):
                raise TypeError(f"Affix field {key!r} must be text.")
        if not isinstance(data.get("value", ""), str):
            raise TypeError("Affix value must be text.")
        return cls(
            id=data["id"],
            definition_id=data["definition_id"],
            group=AffixGroup(data["group"]),
            category=AffixCategory(data["category"]),
            tier_id=data["tier_id"],
            value=data.get("value", ""),
            verification_status=str(
                data.get("verification_status", "community_reference_season_unverified")
            ),
        )


@dataclass(slots=True)
class EquipmentItem:
    id: str = field(default_factory=lambda: f"item-{uuid4().hex}")
    name: str = "New Equipment"
    base_id: str = "sleeping-sages-cane"
    item_level: int = 86
    priceless: bool = False
    rarity: str | None = None
    affixes: list[AffixInstance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["affixes"] = [asdict(affix) for affix in self.affixes]
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EquipmentItem":
        if not isinstance(data, dict):
            raise TypeError("Equipment records must be objects.")
        if not isinstance(data.get("id"), str) or not isinstance(data.get("base_id"), str):
            raise TypeError("Equipment ID and base ID must be text.")
        if not isinstance(data.get("name", "New Equipment"), str):
            raise TypeError("Equipment name must be text.")
        if isinstance(data.get("item_level"), bool) or not isinstance(data.get("item_level"), int):
            raise TypeError("Item Level must be an integer.")
        if not isinstance(data.get("priceless", False), bool):
            raise TypeError("Priceless state must be true or false.")
        if data.get("rarity") is not None and not isinstance(data.get("rarity"), str):
            raise TypeError("Rarity must be text or null.")
        if not isinstance(data.get("affixes", []), list):
            raise TypeError("Affixes must be a list.")
        return cls(
            id=data["id"],
            name=data.get("name", "New Equipment"),
            base_id=data["base_id"],
            item_level=data["item_level"],
            priceless=data.get("priceless", False),
            rarity=data.get("rarity"),
            affixes=[AffixInstance.from_dict(affix) for affix in data.get("affixes", [])],
        )


def new_equipment(base_id: str = "sleeping-sages-cane") -> EquipmentItem:
    return EquipmentItem(base_id=base_id)
