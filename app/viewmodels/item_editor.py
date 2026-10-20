"""QML-facing equipment state and configuration actions."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from core.models import (
    AffixGroup,
    BaseDefinition,
    MIN_ITEM_LEVEL,
    MAX_ITEM_LEVEL,
    resolve_tier_reference,
)
from services.item_editor_service import ItemEditorService


class ItemEditorViewModel(QObject):
    stateChanged = Signal()
    equipmentChanged = Signal()
    affixesChanged = Signal()
    baseChanged = Signal()
    itemLevelChanged = Signal()
    noticeRequested = Signal(str, str)

    def __init__(self, service: ItemEditorService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self._selectable_bases = tuple(
            sorted(
                (base for base in self.service.catalog.bases.values() if not base.is_legacy_alias),
                key=lambda base: (base.category.casefold(), base.subcategory.casefold(), base.name.casefold()),
            )
        )
        current = self._current_base()
        self._selected_base_category = current.category if current else ""
        self._selected_base_subcategory = current.subcategory if current else ""
        if current and current.is_legacy_alias:
            matching = next((base for base in self._selectable_bases if base.subcategory == current.subcategory), None)
            if matching:
                self._selected_base_category = matching.category
        self._base_search_query = ""
        self._base_class_filter = "standard_craftable"
        self._auto_suggest_base = True

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
            "craftingClass": base.crafting_class,
            "recordKind": base.record_kind,
            "editorSupported": base.editor_supported,
            "classificationEvidence": base.classification_evidence,
            "legacyAlias": base.is_legacy_alias,
            "characterRequirementText": (
                f"Character level {base.character_level_requirement}"
                if base.character_level_requirement is not None
                else "Character requirement not listed"
            ),
        }

    def _instance_view(self, instance) -> dict[str, object]:
        definition = self.service.catalog.affixes.get(instance.definition_id)
        tier, tier_ambiguous = (
            resolve_tier_reference(definition.tiers, instance.tier_id)
            if definition else (None, False)
        )
        return {
            "id": instance.id,
            "definitionId": instance.definition_id,
            "name": definition.name if definition else "Unknown affix",
            "group": instance.group.value,
            "category": instance.category.value,
            "tierId": instance.tier_id,
            "tierLabel": tier.tier_label if tier else instance.tier_id,
            "tierAmbiguous": tier_ambiguous,
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
    def baseCraftingStatus(self) -> str:
        base = self._current_base()
        if base is None:
            return "Base data unavailable"
        if base.crafting_class == "standard_craftable":
            return "Standard crafting data listed"
        if base.crafting_class == "special_craftable":
            return "Special modification system · not implemented"
        if base.crafting_class == "non_craftable":
            return "Not craftable in the documented source"
        return "Crafting compatibility unknown"

    @Property(str, notify=stateChanged)
    def basePropertySummary(self) -> str:
        base = self._current_base()
        return " · ".join(base.base_properties[:4]) if base else ""

    @Property(str, notify=stateChanged)
    def baseSourceUrl(self) -> str:
        base = self._current_base()
        return base.source_url if base else ""

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
        categories = sorted({base.category for base in self._selectable_bases})
        return [{"name": category, "id": category} for category in categories]

    @Property("QVariantList", notify=stateChanged)
    def baseSubcategories(self) -> list[dict[str, str]]:
        categories = sorted({
            base.subcategory for base in self._selectable_bases
            if base.category == self._selected_base_category
        })
        return [{"name": category, "id": category} for category in categories]

    @Property("QVariantList", notify=stateChanged)
    def baseOptions(self) -> list[dict[str, object]]:
        query = self._base_search_query.casefold().strip()
        matches = [
            base for base in self._selectable_bases
            if base.crafting_class == self._base_class_filter
            and base.category == self._selected_base_category
            and (not self._selected_base_subcategory or base.subcategory == self._selected_base_subcategory)
            and (not query or query in base.name.casefold())
        ]
        return [self._base_view(base) for base in matches]

    @Property("QVariantList", notify=stateChanged)
    def allBaseOptions(self) -> list[dict[str, object]]:
        return [
            self._base_view(base)
            for base in self._selectable_bases
        ]

    @Property(str, notify=stateChanged)
    def selectedBaseCategory(self) -> str:
        return self._selected_base_category

    @Property(str, notify=stateChanged)
    def selectedBaseSubcategory(self) -> str:
        return self._selected_base_subcategory

    @Property(str, notify=stateChanged)
    def baseSearchQuery(self) -> str:
        return self._base_search_query

    @Property(str, notify=stateChanged)
    def baseResultSummary(self) -> str:
        query = self._base_search_query.casefold().strip()
        matching_count = sum(
            1 for base in self._selectable_bases
            if base.crafting_class == self._base_class_filter
            and base.category == self._selected_base_category
            and (not self._selected_base_subcategory or base.subcategory == self._selected_base_subcategory)
            and (not query or query in base.name.casefold())
        )
        shown = len(self.baseOptions)
        if matching_count > shown:
            return f"{matching_count} matching bases"
        return f"{matching_count} matching base(s)"

    @Property("QVariantList", notify=stateChanged)
    def baseClassFilters(self) -> list[dict[str, str]]:
        return [
            {"name": "Standard craftable", "id": "standard_craftable"},
            {"name": "Special systems", "id": "special_craftable"},
            {"name": "Unknown compatibility", "id": "unknown"},
            {"name": "Not craftable", "id": "non_craftable"},
        ]

    @Property(str, notify=stateChanged)
    def baseClassFilter(self) -> str:
        return self._base_class_filter

    @Property(bool, notify=stateChanged)
    def autoSuggestBase(self) -> bool:
        return self._auto_suggest_base

    @Property("QVariantList", notify=stateChanged)
    def suggestedBaseOptions(self) -> list[dict[str, object]]:
        if not self._auto_suggest_base:
            return []
        eligible = [
            base for base in self._selectable_bases
            if base.crafting_class == "standard_craftable"
            and base.category == self._selected_base_category
            and (not self._selected_base_subcategory or base.subcategory == self._selected_base_subcategory)
            and base.minimum_item_level is not None
            and base.minimum_item_level <= self.service.item.item_level
        ]
        if not eligible:
            return []
        best_minimum = max(base.minimum_item_level for base in eligible if base.minimum_item_level is not None)
        best = [base for base in eligible if base.minimum_item_level == best_minimum]
        best.sort(key=lambda base: (base.character_level_requirement or 0, base.name.casefold()))
        return [self._base_view(base) for base in best]

    @Property(str, notify=stateChanged)
    def baseSuggestionSummary(self) -> str:
        if not self._auto_suggest_base:
            return "Base suggestions are off."
        candidates = self.suggestedBaseOptions
        if not candidates:
            return "No verified minimum Item Level is available for this base category. Choose a base manually."
        if len(candidates) > 1:
            return f"{len(candidates)} bases share the closest verified minimum Item Level; choose manually."
        candidate = candidates[0]
        return (
            f"Suggestion: {candidate['name']} · minimum Item Level {candidate['minimumItemLevel']}"
            f" · {candidate['characterRequirementText']}"
        )

    @Property(bool, notify=stateChanged)
    def canApplyBaseSuggestion(self) -> bool:
        return len(self.suggestedBaseOptions) == 1

    @Property(str, notify=stateChanged)
    def baseCompatibilityWarning(self) -> str:
        base = self._current_base()
        if base is None or base.minimum_item_level is None:
            return ""
        if self.service.item.item_level < base.minimum_item_level:
            return f"This base lists minimum Item Level {base.minimum_item_level}; the equipment is Item Level {self.service.item.item_level}."
        return ""

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
            self.equipmentChanged.emit()

    @Slot(int)
    def setItemLevel(self, level: int) -> None:
        try:
            self.service.set_item_level(level)
        except ValueError as exc:
            self.noticeRequested.emit(str(exc), "error")
            return
        self.stateChanged.emit()
        self.itemLevelChanged.emit()
        self.equipmentChanged.emit()

    @Slot(bool)
    def setPriceless(self, priceless: bool) -> None:
        if self.service.item.priceless != priceless:
            self.service.set_priceless(priceless)
            self.stateChanged.emit()
            self.equipmentChanged.emit()

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
            self._selected_base_subcategory = base.subcategory
        self.stateChanged.emit()
        self.affixesChanged.emit()
        self.baseChanged.emit()
        self.equipmentChanged.emit()
        if incompatible:
            self.noticeRequested.emit(
                f"Base changed. {len(incompatible)} incompatible affix(es) were kept. Review them before saving.",
                "warning",
            )
        elif base:
            self.noticeRequested.emit(f"Base changed to {base.name}.", "success")

    @Slot(str)
    def setBaseCategory(self, category: str) -> None:
        if category not in {base.category for base in self._selectable_bases}:
            return
        self._selected_base_category = category
        options = [base for base in self._selectable_bases if base.category == category]
        subcategories = sorted({base.subcategory for base in options})
        if self._selected_base_subcategory not in subcategories:
            self._selected_base_subcategory = subcategories[0] if subcategories else ""
        self.stateChanged.emit()

    @Slot(str)
    def setBaseSubcategory(self, subcategory: str) -> None:
        options = [
            base for base in self._selectable_bases
            if base.category == self._selected_base_category and base.subcategory == subcategory
        ]
        if not options:
            return
        self._selected_base_subcategory = subcategory
        self.stateChanged.emit()

    @Slot(str)
    def setBaseClassFilter(self, crafting_class: str) -> None:
        if crafting_class not in {entry["id"] for entry in self.baseClassFilters}:
            return
        if crafting_class != self._base_class_filter:
            self._base_class_filter = crafting_class
            self.stateChanged.emit()

    @Slot(bool)
    def setAutoSuggestBase(self, enabled: bool) -> None:
        if self._auto_suggest_base != enabled:
            self._auto_suggest_base = enabled
            self.stateChanged.emit()

    @Slot()
    def applySuggestedBase(self) -> None:
        candidates = self.suggestedBaseOptions
        if len(candidates) == 1:
            self.setBase(str(candidates[0]["id"]))

    @Slot(str)
    def setBaseSearch(self, query: str) -> None:
        clean = query[:100]
        if clean != self._base_search_query:
            self._base_search_query = clean
            self.stateChanged.emit()

    @Slot(str)
    def removeIncompatibleAffixes(self) -> None:
        ids = {issue.instance.id for issue in self.service.incompatible_affixes()}
        count = self.service.remove_incompatible_affixes(ids)
        if count:
            self.affixesChanged.emit()
            self.stateChanged.emit()
            self.equipmentChanged.emit()
            self.noticeRequested.emit(f"Removed {count} incompatible affix(es).", "success")

    def item_replaced(self) -> None:
        base = self._current_base()
        self._selected_base_category = base.category if base else ""
        self._selected_base_subcategory = base.subcategory if base else ""
        self._base_search_query = ""
        self.stateChanged.emit()
        self.affixesChanged.emit()
        self.equipmentChanged.emit()
