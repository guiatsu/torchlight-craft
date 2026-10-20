"""Catalog search, filtering and selection state independent from Qt."""

from __future__ import annotations

from core.catalog import Catalog
from core.models import (
    AffixCategory,
    AffixDefinition,
    AffixGroup,
    AffixInstance,
    TierOption,
    resolve_tier_reference,
)


class AffixBrowser:
    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.group = AffixGroup.PREFIX
        self.category = AffixCategory.BASIC
        self.search_query = ""
        self.definition_id: str | None = None
        self.instance_id: str | None = None
        self.tier_id: str | None = None
        self.value = ""
        self.slot_index: int | None = None

    @property
    def definition(self) -> AffixDefinition | None:
        return self.catalog.affixes.get(self.definition_id) if self.definition_id else None

    @property
    def mode(self) -> str:
        if self.definition is None:
            return "none"
        if not self.instance_id:
            return "add"
        return "edit" if self.definition.id == self._original_definition_id else "replace"

    @property
    def _original_definition_id(self) -> str | None:
        return getattr(self, "_selected_original_definition_id", None)

    def definitions_for(self, base_id: str | None) -> list[AffixDefinition]:
        query = self.search_query.casefold().strip()
        return sorted(
            (
                definition
                for definition in self.catalog.affixes.values()
                if not definition.is_legacy_alias
                and definition.crafting_system_id in {"", "tlidb:standard-craft"}
                and base_id in definition.base_ids
                and definition.group == self.group
                and definition.category == self.category
                and (not query or query in definition.name.casefold())
            ),
            key=lambda definition: (definition.group.value, definition.category.value, definition.name),
        )

    def set_group(self, group: AffixGroup) -> None:
        self.group = group
        self.clear_selection()

    def set_category(self, category: AffixCategory) -> None:
        self.category = category
        # Keep the selected equipment slot/instance as the editing target while
        # the category tabs change which catalog definitions are displayed.
        self.definition_id = None
        self.tier_id = None
        self.value = ""

    def set_search(self, query: str) -> None:
        self.search_query = query[:100]

    def begin_add(self, group: AffixGroup, slot_index: int | None = None) -> None:
        self.group = group
        self.instance_id = None
        self.slot_index = slot_index
        self._selected_original_definition_id = None
        self.definition_id = None
        self.tier_id = None
        self.value = ""

    def select_definition(self, definition: AffixDefinition, item_level: int) -> None:
        self.group = definition.group
        self.category = definition.category
        self.definition_id = definition.id
        eligible = [
            tier for tier in definition.tiers
            if tier.item_level_required is None or item_level >= tier.item_level_required
        ]
        chosen = eligible[0] if eligible else (definition.tiers[0] if definition.tiers else None)
        self.tier_id = chosen.id if chosen else None
        self.value = chosen.value_range if chosen else ""

    def select_instance(self, instance: AffixInstance) -> None:
        self.group = instance.group
        self.category = instance.category
        self.instance_id = instance.id
        self._selected_original_definition_id = instance.definition_id
        self.definition_id = instance.definition_id
        self.tier_id = instance.tier_id
        self.value = instance.value
        self.slot_index = None

    def selected_tier(self) -> TierOption | None:
        definition = self.definition
        if not definition:
            return None
        tier, _ = resolve_tier_reference(definition.tiers, self.tier_id or "")
        return tier

    def selected_tier_is_ambiguous(self) -> bool:
        definition = self.definition
        if not definition:
            return False
        _, ambiguous = resolve_tier_reference(definition.tiers, self.tier_id or "")
        return ambiguous

    def set_tier(self, tier_id: str, item_level: int) -> TierOption | None:
        definition = self.definition
        tier = next((option for option in definition.tiers if option.id == tier_id), None) if definition else None
        if not tier or (tier.item_level_required is not None and item_level < tier.item_level_required):
            return None
        self.tier_id = tier.id
        self.value = tier.value_range
        return tier

    def clear_selection(self) -> None:
        self.instance_id = None
        self.slot_index = None
        self._selected_original_definition_id = None
        self.definition_id = None
        self.tier_id = None
        self.value = ""
