"""Catalog affix models and editable affix instances."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4


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
