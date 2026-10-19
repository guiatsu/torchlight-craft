"""QML-facing affix search, selection, tier and contextual edit state."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from core.models import AffixCategory, AffixGroup, AffixInstance
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
        return any(
            item.definition_id == definition_id and item.id != excluding
            for item in self.editor.item.affixes
        )

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
            "valueRange": tier.value_range,
            "itemLevelRequired": tier.item_level_required,
            "eligible": eligible,
            "label": f"{tier.id} · {tier.value_range}",
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
            "tierSummary": " · ".join(tier.id for tier in definition.tiers),
            "alreadyAdded": self._definition_is_on_item(definition.id, self.browser.instance_id),
        }

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
        return self.browser.tier_id or ""

    @Property(str, notify=selectionChanged)
    def selectedValue(self) -> str:
        return self.browser.value

    @Property(bool, notify=selectionChanged)
    def selectedTierEligible(self) -> bool:
        tier = self.browser.selected_tier()
        return bool(tier and (tier.item_level_required is None or self.editor.item.item_level >= tier.item_level_required))

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
        return "Community reference · compatibility provisional · SS14 unverified"

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
                self.noticeRequested.emit(f"{option.id} is listed from Item Level {option.item_level_required}.", "error")
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

