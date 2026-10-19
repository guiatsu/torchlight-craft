"""QML-facing equipment state and configuration actions."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from core.models import AffixGroup, BaseDefinition, MIN_ITEM_LEVEL, MAX_ITEM_LEVEL
from services.item_editor_service import ItemEditorService


class ItemEditorViewModel(QObject):
    stateChanged = Signal()
    affixesChanged = Signal()
    baseChanged = Signal()
    itemLevelChanged = Signal()
    noticeRequested = Signal(str, str)

    def __init__(self, service: ItemEditorService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self._selected_base_category = self._current_base().category if self._current_base() else ""

    def _current_base(self) -> BaseDefinition | None:
        return self.service.catalog.bases.get(self.service.item.base_id)

    def _base_view(self, base: BaseDefinition) -> dict[str, object]:
        return {
            "id": base.id,
            "name": base.name,
            "category": base.category,
            "subcategory": base.subcategory,
            "equipmentType": base.equipment_type,
            "characterRequirementLevel": base.character_level_requirement,
            "minimumItemLevel": base.minimum_item_level,
        }

    def _instance_view(self, instance) -> dict[str, object]:
        definition = self.service.catalog.affixes.get(instance.definition_id)
        tier = next((option for option in definition.tiers if option.id == instance.tier_id), None) if definition else None
        return {
            "id": instance.id,
            "definitionId": instance.definition_id,
            "name": definition.name if definition else "Unknown affix",
            "group": instance.group.value,
            "category": instance.category.value,
            "tierId": instance.tier_id,
            "value": instance.value,
            "tierRange": tier.value_range if tier else "",
            "verificationStatus": instance.verification_status,
        }

    def _slots(self, group: AffixGroup) -> list[dict[str, object]]:
        return [
            {
                **slot,
                "affix": next(
                    (
                        self._instance_view(instance)
                        for instance in self.service.item.affixes
                        if instance.id == slot["instanceId"]
                    ),
                    {},
                ),
            }
            for slot in self.service.slots(group)
        ]

    @Property(str, notify=stateChanged)
    def itemName(self) -> str:
        return self.service.item.name

    @Property(str, notify=stateChanged)
    def baseId(self) -> str:
        return self.service.item.base_id

    @Property(str, notify=stateChanged)
    def baseName(self) -> str:
        base = self._current_base()
        return base.name if base else "Unknown base"

    @Property(str, notify=stateChanged)
    def baseCategory(self) -> str:
        base = self._current_base()
        return base.category if base else ""

    @Property(str, notify=stateChanged)
    def baseSubcategory(self) -> str:
        base = self._current_base()
        return base.subcategory if base else ""

    @Property(str, notify=stateChanged)
    def equipmentType(self) -> str:
        base = self._current_base()
        return base.equipment_type if base else ""

    @Property(int, notify=stateChanged)
    def itemLevel(self) -> int:
        return self.service.item.item_level

    @Property(bool, notify=stateChanged)
    def priceless(self) -> bool:
        return self.service.item.priceless

    @Property(str, notify=stateChanged)
    def rarityLabel(self) -> str:
        return self.service.item.rarity or "Not set"

    @Property(bool, notify=stateChanged)
    def isDirty(self) -> bool:
        return self.service.is_dirty

    @Property(str, notify=stateChanged)
    def itemLevelRange(self) -> str:
        return f"{MIN_ITEM_LEVEL}–{MAX_ITEM_LEVEL}"

    @Property(str, notify=stateChanged)
    def characterRequirementText(self) -> str:
        base = self._current_base()
        return (
            f"Character requirement {base.character_level_requirement}"
            if base and base.character_level_requirement is not None
            else "Character requirement not listed"
        )

    @Property(str, notify=stateChanged)
    def baseVerificationText(self) -> str:
        base = self._current_base()
        if base is None:
            return "Base data unavailable"
        if base.verification_status == "community_reference_season_unverified":
            return "Community data · SS14 unverified"
        return "Verification pending"

    @Property(str, notify=stateChanged)
    def slotLimitText(self) -> str:
        base = self._current_base()
        if base is None or base.limit_status == "unknown":
            return "Slot limits are not verified for this base."
        if base.limit_status == "visual_example_only":
            return "Three slots per group shown from screenshot · unverified"
        return "Slot limits follow catalog data."

    @Property("QVariantList", notify=stateChanged)
    def baseCategories(self) -> list[dict[str, str]]:
        categories = sorted({base.category for base in self.service.catalog.bases.values()})
        return [{"name": category, "id": category} for category in categories]

    @Property("QVariantList", notify=stateChanged)
    def baseOptions(self) -> list[dict[str, object]]:
        return [
            self._base_view(base)
            for base in sorted(self.service.catalog.bases.values(), key=lambda item: (item.category, item.name))
            if base.category == self._selected_base_category
        ]

    @Property("QVariantList", notify=stateChanged)
    def allBaseOptions(self) -> list[dict[str, object]]:
        return [
            self._base_view(base)
            for base in sorted(self.service.catalog.bases.values(), key=lambda item: (item.category, item.name))
        ]

    @Property(str, notify=stateChanged)
    def selectedBaseCategory(self) -> str:
        return self._selected_base_category

    @Property("QVariantList", notify=affixesChanged)
    def prefixSlots(self) -> list[dict[str, object]]:
        return self._slots(AffixGroup.PREFIX)

    @Property("QVariantList", notify=affixesChanged)
    def suffixSlots(self) -> list[dict[str, object]]:
        return self._slots(AffixGroup.SUFFIX)

    @Property("QVariantList", notify=affixesChanged)
    def prefixAffixes(self) -> list[dict[str, object]]:
        return [self._instance_view(item) for item in self.service.item.affixes if item.group == AffixGroup.PREFIX]

    @Property("QVariantList", notify=affixesChanged)
    def suffixAffixes(self) -> list[dict[str, object]]:
        return [self._instance_view(item) for item in self.service.item.affixes if item.group == AffixGroup.SUFFIX]

    @Property(str, notify=affixesChanged)
    def prefixCountLabel(self) -> str:
        return self._count_label(AffixGroup.PREFIX)

    @Property(str, notify=affixesChanged)
    def suffixCountLabel(self) -> str:
        return self._count_label(AffixGroup.SUFFIX)

    @Property("QVariantList", notify=stateChanged)
    def incompatibleAffixes(self) -> list[dict[str, str]]:
        return [
            {"id": issue.instance.id, "name": issue.name, "reason": issue.reason}
            for issue in self.service.incompatible_affixes()
        ]

    @Property(bool, notify=stateChanged)
    def hasIncompatibleAffixes(self) -> bool:
        return bool(self.service.incompatible_affixes())

    @Property(str, notify=stateChanged)
    def prefixHeaderHint(self) -> str:
        base = self._current_base()
        return self._limit_hint(base.prefix_limit if base else None)

    @Property(str, notify=stateChanged)
    def suffixHeaderHint(self) -> str:
        base = self._current_base()
        return self._limit_hint(base.suffix_limit if base else None)

    @staticmethod
    def _limit_hint(limit: int | None) -> str:
        return f"{limit} slots" if limit is not None else "limit unknown"

    def _count_label(self, group: AffixGroup) -> str:
        count = sum(1 for item in self.service.item.affixes if item.group == group)
        base = self._current_base()
        limit = (base.prefix_limit if group == AffixGroup.PREFIX else base.suffix_limit) if base else None
        return f"{count} / {limit}" if limit is not None else f"{count} · limit unknown"

    @Slot(str)
    def setItemName(self, name: str) -> None:
        before = self.service.item.name
        self.service.set_name(name)
        if before != self.service.item.name:
            self.stateChanged.emit()

    @Slot(int)
    def setItemLevel(self, level: int) -> None:
        try:
            self.service.set_item_level(level)
        except ValueError as exc:
            self.noticeRequested.emit(str(exc), "error")
            return
        self.stateChanged.emit()
        self.itemLevelChanged.emit()

    @Slot(bool)
    def setPriceless(self, priceless: bool) -> None:
        if self.service.item.priceless != priceless:
            self.service.set_priceless(priceless)
            self.stateChanged.emit()

    @Slot(str)
    def setBase(self, base_id: str) -> None:
        if base_id == self.service.item.base_id:
            return
        try:
            incompatible = self.service.change_base(base_id)
        except ValueError as exc:
            self.noticeRequested.emit(str(exc), "error")
            return
        base = self._current_base()
        if base:
            self._selected_base_category = base.category
        self.stateChanged.emit()
        self.affixesChanged.emit()
        self.baseChanged.emit()
        if incompatible:
            self.noticeRequested.emit(
                f"Base changed. {len(incompatible)} incompatible affix(es) were kept. Review them before saving.",
                "warning",
            )
        elif base:
            self.noticeRequested.emit(f"Base changed to {base.name}.", "success")

    @Slot(str)
    def setBaseCategory(self, category: str) -> None:
        if category not in {base.category for base in self.service.catalog.bases.values()}:
            return
        self._selected_base_category = category
        options = [base for base in self.service.catalog.bases.values() if base.category == category]
        if options and self.service.item.base_id not in {base.id for base in options}:
            self.setBase(sorted(options, key=lambda base: base.name)[0].id)
        else:
            self.stateChanged.emit()

    @Slot(str)
    def removeIncompatibleAffixes(self) -> None:
        ids = {issue.instance.id for issue in self.service.incompatible_affixes()}
        count = self.service.remove_incompatible_affixes(ids)
        if count:
            self.affixesChanged.emit()
            self.stateChanged.emit()
            self.noticeRequested.emit(f"Removed {count} incompatible affix(es).", "success")

    def item_replaced(self) -> None:
        base = self._current_base()
        self._selected_base_category = base.category if base else ""
        self.stateChanged.emit()
        self.affixesChanged.emit()
