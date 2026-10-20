"""QML adapter for the session-only probabilistic standard crafting mode."""

from __future__ import annotations

from fractions import Fraction

from PySide6.QtCore import QObject, Property, Signal, Slot

from core.crafting import (
    MODEL_ID,
    CraftAction,
    CraftPool,
    CraftResult,
    CraftingError,
)
from core.models import AffixCategory, AffixGroup
from services.crafting_service import CraftingService
from services.item_editor_service import ItemEditorService


class CraftingViewModel(QObject):
    stateChanged = Signal()
    itemChanged = Signal()
    noticeRequested = Signal(str, str)

    def __init__(
        self,
        service: CraftingService,
        editor: ItemEditorService,
        browser,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.editor = editor
        self.browser = browser
        self._experimental_enabled = False
        self._category = AffixCategory.BASIC
        self._selected_family_id = ""
        self._pool: CraftPool | None = None
        self._preview_error = "Select a Prefix or Suffix slot on the item."
        self._history: list[CraftResult] = []
        self._last_result: CraftResult | None = None
        self.refresh_preview()

    @staticmethod
    def _percent(value: Fraction) -> str:
        return f"{float(value * 100):.4f}%  ({value.numerator}/{value.denominator})"

    def _action(self) -> CraftAction:
        try:
            group = AffixGroup(self.browser.selectedGroup)
        except ValueError:
            group = AffixGroup.PREFIX
        return CraftAction(
            group=group,
            slot_index=int(self.browser.selectedSlotIndex),
            category=self._category,
            model_id=MODEL_ID,
            experimental_opt_in=self._experimental_enabled,
        )

    def _target_summary(self) -> str:
        slot_index = int(self.browser.selectedSlotIndex)
        if slot_index < 0:
            return "Select a Prefix or Suffix slot on the item."
        group = str(self.browser.selectedGroup).title()
        group_affixes = [
            item for item in self.editor.item.affixes
            if item.group.value == str(self.browser.selectedGroup)
        ]
        operation = "Replace" if slot_index < len(group_affixes) else "Add"
        return f"{operation} {group} slot {slot_index + 1}"

    def refresh_preview(self) -> None:
        self._pool = None
        self._preview_error = self._target_summary()
        if int(self.browser.selectedSlotIndex) >= 0:
            try:
                self._pool = self.service.preview(self.editor.item, self._action())
                self._preview_error = (
                    "This exact source pool has no positive eligible weights; probabilities are unavailable."
                    if self._pool.total_weight <= 0
                    else ""
                )
            except CraftingError as exc:
                self._preview_error = str(exc)
        if self._pool:
            family_ids = (
                {entry.family_id for entry in self._pool.family_probabilities}
                if self._pool.total_weight > 0
                else {outcome.family_id for outcome in self._pool.outcomes}
            )
            if self._selected_family_id not in family_ids:
                self._selected_family_id = next(iter(family_ids), "")
        else:
            self._selected_family_id = ""
        self.stateChanged.emit()

    def _candidate_views(self) -> list[dict[str, object]]:
        if self._pool is None:
            return []
        tier_stats = {
            (row.family_id, row.tier_id): row for row in self._pool.tier_probabilities
        }
        outcomes_by_family: dict[str, list] = {}
        for outcome in self._pool.outcomes:
            outcomes_by_family.setdefault(outcome.family_id, []).append(outcome)
        result = []
        family_probabilities = {
            entry.family_id: entry for entry in self._pool.family_probabilities
        }
        family_names = {
            outcome.family_id: outcome.name for outcome in self._pool.outcomes
        }
        family_ids = sorted(family_names, key=lambda family_id: family_names[family_id].casefold())
        for family_id in family_ids:
            family = family_probabilities.get(family_id)
            tiers = outcomes_by_family.get(family_id, [])
            highest = next((tier for tier in tiers if tier.weight > 0), None)
            result.append({
                "familyId": family_id,
                "name": family_names[family_id],
                "chance": self._percent(family.probability) if family else "Unavailable",
                "familyWeight": family.total_weight if family else 0,
                "highestTier": highest.tier_label if highest else "No rollable tier",
                "highestRange": highest.value_range if highest else "",
                "selected": family_id == self._selected_family_id,
                "tiers": [
                    {
                        "tierId": outcome.tier_id,
                        "tierLabel": outcome.tier_label,
                        "range": outcome.value_range,
                        "weight": outcome.weight,
                        "jointChance": (
                            self._percent(tier_stats[(outcome.family_id, outcome.tier_id)].joint_probability)
                            if (outcome.family_id, outcome.tier_id) in tier_stats
                            else "Unavailable"
                        ),
                        "conditionalChance": (
                            self._percent(tier_stats[(outcome.family_id, outcome.tier_id)].conditional_probability)
                            if (outcome.family_id, outcome.tier_id) in tier_stats
                            else "Unavailable"
                        ),
                        "rollable": outcome.weight > 0,
                        "sourceUrl": outcome.source_url,
                        "sourceSection": outcome.source_section,
                        "sourceTable": outcome.source_table,
                        "sourceRowKey": outcome.source_row_key,
                    }
                    for outcome in tiers
                ],
            })
        return result

    @Property(bool, notify=stateChanged)
    def experimentalEnabled(self) -> bool:
        return self._experimental_enabled

    @Property(str, notify=stateChanged)
    def selectedCategory(self) -> str:
        return self._category.value

    @Property(str, notify=stateChanged)
    def selectedGroup(self) -> str:
        return str(self.browser.selectedGroup)

    @Property(int, notify=stateChanged)
    def selectedSlotIndex(self) -> int:
        return int(self.browser.selectedSlotIndex)

    @Property(str, notify=stateChanged)
    def operationLabel(self) -> str:
        return self._target_summary()

    @Property(str, notify=stateChanged)
    def poolMessage(self) -> str:
        return self._preview_error

    @Property(bool, notify=stateChanged)
    def poolAvailable(self) -> bool:
        return self._pool is not None and self._pool.total_weight > 0

    @Property(bool, notify=stateChanged)
    def poolConstructed(self) -> bool:
        return self._pool is not None

    @Property(bool, notify=stateChanged)
    def canCraft(self) -> bool:
        return self._experimental_enabled and self._pool is not None

    @Property(str, notify=stateChanged)
    def modelName(self) -> str:
        return "TLIDB Weighted · Experimental"

    @Property(str, notify=stateChanged)
    def ruleStatusSummary(self) -> str:
        return "Pool selection: verified · Eligibility/caps: source-derived · Replacement and weight rules: experimental · Numeric value roll: unknown"

    @Property("QVariantList", notify=stateChanged)
    def ruleEvidence(self) -> list[dict[str, object]]:
        rules = self._pool.rule_evidence if self._pool else ()
        return [
            {
                "id": rule.id,
                "status": rule.status.value,
                "description": rule.description,
                "sources": list(rule.sources),
            }
            for rule in rules
        ]

    @Property(str, notify=stateChanged)
    def baseName(self) -> str:
        base = self.editor.catalog.bases.get(self.editor.item.base_id)
        return base.name if base else "Unknown base"

    @Property(int, notify=stateChanged)
    def itemLevel(self) -> int:
        return self.editor.item.item_level

    @Property(str, notify=stateChanged)
    def poolId(self) -> str:
        return self._pool.pool_id if self._pool else "—"

    @Property(int, notify=stateChanged)
    def familyCount(self) -> int:
        return self._pool.family_count if self._pool else 0

    @Property(int, notify=stateChanged)
    def rollableOutcomeCount(self) -> int:
        return self._pool.rollable_count if self._pool else 0

    @Property(int, notify=stateChanged)
    def totalWeight(self) -> int:
        return self._pool.total_weight if self._pool else 0

    @Property(str, notify=stateChanged)
    def slotEvidenceText(self) -> str:
        if not self._pool:
            return ""
        if self._pool.slot_limit_status == "visual_example_only":
            return "Slot capacity from the supplied screenshot · unverified"
        if self._pool.slot_limit_status == "unknown":
            return "Slot capacity unknown"
        if self._pool.slot_limit_status == "source_derived":
            return "Slot capacity source-derived · not officially verified"
        return "Slot capacity listed in the catalog"

    @Property("QVariantList", notify=stateChanged)
    def candidates(self) -> list[dict[str, object]]:
        return self._candidate_views()

    @Property("QVariantList", notify=stateChanged)
    def selectedTiers(self) -> list[dict[str, object]]:
        return next(
            (row["tiers"] for row in self.candidates if row["familyId"] == self._selected_family_id),
            [],
        )

    @Property(str, notify=stateChanged)
    def selectedFamilyName(self) -> str:
        return next(
            (str(row["name"]) for row in self.candidates if row["familyId"] == self._selected_family_id),
            "Select a possible family to inspect tier chances",
        )

    @Property(str, notify=stateChanged)
    def lastResultText(self) -> str:
        if self._last_result is None:
            return "No craft attempts in this session."
        if not self._last_result.success or self._last_result.outcome is None:
            return self._last_result.reason
        action = self._last_result.action
        operation = "replaced" if self._last_result.replaced_instance_id else "added"
        outcome = self._last_result.outcome
        result_name = outcome.name
        if self._last_result.replaced_instance_id:
            previous = next(
                (
                    instance for instance in self._last_result.before_item.affixes
                    if instance.id == self._last_result.replaced_instance_id
                ),
                None,
            )
            previous_definition = (
                self.editor.catalog.affixes.get(previous.definition_id) if previous else None
            )
            previous_name = previous_definition.name if previous_definition else "Unknown affix"
            result_name = f"{previous_name} → {outcome.name}"
        seed = f" Seed: {self._last_result.seed_used}." if self._last_result.seed_used is not None else ""
        return f"{result_name} · {outcome.tier_label} {operation} in {action.group.value.title()} slot {action.slot_index + 1}. Value range: {outcome.value_range} (numeric roll not simulated).{seed}"

    @Property(bool, notify=stateChanged)
    def canUndo(self) -> bool:
        return bool(self._history)

    @Property(int, notify=stateChanged)
    def historyCount(self) -> int:
        return len(self._history)

    @Property("QVariantList", notify=stateChanged)
    def history(self) -> list[dict[str, object]]:
        return [
            {
                "name": result.outcome.name if result.outcome else "Craft attempt",
                "tier": result.outcome.tier_label if result.outcome else "",
                "operation": "Replace" if result.replaced_instance_id else "Add",
                "valueRange": result.outcome.value_range if result.outcome else "",
            }
            for result in reversed(self._history)
        ]

    @Slot(bool)
    def setExperimentalEnabled(self, enabled: bool) -> None:
        if self._experimental_enabled != enabled:
            self._experimental_enabled = enabled
            self.refresh_preview()

    @Slot(str)
    def setCategory(self, category: str) -> None:
        try:
            selected = AffixCategory(category)
        except ValueError:
            return
        if selected != self._category:
            self._category = selected
            self._selected_family_id = ""
            self.refresh_preview()

    @Slot(str)
    def selectFamily(self, family_id: str) -> None:
        if any(row["familyId"] == family_id for row in self.candidates):
            self._selected_family_id = family_id
            self.stateChanged.emit()

    @Slot()
    def craftOnce(self) -> None:
        if not self._experimental_enabled:
            self.noticeRequested.emit("Enable the experimental weighted model before crafting.", "error")
            return
        action = self._action()
        result = self.service.attempt(self.editor.item, action)
        self._last_result = result
        if not result.success:
            self.noticeRequested.emit(result.reason, "error")
            self.stateChanged.emit()
            return
        self.editor.apply_crafted_state(result.after_item)
        self._history.append(result)
        self.service.invalidate()
        target = [
            instance for instance in result.after_item.affixes
            if instance.group == action.group
        ][action.slot_index]
        self.browser.selectCraftedInstance(target.id)
        self.refresh_preview()
        self.itemChanged.emit()
        self.noticeRequested.emit(result.reason, "success")

    @Slot()
    def undoLast(self) -> None:
        if not self._history:
            return
        result = self._history.pop()
        self.editor.apply_crafted_state(result.before_item)
        self.service.invalidate()
        if result.replaced_instance_id:
            self.browser.selectCraftedInstance(result.replaced_instance_id)
        else:
            self.browser.selectCraftTarget(
                result.action.group.value, result.action.slot_index, ""
            )
        self._last_result = self._history[-1] if self._history else None
        self.refresh_preview()
        self.itemChanged.emit()
        self.noticeRequested.emit("Last craft attempt undone.", "info")

    @Slot()
    def invalidateHistory(self) -> None:
        if self._history:
            self._history.clear()
            self._last_result = None
            self.stateChanged.emit()

    @Slot()
    def refreshPreview(self) -> None:
        self.refresh_preview()
