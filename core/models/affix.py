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
    tier_label: str = ""
    verification_status: str = "community_reference_season_unverified"
    requirement_level_raw: str | None = None
    weight_raw: str | None = None
    weight_parse_status: str = "missing"
    library: str = ""
    source_url: str = ""
    source_section: str = ""
    source_table: str = ""
    source_row_key: str = ""

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
            tier_label=str(data.get("tier_label", data["id"])),
            verification_status=str(
                data.get("verification_status", "community_reference_season_unverified")
            ),
            requirement_level_raw=(
                str(data["requirement_level_raw"])
                if data.get("requirement_level_raw") is not None
                else None
            ),
            weight_raw=(str(data["weight_raw"]) if data.get("weight_raw") is not None else None),
            weight_parse_status=str(data.get("weight_parse_status", "missing")),
            library=str(data.get("library", "")),
            source_url=str(data.get("source_url", "")),
            source_section=str(data.get("source_section", "")),
            source_table=str(data.get("source_table", "")),
            source_row_key=str(data.get("source_row_key", "")),
        )


def resolve_tier_reference(
    tiers: tuple[TierOption, ...], stored_id: str
) -> tuple[TierOption | None, bool]:
    """Resolve stable IDs, or an old visual label only when it is unique."""
    exact = next((tier for tier in tiers if tier.id == stored_id), None)
    if exact is not None:
        return exact, False
    legacy_matches = [tier for tier in tiers if tier.tier_label == stored_id]
    if len(legacy_matches) == 1:
        return legacy_matches[0], False
    return None, len(legacy_matches) > 1


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
    source_url: str = ""
    source_section: str = ""
    source_family_id: str = ""
    family_grouping_status: str = "unknown"
    crafting_system_id: str = ""
    is_legacy_alias: bool = False
    legacy_family_member_ids: tuple[str, ...] = ()

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
            source_url=str(data.get("source_url", "")),
            source_section=str(data.get("source_section", "")),
            source_family_id=str(data.get("source_family_id", "")),
            family_grouping_status=str(data.get("family_grouping_status", "unknown")),
            crafting_system_id=str(data.get("crafting_system_id", "")),
            is_legacy_alias=bool(data.get("is_legacy_alias", False)),
            legacy_family_member_ids=tuple(
                str(value) for value in data.get("legacy_family_member_ids", [])
            ),
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
