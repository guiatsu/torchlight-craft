"""Qt bridge for the QML editor."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QObject, Property, QStandardPaths, Signal, Slot

from core.catalog import Catalog, load_catalog
from core.models import (
    MAX_ITEM_LEVEL,
    MIN_ITEM_LEVEL,
    AffixCategory,
    AffixDefinition,
    AffixGroup,
    AffixInstance,
    BaseDefinition,
    EquipmentItem,
    TierOption,
    new_equipment,
)
from core.validation import validate_item
from services.item_repository import ItemRepository, RepositoryError


class AppController(QObject):
    stateChanged = Signal()
    affixesChanged = Signal()
    selectionChanged = Signal()
    savedItemsChanged = Signal()
    noticeChanged = Signal()
    confirmUnsaved = Signal()
    closeConfirmed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.catalog: Catalog = load_catalog()
        app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        self.repository = ItemRepository(Path(app_data) / "items.json")
        self._current_item = new_equipment()
        initial_base = self.catalog.bases.get(self._current_item.base_id)
        if initial_base:
            self._current_item.name = initial_base.name
        self._saved_items: list[EquipmentItem] = []
        self._baseline = self._current_item.to_dict()
        self._pending_action: tuple[str, str | None] | None = None
        self._selected_group = AffixGroup.PREFIX
        self._selected_category = AffixCategory.BASIC
        current_base = self._current_base()
        self._selected_base_category = current_base.category if current_base else ""
        self._search_query = ""
        self._selected_definition_id: str | None = None
        self._selected_instance_id: str | None = None
        self._selected_tier_id: str | None = None
        self._selected_value = ""
        self._notice_text = ""
        self._notice_kind = "info"
        self._refresh_saved_items(silent=True)
        self._set_default_selection()

    def _set_default_selection(self) -> None:
        candidates = [
            definition
            for definition in self._matching_affixes()
            if not self._definition_is_on_item(definition.id)
        ]
        if not candidates:
            candidates = self._matching_affixes()
        if candidates:
            self._select_definition(candidates[0].id)

    def _definition_is_on_item(
        self, definition_id: str, excluding_instance_id: str | None = None
    ) -> bool:
        return any(
            instance.definition_id == definition_id
            and instance.id != excluding_instance_id
            for instance in self._current_item.affixes
        )

    @staticmethod
    def _enum_value(value: AffixGroup | AffixCategory) -> str:
        return str(value.value)

    def _current_base(self) -> BaseDefinition | None:
        return self.catalog.bases.get(self._current_item.base_id)

    def _dirty(self) -> bool:
        return self._current_item.to_dict() != self._baseline

    def _emit_all(self) -> None:
        self.stateChanged.emit()
        self.affixesChanged.emit()
        self.selectionChanged.emit()

    def _set_notice(self, message: str, kind: str = "info") -> None:
        self._notice_text = message
        self._notice_kind = kind
        self.noticeChanged.emit()

    def _definitions_for(self, base: BaseDefinition | None = None) -> list[AffixDefinition]:
        selected_base = base or self._current_base()
        if selected_base is None:
            return []
        return sorted(
            (
                definition
                for definition in self.catalog.affixes.values()
                if not definition.base_ids or selected_base.id in definition.base_ids
            ),
            key=lambda definition: (definition.group.value, definition.category.value, definition.name),
        )

    def _matching_affixes(self) -> list[AffixDefinition]:
        query = self._search_query.casefold().strip()
        return [
            definition
            for definition in self._definitions_for()
            if definition.group == self._selected_group
            and definition.category == self._selected_category
            and (not query or query in definition.name.casefold())
        ]

    def _selected_definition(self) -> AffixDefinition | None:
        if self._selected_definition_id is None:
            return None
        return self.catalog.affixes.get(self._selected_definition_id)

    def _selected_tier(self, definition: AffixDefinition | None = None) -> TierOption | None:
        selected = definition or self._selected_definition()
        if selected is None:
            return None
        return next((tier for tier in selected.tiers if tier.id == self._selected_tier_id), None)

    def _tier_view(self, tier: TierOption, index: int) -> dict[str, object]:
        eligible = tier.item_level_required is None or self._current_item.item_level >= tier.item_level_required
        return {
            "id": tier.id,
            "valueRange": tier.value_range,
            "itemLevelRequired": tier.item_level_required,
            "eligible": eligible,
            "label": f"{tier.id} · {tier.value_range}",
            "sortIndex": index,
        }

    @Property(str, notify=stateChanged)
    def itemName(self) -> str:
        return self._current_item.name

    @Property(str, notify=stateChanged)
    def baseId(self) -> str:
        return self._current_item.base_id

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
        return self._current_item.item_level

    @Property(bool, notify=stateChanged)
    def priceless(self) -> bool:
        return self._current_item.priceless

    @Property(str, notify=stateChanged)
    def rarityLabel(self) -> str:
        return self._current_item.rarity or "Not set"

    @Property(bool, notify=stateChanged)
    def isDirty(self) -> bool:
        return self._dirty()

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
            return "3 + 3 slots shown from screenshot · unverified"
        return "Slot limits follow catalog data."

    @Property("QVariantList", notify=stateChanged)
    def baseCategories(self) -> list[dict[str, str]]:
        categories = sorted({base.category for base in self.catalog.bases.values()})
        return [{"name": category, "id": category} for category in categories]

    @Property("QVariantList", notify=stateChanged)
    def baseOptions(self) -> list[dict[str, object]]:
        return [
            self._base_view(option)
            for option in sorted(self.catalog.bases.values(), key=lambda option: (option.category, option.name))
            if option.category == self._selected_base_category
        ]

    @Property("QVariantList", notify=stateChanged)
    def allBaseOptions(self) -> list[dict[str, object]]:
        return [
            self._base_view(base)
            for base in sorted(self.catalog.bases.values(), key=lambda option: (option.category, option.name))
        ]

    @Property(str, notify=stateChanged)
    def selectedBaseCategory(self) -> str:
        return self._selected_base_category

    @Property("QVariantList", notify=affixesChanged)
    def prefixAffixes(self) -> list[dict[str, object]]:
        return [self._instance_view(instance) for instance in self._current_item.affixes if instance.group == AffixGroup.PREFIX]

    @Property("QVariantList", notify=affixesChanged)
    def suffixAffixes(self) -> list[dict[str, object]]:
        return [self._instance_view(instance) for instance in self._current_item.affixes if instance.group == AffixGroup.SUFFIX]

    @Property(str, notify=affixesChanged)
    def prefixCountLabel(self) -> str:
        return self._count_label(AffixGroup.PREFIX)

    @Property(str, notify=affixesChanged)
    def suffixCountLabel(self) -> str:
        return self._count_label(AffixGroup.SUFFIX)

    @Property("QVariantList", notify=selectionChanged)
    def availableAffixes(self) -> list[dict[str, object]]:
        return [self._definition_view(definition) for definition in self._matching_affixes()]

    @Property("QVariantList", notify=selectionChanged)
    def tierOptions(self) -> list[dict[str, object]]:
        definition = self._selected_definition()
        if definition is None:
            return []
        return [self._tier_view(tier, index) for index, tier in enumerate(definition.tiers)]

    @Property(str, notify=selectionChanged)
    def selectedGroup(self) -> str:
        return self._selected_group.value

    @Property(str, notify=selectionChanged)
    def selectedCategory(self) -> str:
        return self._selected_category.value

    @Property(str, notify=selectionChanged)
    def selectedDefinitionId(self) -> str:
        return self._selected_definition_id or ""

    @Property(bool, notify=selectionChanged)
    def selectedDefinitionAlreadyAdded(self) -> bool:
        if self._selected_definition_id is None:
            return False
        return self._definition_is_on_item(
            self._selected_definition_id, self._selected_instance_id
        )

    @Property(str, notify=selectionChanged)
    def selectedDefinitionName(self) -> str:
        definition = self._selected_definition()
        return definition.name if definition else "Select an affix"

    @Property(str, notify=selectionChanged)
    def selectedTierId(self) -> str:
        return self._selected_tier_id or ""

    @Property(str, notify=selectionChanged)
    def selectedValue(self) -> str:
        return self._selected_value

    @Property(bool, notify=selectionChanged)
    def selectedTierEligible(self) -> bool:
        tier = self._selected_tier()
        return tier is not None and (
            tier.item_level_required is None or self._current_item.item_level >= tier.item_level_required
        )

    @Property(bool, notify=selectionChanged)
    def selectedValueEditable(self) -> bool:
        definition = self._selected_definition()
        return bool(definition and definition.value_editable)

    @Property(str, notify=selectionChanged)
    def selectedInstanceId(self) -> str:
        return self._selected_instance_id or ""

    @Property(bool, notify=selectionChanged)
    def isEditingAffix(self) -> bool:
        return self._selected_instance_id is not None

    @Property(str, notify=selectionChanged)
    def selectionVerificationText(self) -> str:
        definition = self._selected_definition()
        if definition is None:
            return "Choose an affix from the local catalog."
        return "Community reference · compatibility provisional · SS14 unverified"

    @Property(str, notify=stateChanged)
    def prefixHeaderHint(self) -> str:
        base = self._current_base()
        return self._limit_hint(base.prefix_limit if base else None)

    @Property(str, notify=stateChanged)
    def suffixHeaderHint(self) -> str:
        base = self._current_base()
        return self._limit_hint(base.suffix_limit if base else None)

    @Property(str, notify=noticeChanged)
    def noticeText(self) -> str:
        return self._notice_text

    @Property(str, notify=noticeChanged)
    def noticeKind(self) -> str:
        return self._notice_kind

    @Property("QVariantList", notify=savedItemsChanged)
    def savedItems(self) -> list[dict[str, object]]:
        return [self._saved_item_view(item) for item in self._saved_items]

    @Property(str, notify=savedItemsChanged)
    def savedCountText(self) -> str:
        count = len(self._saved_items)
        return f"{count} saved item" if count == 1 else f"{count} saved items"

    @staticmethod
    def _base_view(base: BaseDefinition) -> dict[str, object]:
        return {
            "id": base.id,
            "name": base.name,
            "category": base.category,
            "subcategory": base.subcategory,
            "equipmentType": base.equipment_type,
            "characterRequirementLevel": base.character_level_requirement,
            "minimumItemLevel": base.minimum_item_level,
        }

    def _definition_view(self, definition: AffixDefinition) -> dict[str, object]:
        already_added = self._definition_is_on_item(
            definition.id, self._selected_instance_id
        )
        return {
            "id": definition.id,
            "name": definition.name,
            "group": definition.group.value,
            "category": definition.category.value,
            "compatibilityStatus": definition.compatibility_status,
            "verificationStatus": definition.verification_status,
            "tierSummary": " · ".join(tier.id for tier in definition.tiers),
            "alreadyAdded": already_added,
        }

    def _instance_view(self, instance: AffixInstance) -> dict[str, object]:
        definition = self.catalog.affixes.get(instance.definition_id)
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

    def _saved_item_view(self, item: EquipmentItem) -> dict[str, object]:
        base = self.catalog.bases.get(item.base_id)
        return {
            "id": item.id,
            "name": item.name,
            "baseName": base.name if base else "Unknown base",
            "itemLevel": item.item_level,
            "priceless": item.priceless,
            "affixCount": len(item.affixes),
        }

    @staticmethod
    def _limit_hint(limit: int | None) -> str:
        return f"{limit} slots" if limit is not None else "limit unknown"

    def _count_label(self, group: AffixGroup) -> str:
        count = sum(1 for instance in self._current_item.affixes if instance.group == group)
        base = self._current_base()
        limit = None
        if base is not None:
            limit = base.prefix_limit if group == AffixGroup.PREFIX else base.suffix_limit
        return f"{count} / {limit}" if limit is not None else f"{count} · limit unknown"

    def _refresh_saved_items(self, silent: bool = False) -> None:
        try:
            self._saved_items = self.repository.load_all()
        except RepositoryError as exc:
            self._saved_items = []
            if not silent:
                self._set_notice(str(exc), "error")
        self.savedItemsChanged.emit()

    def _commit_current(self) -> bool:
        errors = validate_item(self._current_item, self.catalog.bases, self.catalog.affixes)
        if errors:
            self._set_notice(" ".join(errors), "error")
            return False
        try:
            self._saved_items = self.repository.save_item(self._current_item)
        except RepositoryError as exc:
            self._set_notice(str(exc), "error")
            return False
        self._baseline = self._current_item.to_dict()
        self.savedItemsChanged.emit()
        self.stateChanged.emit()
        self._set_notice("Equipment saved locally.", "success")
        return True

    def _continue_pending_action(self) -> None:
        if self._pending_action is None:
            return
        action, identifier = self._pending_action
        self._pending_action = None
        if action == "new":
            self._start_new_item()
        elif action == "open" and identifier:
            item = next((saved for saved in self._saved_items if saved.id == identifier), None)
            if item is None:
                self._refresh_saved_items()
                self._set_notice("That saved item could not be found.", "error")
                return
            self._load_item(item)
        elif action == "duplicate" and identifier:
            item = next((saved for saved in self._saved_items if saved.id == identifier), None)
            if item is None:
                self._set_notice("That saved item could not be found.", "error")
                return
            copied = EquipmentItem.from_dict(item.to_dict())
            copied.id = f"item-{uuid4().hex}"
            copied.name = f"{item.name} Copy"
            self._current_item = copied
            self._baseline = self._current_item.to_dict() | {"name": ""}
            self._sync_selection_to_item()
            self._emit_all()
            self._set_notice("Duplicate created. Save it when ready.", "success")
        elif action == "close":
            self.closeConfirmed.emit()

    def _load_item(self, item: EquipmentItem) -> None:
        self._current_item = EquipmentItem.from_dict(item.to_dict())
        self._baseline = self._current_item.to_dict()
        self._sync_selection_to_item()
        self._emit_all()
        issues = validate_item(self._current_item, self.catalog.bases, self.catalog.affixes)
        if issues:
            self._set_notice(f"Opened {item.name} with catalog issues: {' '.join(issues)}", "warning")
        else:
            self._set_notice(f"Opened {item.name}.", "success")

    def _start_new_item(self) -> None:
        self._current_item = new_equipment()
        base = self._current_base()
        if base:
            self._current_item.name = base.name
            self._selected_base_category = base.category
        self._baseline = self._current_item.to_dict()
        self._selected_instance_id = None
        self._selected_definition_id = None
        self._selected_tier_id = None
        self._selected_value = ""
        self._set_default_selection()
        self._emit_all()
        self._set_notice("New equipment ready.", "success")

    def _sync_selection_to_item(self) -> None:
        self._selected_instance_id = None
        self._selected_definition_id = None
        self._selected_tier_id = None
        self._selected_value = ""
        self._selected_group = AffixGroup.PREFIX
        self._selected_category = AffixCategory.BASIC
        base = self._current_base()
        self._selected_base_category = base.category if base else ""
        self._search_query = ""
        self._set_default_selection()

    def _select_definition(self, definition_id: str) -> None:
        definition = self.catalog.affixes.get(definition_id)
        if definition is None:
            return
        self._selected_instance_id = None
        self._selected_definition_id = definition.id
        self._selected_tier_id = definition.tiers[0].id if definition.tiers else None
        tier = self._selected_tier(definition)
        self._selected_value = tier.value_range if tier else ""
        self.selectionChanged.emit()

    @Slot(str)
    def setItemName(self, name: str) -> None:
        clean_name = name[:80]
        if self._current_item.name != clean_name:
            self._current_item.name = clean_name
            self.stateChanged.emit()

    @Slot(int)
    def setItemLevel(self, level: int) -> None:
        if isinstance(level, bool) or not MIN_ITEM_LEVEL <= level <= MAX_ITEM_LEVEL:
            self._set_notice(f"Item Level must be between {MIN_ITEM_LEVEL} and {MAX_ITEM_LEVEL}.", "error")
            return
        self._current_item.item_level = level
        self.stateChanged.emit()
        self.selectionChanged.emit()

    @Slot(bool)
    def setPriceless(self, priceless: bool) -> None:
        if self._current_item.priceless != priceless:
            self._current_item.priceless = priceless
            self.stateChanged.emit()

    @Slot(str)
    def setBase(self, base_id: str) -> None:
        base = self.catalog.bases.get(base_id)
        if base is None or base_id == self._current_item.base_id:
            return
        previous = self._current_base()
        if previous and self._current_item.name == previous.name:
            self._current_item.name = base.name
        self._current_item.base_id = base.id
        self._selected_base_category = base.category
        incompatible_count = sum(
            1
            for instance in self._current_item.affixes
            if (definition := self.catalog.affixes.get(instance.definition_id))
            and definition.base_ids
            and base.id not in definition.base_ids
        )
        self._sync_selection_to_item()
        self._emit_all()
        if incompatible_count:
            self._set_notice(
                f"Base changed to {base.name}. {incompatible_count} existing affix(es) were kept; catalog compatibility is unresolved.",
                "warning",
            )
        else:
            self._set_notice(f"Base changed to {base.name}.", "success")

    @Slot(str)
    def setBaseCategory(self, category: str) -> None:
        if category not in {base.category for base in self.catalog.bases.values()}:
            return
        self._selected_base_category = category
        options = [base for base in self.catalog.bases.values() if base.category == category]
        if options and self._current_item.base_id not in {base.id for base in options}:
            self.setBase(sorted(options, key=lambda base: base.name)[0].id)
        else:
            self.stateChanged.emit()

    @Slot(str)
    def setAffixGroup(self, group: str) -> None:
        try:
            selected = AffixGroup(group)
        except ValueError:
            return
        if selected == self._selected_group:
            return
        self._selected_group = selected
        self._selected_definition_id = None
        self._selected_tier_id = None
        self._selected_value = ""
        self.selectionChanged.emit()

    @Slot(str)
    def setAffixCategory(self, category: str) -> None:
        try:
            selected = AffixCategory(category)
        except ValueError:
            return
        if selected == self._selected_category:
            return
        self._selected_category = selected
        self._selected_definition_id = None
        self._selected_tier_id = None
        self._selected_value = ""
        self.selectionChanged.emit()

    @Slot(str)
    def setSearchQuery(self, query: str) -> None:
        self._search_query = query[:100]
        self.selectionChanged.emit()

    @Slot(str)
    def selectDefinition(self, definition_id: str) -> None:
        definition = self.catalog.affixes.get(definition_id)
        if definition is None:
            return
        self._selected_group = definition.group
        self._selected_category = definition.category
        current_instance = self._selected_instance_id
        self._selected_definition_id = definition.id
        eligible_tiers = [
            tier
            for tier in definition.tiers
            if tier.item_level_required is None or self._current_item.item_level >= tier.item_level_required
        ]
        chosen_tier = eligible_tiers[0] if eligible_tiers else (definition.tiers[0] if definition.tiers else None)
        self._selected_tier_id = chosen_tier.id if chosen_tier else None
        self._selected_value = chosen_tier.value_range if chosen_tier else ""
        if current_instance and not any(
            instance.id == current_instance for instance in self._current_item.affixes
        ):
            self._selected_instance_id = None
        self.selectionChanged.emit()

    @Slot(str)
    def beginAddAffix(self, group: str) -> None:
        try:
            selected = AffixGroup(group)
        except ValueError:
            return
        self._selected_group = selected
        self._selected_instance_id = None
        self._selected_definition_id = None
        self._selected_tier_id = None
        self._selected_value = ""
        self._set_default_selection()
        self.selectionChanged.emit()

    @Slot(str)
    def selectAffixInstance(self, instance_id: str) -> None:
        instance = next((value for value in self._current_item.affixes if value.id == instance_id), None)
        if instance is None:
            return
        definition = self.catalog.affixes.get(instance.definition_id)
        if definition is None:
            self._set_notice("This affix is no longer in the local catalog, so it is read-only.", "error")
            return
        self._selected_group = instance.group
        self._selected_category = instance.category
        self._selected_instance_id = instance.id
        self._selected_definition_id = definition.id
        self._selected_tier_id = instance.tier_id
        self._selected_value = instance.value
        self.selectionChanged.emit()

    @Slot(str)
    def setTier(self, tier_id: str) -> None:
        definition = self._selected_definition()
        if definition is None:
            return
        tier = next((option for option in definition.tiers if option.id == tier_id), None)
        if tier is None:
            return
        if tier.item_level_required is not None and self._current_item.item_level < tier.item_level_required:
            self._set_notice(f"{tier.id} is listed from Item Level {tier.item_level_required}.", "error")
            return
        self._selected_tier_id = tier.id
        self._selected_value = tier.value_range
        self.selectionChanged.emit()

    @Slot(str)
    def setAffixValue(self, value: str) -> None:
        self._selected_value = value[:120]
        self.selectionChanged.emit()

    @Slot()
    def addOrUpdateAffix(self) -> None:
        definition = self._selected_definition()
        tier = self._selected_tier(definition)
        base = self._current_base()
        if definition is None or tier is None or base is None:
            self._set_notice("Choose an available affix and tier first.", "error")
            return
        if definition.base_ids and base.id not in definition.base_ids:
            self._set_notice("This affix is not listed for the selected base.", "error")
            return
        if tier.item_level_required is not None and self._current_item.item_level < tier.item_level_required:
            self._set_notice(f"{tier.id} requires Item Level {tier.item_level_required} in the current catalog.", "error")
            return
        value = self._selected_value.strip()
        if not value:
            self._set_notice("Enter a value for this affix.", "error")
            return
        if len(value) > 120:
            self._set_notice("Affix values must be 120 characters or fewer.", "error")
            return

        if self._definition_is_on_item(definition.id, self._selected_instance_id):
            self._set_notice(f"{definition.name} is already on this equipment.", "error")
            return

        if self._selected_instance_id:
            instance = next(
                (affix for affix in self._current_item.affixes if affix.id == self._selected_instance_id),
                None,
            )
            if instance is None:
                self._set_notice("Select an affix on the item to edit it.", "error")
                return
            if instance.group != definition.group:
                limit = base.prefix_limit if definition.group == AffixGroup.PREFIX else base.suffix_limit
                count = sum(1 for existing in self._current_item.affixes if existing.group == definition.group)
                if limit is not None and count >= limit:
                    self._set_notice(f"This base's screenshot-based {definition.group.value} limit is {limit}.", "error")
                    return
            instance.definition_id = definition.id
            instance.group = definition.group
            instance.category = definition.category
            instance.tier_id = tier.id
            instance.value = value
            instance.verification_status = definition.verification_status
            message = "Affix updated."
        else:
            limit = base.prefix_limit if definition.group == AffixGroup.PREFIX else base.suffix_limit
            count = sum(1 for existing in self._current_item.affixes if existing.group == definition.group)
            if limit is not None and count >= limit:
                self._set_notice(f"This base's screenshot-based {definition.group.value} limit is {limit}.", "error")
                return
            instance = AffixInstance.create(definition, tier, value)
            self._current_item.affixes.append(instance)
            self._selected_instance_id = instance.id
            message = "Affix added."

        self.affixesChanged.emit()
        self.selectionChanged.emit()
        self.stateChanged.emit()
        self._set_notice(message, "success")

    @Slot()
    def removeSelectedAffix(self) -> None:
        if not self._selected_instance_id:
            return
        before = len(self._current_item.affixes)
        self._current_item.affixes = [
            instance for instance in self._current_item.affixes if instance.id != self._selected_instance_id
        ]
        if len(self._current_item.affixes) == before:
            self._set_notice("That affix is no longer on this item.", "error")
            return
        self._selected_instance_id = None
        self._set_default_selection()
        self._emit_all()
        self._set_notice("Affix removed.", "success")

    @Slot()
    def saveCurrent(self) -> bool:
        return self._commit_current()

    @Slot()
    def requestNewItem(self) -> None:
        if self._dirty():
            self._pending_action = ("new", None)
            self.confirmUnsaved.emit()
            return
        self._start_new_item()

    @Slot(str)
    def requestOpenItem(self, item_id: str) -> None:
        if self._dirty():
            self._pending_action = ("open", item_id)
            self.confirmUnsaved.emit()
            return
        self._open_by_id(item_id)

    def _open_by_id(self, item_id: str) -> None:
        item = next((saved for saved in self._saved_items if saved.id == item_id), None)
        if item is None:
            self._refresh_saved_items()
            self._set_notice("That saved item could not be found.", "error")
            return
        self._load_item(item)

    @Slot(str)
    def requestDuplicateItem(self, item_id: str) -> None:
        if self._dirty():
            self._pending_action = ("duplicate", item_id)
            self.confirmUnsaved.emit()
            return
        self._pending_action = ("duplicate", item_id)
        self._continue_pending_action()

    @Slot(str)
    def resolveUnsaved(self, choice: str) -> None:
        if choice not in {"cancel", "discard", "save"}:
            return
        if choice == "cancel":
            self._pending_action = None
            return
        if choice == "save" and not self._commit_current():
            self._pending_action = None
            return
        self._continue_pending_action()

    @Slot()
    def requestClose(self) -> None:
        if self._dirty():
            self._pending_action = ("close", None)
            self.confirmUnsaved.emit()
        else:
            self.closeConfirmed.emit()

    @Slot(str, str)
    def renameSavedItem(self, item_id: str, name: str = "") -> None:
        item = next((saved for saved in self._saved_items if saved.id == item_id), None)
        if item is None:
            self._set_notice("That saved item could not be found.", "error")
            return
        clean_name = name.strip()[:80]
        if not clean_name:
            self._set_notice("Give this equipment a name.", "error")
            return
        item.name = clean_name
        try:
            self._saved_items = self.repository.save_item(item)
        except RepositoryError as exc:
            self._set_notice(str(exc), "error")
            self._refresh_saved_items(silent=True)
            return
        if self._current_item.id == item.id:
            self._current_item.name = clean_name
            if "name" in self._baseline:
                self._baseline["name"] = clean_name
            self.stateChanged.emit()
        self.savedItemsChanged.emit()
        self._set_notice("Saved equipment renamed.", "success")

    @Slot(str)
    def deleteSavedItem(self, item_id: str) -> None:
        try:
            self._saved_items = self.repository.delete_item(item_id)
        except RepositoryError as exc:
            self._set_notice(str(exc), "error")
            self._refresh_saved_items(silent=True)
            return
        if self._current_item.id == item_id:
            self._baseline = {}
        self.savedItemsChanged.emit()
        if self._current_item.id == item_id:
            self.stateChanged.emit()
            self._set_notice("Saved equipment deleted. The open copy remains in the editor as an unsaved item.", "warning")
        else:
            self._set_notice("Saved equipment deleted.", "success")

    @Slot()
    def refreshLibrary(self) -> None:
        self._refresh_saved_items()

    @Slot()
    def dismissNotice(self) -> None:
        if self._notice_text:
            self._notice_text = ""
            self.noticeChanged.emit()
