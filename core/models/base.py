"""Equipment base definitions loaded from the local catalog."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
