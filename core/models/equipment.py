"""User-owned equipment records and schema constants."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from core.models.affix import AffixInstance

SCHEMA_VERSION = 1
MIN_ITEM_LEVEL = 1
MAX_ITEM_LEVEL = 100


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
