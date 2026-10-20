"""QML-facing affix search, selection, tier and contextual edit state."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from core.models import AffixCategory, AffixGroup, AffixInstance, resolve_tier_reference
from services.affix_browser import AffixBrowser
from services.item_editor_service import ItemEditError, ItemEditorService


class AffixBrowserViewModel(QObject):
    selectionChanged = Signal()
    affixesChanged = Signal()
    itemChanged = Signal()
    noticeRequested = Signal(str, str)

    def __init__(
        self,
        browser: AffixBrowser,
        editor: ItemEditorService,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.browser = browser
        self.editor = editor
        self._set_default_selection()

    def _definition_is_on_item(self, definition_id: str, excluding: str | None = None) -> bool:
        definition = self.browser.catalog.affixes.get(definition_id)
        for item in self.editor.item.affixes:
            if item.id == excluding:
                continue
            if item.definition_id == definition_id:
                return True
            old_definition = self.browser.catalog.affixes.get(item.definition_id)
            if (
                definition is None
                or old_definition is None
                or not old_definition.is_legacy_alias
                or definition_id not in old_definition.legacy_family_member_ids
            ):
                continue
            old_tier, ambiguous = resolve_tier_reference(old_definition.tiers, item.tier_id)
            if ambiguous:
                return True
            if old_tier and any(tier.id == old_tier.id for tier in definition.tiers):
                return True
        return False

    def _set_default_selection(self) -> None:
        candidates = self.browser.definitions_for(self.editor.item.base_id)
        definition = next(
            (item for item in candidates if not self._definition_is_on_item(item.id)),
            candidates[0] if candidates else None,
        )
        if definition:
            self.browser.select_definition(definition, self.editor.item.item_level)

    def _tier_view(self, tier, index: int) -> dict[str, object]:
        eligible = tier.item_level_required is None or self.editor.item.item_level >= tier.item_level_required
        return {
            "id": tier.id,
            "tierLabel": tier.tier_label,
            "valueRange": tier.value_range,
            "itemLevelRequired": tier.item_level_required,
            "itemLevelRequiredRaw": tier.requirement_level_raw,
            "weightRaw": tier.weight_raw,
            "weightParseStatus": tier.weight_parse_status,
            "sourceSection": tier.source_section,
            "sourceTable": tier.source_table,
            "sourceRowKey": tier.source_row_key,
            "sourceUrl": tier.source_url,
            "eligible": eligible,
            "label": f"{tier.tier_label} · {tier.value_range}",
            "sortIndex": index,
        }

    def _definition_view(self, definition) -> dict[str, object]:
        return {
            "id": definition.id,
            "name": definition.name,
            "group": definition.group.value,
            "category": definition.category.value,
            "compatibilityStatus": definition.compatibility_status,
            "verificationStatus": definition.verification_status,
            "tierSummary": self._tier_summary(definition),
            "tierCount": len(definition.tiers),
            "categoryLabel": f"{definition.group.value.title()} · {definition.category.value}",
            "craftingSystemId": definition.crafting_system_id,
            "sourceSection": definition.source_section,
            "familyGroupingStatus": definition.family_grouping_status,
            "alreadyAdded": self._definition_is_on_item(definition.id, self.browser.instance_id),
        }

    @staticmethod
    def _tier_summary(definition) -> str:
        labels = [tier.tier_label for tier in definition.tiers]
        preview = " · ".join(labels[:4])
        return f"{preview} · +{len(labels) - 4}" if len(labels) > 4 else preview

    @Property("QVariantList", notify=selectionChanged)
    def availableAffixes(self) -> list[dict[str, object]]:
        return [
            self._definition_view(definition)
            for definition in self.browser.definitions_for(self.editor.item.base_id)
        ]

    @Property("QVariantList", notify=selectionChanged)
    def tierOptions(self) -> list[dict[str, object]]:
        definition = self.browser.definition
        return [self._tier_view(tier, index) for index, tier in enumerate(definition.tiers)] if definition else []

    @Property(str, notify=selectionChanged)
    def selectedGroup(self) -> str:
        return self.browser.group.value

    @Property(str, notify=selectionChanged)
    def selectedCategory(self) -> str:
        return self.browser.category.value

    @Property(str, notify=selectionChanged)
    def selectedDefinitionId(self) -> str:
        return self.browser.definition_id or ""

    @Property(bool, notify=selectionChanged)
    def selectedDefinitionAlreadyAdded(self) -> bool:
        return bool(
            self.browser.definition_id
            and self._definition_is_on_item(self.browser.definition_id, self.browser.instance_id)
        )

    @Property(str, notify=selectionChanged)
    def selectedDefinitionName(self) -> str:
        definition = self.browser.definition
        return definition.name if definition else "Select an affix"

    @Property(str, notify=selectionChanged)
    def selectedTierId(self) -> str:
        tier = self.browser.selected_tier()
        return tier.id if tier else ""

    @Property(bool, notify=selectionChanged)
    def selectedTierAmbiguous(self) -> bool:
        return self.browser.selected_tier_is_ambiguous()

    @Property(str, notify=selectionChanged)
    def selectedValue(self) -> str:
        return self.browser.value

    @Property(bool, notify=selectionChanged)
    def selectedTierEligible(self) -> bool:
        tier = self.browser.selected_tier()
        return bool(tier and (tier.item_level_required is None or self.editor.item.item_level >= tier.item_level_required))

    @Property(str, notify=selectionChanged)
    def selectedTierTechnicalText(self) -> str:
        tier = self.browser.selected_tier()
        if tier is None:
            return ""
        level = f"Requires Item Level {tier.item_level_required}" if tier.item_level_required is not None else "Item Level requirement not listed"
        weight = f"Published weight {tier.weight_raw}" if tier.weight_raw is not None else "Weight not listed"
        source = tier.source_section or tier.source_table or "TLIDB source"
        return f"{level} · {weight} · {source} · {tier.source_row_key} · weight is source data, not a probability"

    @Property(str, notify=selectionChanged)
    def selectedTierSourceUrl(self) -> str:
        tier = self.browser.selected_tier()
        return tier.source_url if tier else ""

    @Property(bool, notify=selectionChanged)
    def selectedValueEditable(self) -> bool:
        return bool(self.browser.definition and self.browser.definition.value_editable)

    @Property(str, notify=selectionChanged)
    def selectedInstanceId(self) -> str:
        return self.browser.instance_id or ""

    @Property(bool, notify=selectionChanged)
    def isEditingAffix(self) -> bool:
        return self.browser.instance_id is not None

    @Property(str, notify=selectionChanged)
    def selectedMode(self) -> str:
        return self.browser.mode

    @Property(str, notify=selectionChanged)
    def actionLabel(self) -> str:
        return {
            "add": "Add affix",
            "edit": "Update affix",
            "replace": "Replace affix",
        }.get(self.browser.mode, "Select affix")

    @Property(str, notify=selectionChanged)
    def selectionVerificationText(self) -> str:
        if not self.browser.definition:
            return "Choose an affix from the local catalog."
        definition = self.browser.definition
        if definition.family_grouping_status == "ambiguous_legacy_alias":
            if self.browser.selected_tier_is_ambiguous():
                return "Legacy family split · this saved tier label is ambiguous"
            return "Legacy family alias · selected tier resolves to a source record"
        if definition and definition.family_grouping_status != "source_family_id":
            return "Community reference · family grouping pending · SS14 unverified"
        return "Community reference · SS14 unverified"

    @Property(str, notify=selectionChanged)
    def searchQuery(self) -> str:
        return self.browser.search_query

    @Slot(str)
    def setAffixGroup(self, group: str) -> None:
        try:
            self.browser.set_group(AffixGroup(group))
        except ValueError:
            return
        self._set_default_selection()
        self.selectionChanged.emit()

    @Slot(str)
    def setAffixCategory(self, category: str) -> None:
        try:
            self.browser.set_category(AffixCategory(category))
        except ValueError:
            return
        self._set_default_selection()
        self.selectionChanged.emit()

    @Slot(str)
    def setSearchQuery(self, query: str) -> None:
        self.browser.set_search(query)
        self.selectionChanged.emit()

    @Slot(str)
    def selectDefinition(self, definition_id: str) -> None:
        definition = self.browser.catalog.affixes.get(definition_id)
        if definition is None:
            return
        self.browser.select_definition(definition, self.editor.item.item_level)
        self.selectionChanged.emit()

    @Slot(str)
    def beginAddAffix(self, group: str) -> None:
        try:
            selected = AffixGroup(group)
        except ValueError:
            return
        self.browser.begin_add(selected)
        self._set_default_selection()
        self.selectionChanged.emit()

    @Slot(str, int)
    def beginAddAffixAtSlot(self, group: str, index: int) -> None:
        try:
            selected = AffixGroup(group)
        except ValueError:
            return
        self.browser.begin_add(selected, index)
        self._set_default_selection()
        self.selectionChanged.emit()

    @Slot(str)
    def selectAffixInstance(self, instance_id: str) -> None:
        instance = next((item for item in self.editor.item.affixes if item.id == instance_id), None)
        if instance is None:
            return
        if instance.definition_id not in self.browser.catalog.affixes:
            self.noticeRequested.emit("This affix is no longer in the local catalog, so it is read-only.", "error")
            return
        self.browser.select_instance(instance)
        self.selectionChanged.emit()

    @Slot(str)
    def setTier(self, tier_id: str) -> None:
        tier = self.browser.set_tier(tier_id, self.editor.item.item_level)
        if tier is None:
            definition = self.browser.definition
            option = next((item for item in definition.tiers if item.id == tier_id), None) if definition else None
            if option:
                self.noticeRequested.emit(f"{option.tier_label} is listed from Item Level {option.item_level_required}.", "error")
            return
        self.selectionChanged.emit()

    @Slot(str)
    def setAffixValue(self, value: str) -> None:
        self.browser.value = value[:120]
        self.selectionChanged.emit()

    @Slot()
    def addOrUpdateAffix(self) -> None:
        definition = self.browser.definition
        tier = self.browser.selected_tier()
        if definition is None or tier is None:
            self.noticeRequested.emit("Choose an available affix and tier first.", "error")
            return
        mode = self.browser.mode
        try:
            instance = self.editor.add_or_update_affix(
                definition,
                tier,
                self.browser.value,
                instance_id=self.browser.instance_id,
                slot_index=self.browser.slot_index,
            )
        except ItemEditError as exc:
            self.noticeRequested.emit(str(exc), "error")
            return
        self.browser.select_instance(instance)
        self.itemChanged.emit()
        self.affixesChanged.emit()
        self.selectionChanged.emit()
        message = "Affix added." if mode == "add" else "Affix replaced." if mode == "replace" else "Affix updated."
        self.noticeRequested.emit(message, "success")

    @Slot()
    def removeSelectedAffix(self) -> None:
        instance_id = self.browser.instance_id
        if not instance_id or not self.editor.remove_affix(instance_id):
            if instance_id:
                self.noticeRequested.emit("That affix is no longer on this item.", "error")
            return
        self.browser.clear_selection()
        self._set_default_selection()
        self.itemChanged.emit()
        self.affixesChanged.emit()
        self.selectionChanged.emit()
        self.noticeRequested.emit("Affix removed.", "success")

    def item_replaced(self) -> None:
        self.browser.clear_selection()
        self._set_default_selection()
        self.selectionChanged.emit()

    def item_level_changed(self) -> None:
        self.selectionChanged.emit()

