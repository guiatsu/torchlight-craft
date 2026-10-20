"""Qt-independent use cases for the single equipment currently being edited."""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy

from core.catalog import Catalog
from core.models import (
    MAX_ITEM_LEVEL,
    MIN_ITEM_LEVEL,
    AffixDefinition,
    AffixGroup,
    AffixInstance,
    BaseDefinition,
    EquipmentItem,
    TierOption,
    new_equipment,
    resolve_tier_reference,
)
from core.validation import validate_item


class ItemEditError(ValueError):
    """An edit could not be applied without violating known catalog rules."""


@dataclass(frozen=True, slots=True)
class IncompatibleAffix:
    instance: AffixInstance
    name: str
    reason: str


class ItemEditorService:
    """Owns one mutable item instance; presentation layers only reference it."""

    def __init__(self, catalog: Catalog, item: EquipmentItem | None = None) -> None:
        self.catalog = catalog
        self._item = item or new_equipment()
        self._baseline = deepcopy(self._item.to_dict())

    @property
    def item(self) -> EquipmentItem:
        return self._item

    def replace_item(self, item: EquipmentItem, *, clean: bool = True) -> None:
        self._item = item
        self._baseline = deepcopy(item.to_dict()) if clean else {}

    @property
    def is_dirty(self) -> bool:
        return self._item.to_dict() != self._baseline

    def mark_saved(self) -> None:
        self._baseline = deepcopy(self._item.to_dict())

    def rename_baseline(self, name: str) -> None:
        if "name" in self._baseline:
            self._baseline["name"] = name

    def mark_deleted_from_library(self) -> None:
        self._baseline = {}

    def set_name(self, name: str) -> None:
        self._item.name = name[:80]

    def set_item_level(self, level: int) -> None:
        if isinstance(level, bool) or not MIN_ITEM_LEVEL <= level <= MAX_ITEM_LEVEL:
            raise ItemEditError(f"Item Level must be between {MIN_ITEM_LEVEL} and {MAX_ITEM_LEVEL}.")
        self._item.item_level = level

    def set_priceless(self, priceless: bool) -> None:
        self._item.priceless = priceless

    def change_base(self, base_id: str) -> list[IncompatibleAffix]:
        base = self.catalog.bases.get(base_id)
        if base is None:
            raise ItemEditError("The selected equipment base is not in the local catalog.")
        if base.id == self._item.base_id:
            return self.incompatible_affixes()
        previous = self.catalog.bases.get(self._item.base_id)
        if previous and self._item.name == previous.name:
            self._item.name = base.name
        self._item.base_id = base.id
        return self.incompatible_affixes()

    def incompatible_affixes(self) -> list[IncompatibleAffix]:
        base = self.catalog.bases.get(self._item.base_id)
        if base is None:
            return []
        results = []
        for instance in self._item.affixes:
            definition = self.catalog.affixes.get(instance.definition_id)
            if definition and definition.base_ids and base.id not in definition.base_ids:
                results.append(
                    IncompatibleAffix(
                        instance=instance,
                        name=definition.name,
                        reason=f"Not listed for {base.name}",
                    )
                )
        return results

    def remove_incompatible_affixes(self, instance_ids: set[str]) -> int:
        incompatible_ids = {entry.instance.id for entry in self.incompatible_affixes()}
        requested = incompatible_ids.intersection(instance_ids)
        if not requested:
            return 0
        before = len(self._item.affixes)
        self._item.affixes = [affix for affix in self._item.affixes if affix.id not in requested]
        return before - len(self._item.affixes)

    def validation_errors(self) -> list[str]:
        return validate_item(self._item, self.catalog.bases, self.catalog.affixes)

    def _definition_is_already_present(
        self, definition: AffixDefinition, *, excluding: str | None = None
    ) -> bool:
        for instance in self._item.affixes:
            if instance.id == excluding:
                continue
            if instance.definition_id == definition.id:
                return True
            old_definition = self.catalog.affixes.get(instance.definition_id)
            if (
                old_definition is None
                or not old_definition.is_legacy_alias
                or definition.id not in old_definition.legacy_family_member_ids
            ):
                continue
            old_tier, ambiguous = resolve_tier_reference(old_definition.tiers, instance.tier_id)
            if ambiguous:
                return True
            if old_tier and any(tier.id == old_tier.id for tier in definition.tiers):
                return True
        return False

    def add_or_update_affix(
        self,
        definition: AffixDefinition,
        tier: TierOption,
        value: str,
        *,
        instance_id: str | None = None,
        slot_index: int | None = None,
    ) -> AffixInstance:
        base = self.catalog.bases.get(self._item.base_id)
        if base is None:
            raise ItemEditError("The selected equipment base is not in the local catalog.")
        if definition.id not in self.catalog.affixes:
            raise ItemEditError("Choose an available affix and tier first.")
        if definition.base_ids and base.id not in definition.base_ids:
            raise ItemEditError("This affix is not listed for the selected base.")
        if tier not in definition.tiers:
            raise ItemEditError("Choose an available affix and tier first.")
        if tier.item_level_required is not None and self._item.item_level < tier.item_level_required:
            raise ItemEditError(
                f"{tier.tier_label} requires Item Level {tier.item_level_required} in the current catalog."
            )
        clean_value = value.strip()
        if not clean_value:
            raise ItemEditError("Enter a value for this affix.")
        if len(clean_value) > 120:
            raise ItemEditError("Affix values must be 120 characters or fewer.")

        target = next((a for a in self._item.affixes if a.id == instance_id), None)
        if instance_id and target is None:
            raise ItemEditError("Select an affix on the item to edit it.")
        unresolved = {entry.instance.id for entry in self.incompatible_affixes()}
        if unresolved - ({instance_id} if instance_id else set()):
            raise ItemEditError(
                "Resolve the other incompatible affixes before adding or replacing an affix."
            )
        if self._definition_is_already_present(definition, excluding=instance_id):
            raise ItemEditError(f"{definition.name} is already on this equipment.")

        if target:
            if target.group != definition.group:
                self._check_group_capacity(base, definition.group)
            target.definition_id = definition.id
            target.group = definition.group
            target.category = definition.category
            target.tier_id = tier.id
            target.value = clean_value
            target.verification_status = definition.verification_status
            return target

        self._check_group_capacity(base, definition.group)
        instance = AffixInstance.create(definition, tier, clean_value)
        self._insert_instance(instance, slot_index)
        return instance

    def remove_affix(self, instance_id: str) -> bool:
        before = len(self._item.affixes)
        self._item.affixes = [a for a in self._item.affixes if a.id != instance_id]
        return len(self._item.affixes) != before

    def _check_group_capacity(self, base: BaseDefinition, group: AffixGroup) -> None:
        limit = base.prefix_limit if group == AffixGroup.PREFIX else base.suffix_limit
        count = sum(1 for item_affix in self._item.affixes if item_affix.group == group)
        if limit is not None and count >= limit:
            raise ItemEditError(
                f"This base's catalog-listed {group.value} limit is {limit}."
            )

    def _insert_instance(self, instance: AffixInstance, slot_index: int | None) -> None:
        if slot_index is None:
            self._item.affixes.append(instance)
            return
        group_indices = [
            index for index, existing in enumerate(self._item.affixes)
            if existing.group == instance.group
        ]
        if slot_index < len(group_indices):
            self._item.affixes.insert(group_indices[slot_index], instance)
        else:
            self._item.affixes.append(instance)

    def slots(self, group: AffixGroup) -> list[dict[str, object]]:
        occupied = [affix for affix in self._item.affixes if affix.group == group]
        base = self.catalog.bases.get(self._item.base_id)
        limit = None
        if base:
            limit = base.prefix_limit if group == AffixGroup.PREFIX else base.suffix_limit
        result: list[dict[str, object]] = [
            {"kind": "affix", "index": index, "instanceId": affix.id}
            for index, affix in enumerate(occupied)
        ]
        if limit is not None:
            result.extend(
                {"kind": "empty", "index": index, "instanceId": ""}
                for index in range(len(occupied), limit)
            )
        return result
