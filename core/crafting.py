"""Pure, session-only standard crafting rules and experimental weighted draws.

The official game source confirms random selection from a selected pool, but
does not establish that TLIDB's listed weights are the live game odds. This
module therefore exposes those weights only through an explicit experimental
model and keeps its probabilities exact and reproducible.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Protocol

from core.catalog import Catalog
from core.models import (
    AffixCategory,
    AffixDefinition,
    AffixGroup,
    AffixInstance,
    EquipmentItem,
    MAX_ITEM_LEVEL,
    MIN_ITEM_LEVEL,
    resolve_tier_reference,
)


MODEL_ID = "tlidb-weighted-experimental"
STANDARD_CRAFT_SYSTEM = "tlidb:standard-craft"
ADVANCED_LIMIT = 2
ULTIMATE_LIMIT = 2


class RuleStatus(StrEnum):
    VERIFIED = "verified"
    SOURCE_DERIVED = "source_derived"
    EXPERIMENTAL = "experimental"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RuleEvidence:
    id: str
    status: RuleStatus
    description: str
    sources: tuple[str, ...] = ()


CRAFT_RULES = (
    RuleEvidence(
        "chosen-pool-random-selection",
        RuleStatus.VERIFIED,
        "The official SS14 source describes random selection from a chosen pool.",
        ("https://torchlight.xd.com/us/news/single?id=nezvlurrIS2B",),
    ),
    RuleEvidence(
        "category-group-and-base-pools",
        RuleStatus.SOURCE_DERIVED,
        "Catalog compatibility, exact pool, Prefix/Suffix, and Basic/Advanced/Ultimate boundaries.",
        ("https://tlidb.com/en/Craft",),
    ),
    RuleEvidence(
        "catalog-slot-capacity",
        RuleStatus.SOURCE_DERIVED,
        "Only listed empty slots can be added to; unknown capacity blocks additions.",
        ("https://tlidb.com/en/Craft",),
    ),
    RuleEvidence(
        "tier-item-level-requirement",
        RuleStatus.SOURCE_DERIVED,
        "The imported tier Item Level requirement filters eligible outcomes.",
        ("https://tlidb.com/en/",),
    ),
    RuleEvidence(
        "ultimate-priceless-and-category-caps",
        RuleStatus.SOURCE_DERIVED,
        "Ultimate requires Priceless; at most two Advanced and two Ultimate affixes per item.",
        ("https://tlidb.com/en/Craft", "https://tlidb.com/en/Priceless"),
    ),
    RuleEvidence(
        "existing-family-and-replacement-target-policy",
        RuleStatus.EXPERIMENTAL,
        "Existing semantic families are excluded, with the selected replacement target removed from that check.",
        ("user-provided crafting screenshot",),
    ),
    RuleEvidence(
        "category-crossing-replacement-policy",
        RuleStatus.EXPERIMENTAL,
        "The selected slot may be replaced from another selected category; caps count the post-replacement item.",
        (),
    ),
    RuleEvidence(
        "zero-weight-tier-rows",
        RuleStatus.SOURCE_DERIVED,
        "Imported zero weights remain visible and are excluded from this positive-weight sampler.",
        ("https://tlidb.com/en/",),
    ),
    RuleEvidence(
        "flat-tlidb-weighted-family-tier-draw",
        RuleStatus.EXPERIMENTAL,
        "Each eligible family-tier row is sampled proportionally to its TLIDB integer weight.",
        ("https://tlidb.com/en/Craft",),
    ),
    RuleEvidence(
        "numeric-value-roll-within-tier",
        RuleStatus.UNKNOWN,
        "The distribution for a numeric value within a tier range is not established; the engine does not roll it.",
        (),
    ),
    RuleEvidence(
        "in-game-attempt-failure-and-material-cost",
        RuleStatus.UNKNOWN,
        "The local model does not predict game-side failures or consume materials.",
        ("https://tlidb.com/en/Craft",),
    ),
)


class CraftingError(ValueError):
    """A craft cannot proceed with the selected item, slot, or source data."""


class WeightedRandomizer(Protocol):
    def randrange(self, stop: int) -> int: ...


@dataclass(frozen=True, slots=True)
class CraftAction:
    """One attempt at the currently selected prefix or suffix slot."""

    group: AffixGroup
    slot_index: int
    category: AffixCategory
    model_id: str = MODEL_ID
    experimental_opt_in: bool = False
    seed: int | None = None


@dataclass(frozen=True, slots=True)
class CraftOutcome:
    """A family-tier source row; it is a possible result, not a target."""

    family_id: str
    pool_id: str
    name: str
    group: AffixGroup
    category: AffixCategory
    tier_id: str
    tier_label: str
    value_range: str
    required_item_level: int
    weight: int
    verification_status: str
    source_url: str
    source_section: str
    source_table: str
    source_row_key: str


@dataclass(frozen=True, slots=True)
class FamilyProbability:
    family_id: str
    name: str
    total_weight: int
    probability: Fraction


@dataclass(frozen=True, slots=True)
class TierProbability:
    family_id: str
    tier_id: str
    tier_label: str
    weight: int
    joint_probability: Fraction
    conditional_probability: Fraction


@dataclass(frozen=True, slots=True)
class CraftPool:
    """Eligible family-tier rows, retaining zero-weight rows for inspection."""

    pool_id: str
    group: AffixGroup
    category: AffixCategory
    item_level: int
    base_id: str
    slot_limit_status: str
    outcomes: tuple[CraftOutcome, ...]
    total_weight: int
    rule_evidence: tuple[RuleEvidence, ...] = CRAFT_RULES

    @property
    def rollable_count(self) -> int:
        return sum(outcome.weight > 0 for outcome in self.outcomes)

    @property
    def family_count(self) -> int:
        return len({outcome.family_id for outcome in self.outcomes})

    @property
    def family_probabilities(self) -> tuple[FamilyProbability, ...]:
        if self.total_weight <= 0:
            return ()
        totals: dict[str, tuple[str, int]] = {}
        for outcome in self.outcomes:
            name, weight = totals.get(outcome.family_id, (outcome.name, 0))
            totals[outcome.family_id] = (name, weight + outcome.weight)
        return tuple(
            FamilyProbability(family_id, name, weight, Fraction(weight, self.total_weight))
            for family_id, (name, weight) in sorted(totals.items(), key=lambda row: row[1][0].casefold())
        )

    @property
    def tier_probabilities(self) -> tuple[TierProbability, ...]:
        if self.total_weight <= 0:
            return ()
        family_weights: dict[str, int] = {}
        for outcome in self.outcomes:
            family_weights[outcome.family_id] = family_weights.get(outcome.family_id, 0) + outcome.weight
        return tuple(
            TierProbability(
                family_id=outcome.family_id,
                tier_id=outcome.tier_id,
                tier_label=outcome.tier_label,
                weight=outcome.weight,
                joint_probability=Fraction(outcome.weight, self.total_weight),
                conditional_probability=(
                    Fraction(outcome.weight, family_weights[outcome.family_id])
                    if family_weights[outcome.family_id]
                    else Fraction(0, 1)
                ),
            )
            for outcome in self.outcomes
        )


@dataclass(frozen=True, slots=True)
class CraftResult:
    """Immutable attempt record; item snapshots are canonical schema-v1 JSON."""

    success: bool
    reason: str
    model_id: str
    before_item_json: str
    after_item_json: str
    action: CraftAction
    pool: CraftPool | None = None
    outcome: CraftOutcome | None = None
    replaced_instance_id: str = ""
    draw_ticket: int | None = None
    draw_total: int = 0
    seed_used: int | None = None
    value_roll_simulated: bool = False

    @property
    def before_item(self) -> EquipmentItem:
        return EquipmentItem.from_dict(json.loads(self.before_item_json))

    @property
    def after_item(self) -> EquipmentItem:
        return EquipmentItem.from_dict(json.loads(self.after_item_json))


def _snapshot(item: EquipmentItem) -> str:
    return json.dumps(item.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _family_identity(definition: AffixDefinition) -> str:
    if definition.is_legacy_alias:
        return f"legacy:{definition.id}"
    if definition.semantic_signature:
        return f"{definition.source_id}:{definition.semantic_signature}"
    return definition.id


def _existing_family_identities(
    item: EquipmentItem, affixes: dict[str, AffixDefinition], excluding: str | None
) -> set[str]:
    result: set[str] = set()
    for instance in item.affixes:
        if instance.id == excluding:
            continue
        definition = affixes.get(instance.definition_id)
        if definition is None:
            # Unknown existing affixes are conservatively treated as occupying
            # an identity. They cannot be safely matched to a new outcome.
            result.add(f"unknown:{instance.definition_id}")
            continue
        if definition.is_legacy_alias and definition.legacy_family_member_ids:
            tier, ambiguous = resolve_tier_reference(definition.tiers, instance.tier_id)
            if not ambiguous and tier:
                matching = [
                    member_id
                    for member_id in definition.legacy_family_member_ids
                    if member_id in affixes
                    and any(option.id == tier.id for option in affixes[member_id].tiers)
                ]
                if len(matching) == 1:
                    result.add(_family_identity(affixes[matching[0]]))
                    continue
            result.update(
                _family_identity(affixes[member_id])
                for member_id in definition.legacy_family_member_ids
                if member_id in affixes
            )
            continue
        result.add(_family_identity(definition))
    return result


def _source_weight(outcome: CraftOutcome, tier_status: str, weight_raw: str | None) -> int:
    if tier_status != "parsed_integer" or not isinstance(weight_raw, str):
        raise CraftingError(
            f"Weight is missing or unparsed for {outcome.name} {outcome.tier_label}; crafting is blocked."
        )
    raw = weight_raw.strip()
    if not re.fullmatch(r"-?\d+", raw):
        raise CraftingError(
            f"Weight '{weight_raw}' is not an integer for {outcome.name} {outcome.tier_label}; crafting is blocked."
        )
    weight = int(raw)
    if weight < 0:
        raise CraftingError(
            f"Negative weight for {outcome.name} {outcome.tier_label}; crafting is blocked."
        )
    return weight


class CraftingEngine:
    """Build auditable eligible pools and make one weighted standard attempt."""

    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog

    def build_pool(self, item: EquipmentItem, action: CraftAction) -> CraftPool:
        if action.model_id != MODEL_ID:
            raise CraftingError("Unknown crafting probability model.")
        if not action.experimental_opt_in:
            raise CraftingError("Enable the experimental TLIDB weighted model before crafting.")
        if not isinstance(action.group, AffixGroup) or not isinstance(action.category, AffixCategory):
            raise CraftingError("Choose a supported Prefix/Suffix group and craft category.")
        if (
            isinstance(action.slot_index, bool)
            or not isinstance(action.slot_index, int)
            or action.slot_index < 0
        ):
            raise CraftingError("Select a valid Prefix or Suffix slot on the item.")
        if isinstance(item.item_level, bool) or not isinstance(item.item_level, int):
            raise CraftingError("Item Level must be a whole number before crafting.")
        if not MIN_ITEM_LEVEL <= item.item_level <= MAX_ITEM_LEVEL:
            raise CraftingError(
                f"Item Level must be between {MIN_ITEM_LEVEL} and {MAX_ITEM_LEVEL} before crafting."
            )
        if not isinstance(item.priceless, bool):
            raise CraftingError("Priceless state is missing or invalid.")
        if action.seed is not None and (isinstance(action.seed, bool) or not isinstance(action.seed, int)):
            raise CraftingError("Craft seed must be an integer.")

        base = self.catalog.bases.get(item.base_id)
        if base is None:
            raise CraftingError("The selected base is not in the local catalog.")
        if (
            base.crafting_class != "standard_craftable"
            or base.record_kind != "base"
            or not base.editor_supported
        ):
            raise CraftingError("Only catalog-listed standard-craftable bases are supported.")
        if base.minimum_item_level is not None and item.item_level < base.minimum_item_level:
            raise CraftingError(f"This base requires Item Level {base.minimum_item_level}.")

        group_items = [affix for affix in item.affixes if affix.group == action.group]
        target = group_items[action.slot_index] if action.slot_index < len(group_items) else None
        if target is None:
            limit = base.prefix_limit if action.group == AffixGroup.PREFIX else base.suffix_limit
            if limit is None or base.limit_status not in {
                "catalog_listed", "verified", "source_derived", "visual_example_only"
            }:
                raise CraftingError("This base has no verified empty slot limit; adding is blocked.")
            if action.slot_index != len(group_items) or action.slot_index >= limit:
                raise CraftingError("Select an occupied slot to replace or the next catalog-listed empty slot.")

        instance_ids = [instance.id for instance in item.affixes]
        if len(instance_ids) != len(set(instance_ids)):
            raise CraftingError("Equipment contains duplicate affix instance IDs; resolve them before crafting.")

        for instance in item.affixes:
            if instance.id == (target.id if target else ""):
                continue
            definition = self.catalog.affixes.get(instance.definition_id)
            if definition is None:
                raise CraftingError("Resolve affixes missing from the local catalog before crafting.")
            if definition.base_ids and base.id not in definition.base_ids:
                raise CraftingError(
                    f"Resolve the incompatible {definition.name} affix before crafting."
                )
            if definition.group != instance.group or definition.category != instance.category:
                raise CraftingError(
                    f"Resolve the invalid group or category on {definition.name} before crafting."
                )
            tier, ambiguous_tier = resolve_tier_reference(definition.tiers, instance.tier_id)
            if tier is None or ambiguous_tier or tier.item_level_required is None:
                raise CraftingError(
                    f"Resolve the unsupported or ambiguous tier on {definition.name} before crafting."
                )
            if item.item_level < tier.item_level_required:
                raise CraftingError(
                    f"Resolve {definition.name} {tier.tier_label}, which requires Item Level {tier.item_level_required}, before crafting."
                )

        if action.category == AffixCategory.ULTIMATE and not item.priceless:
            raise CraftingError("Ultimate affixes require the item to be marked Priceless.")

        category_count = sum(
            1 for instance in item.affixes
            if instance.category == action.category and (target is None or instance.id != target.id)
        )
        cap = ADVANCED_LIMIT if action.category == AffixCategory.ADVANCED else ULTIMATE_LIMIT
        if action.category in {AffixCategory.ADVANCED, AffixCategory.ULTIMATE} and category_count >= cap:
            raise CraftingError(
                f"This item already has the source-derived maximum of {cap} {action.category.value} affixes."
            )

        existing_families = _existing_family_identities(
            item, self.catalog.affixes, target.id if target else None
        )
        candidates = [
            definition
            for definition in self.catalog.affixes.values()
            if not definition.is_legacy_alias
            and definition.pool_id
            and definition.crafting_system_id == STANDARD_CRAFT_SYSTEM
            and definition.source_id == base.source_id
            and base.id in definition.base_ids
            and definition.group == action.group
            and definition.category == action.category
            and _family_identity(definition) not in existing_families
        ]
        candidate_family_ids = [_family_identity(definition) for definition in candidates]
        if len(candidate_family_ids) != len(set(candidate_family_ids)):
            raise CraftingError(
                "Catalog has repeated semantic family rows in this pool; crafting is blocked."
            )
        pool_ids = {definition.pool_id for definition in candidates}
        if not pool_ids:
            raise CraftingError("No source-listed outcomes match this base, slot, and craft category.")
        if len(pool_ids) != 1:
            raise CraftingError("Catalog definitions cross exact pool boundaries; crafting is blocked.")
        pool_id = next(iter(pool_ids))

        outcomes: list[CraftOutcome] = []
        for definition in sorted(candidates, key=lambda entry: (entry.name.casefold(), entry.id)):
            for tier in definition.tiers:
                if tier.item_level_required is None:
                    raise CraftingError(
                        f"Item Level requirement is unknown for {definition.name} {tier.tier_label}; crafting is blocked."
                    )
                if item.item_level < tier.item_level_required:
                    continue
                outcome = CraftOutcome(
                    family_id=definition.id,
                    pool_id=definition.pool_id,
                    name=definition.name,
                    group=definition.group,
                    category=definition.category,
                    tier_id=tier.id,
                    tier_label=tier.tier_label,
                    value_range=tier.value_range,
                    required_item_level=tier.item_level_required,
                    weight=0,
                    verification_status=tier.verification_status,
                    source_url=tier.source_url,
                    source_section=tier.source_section,
                    source_table=tier.source_table,
                    source_row_key=tier.source_row_key,
                )
                weight = _source_weight(outcome, tier.weight_parse_status, tier.weight_raw)
                outcomes.append(
                    CraftOutcome(
                        family_id=outcome.family_id,
                        pool_id=outcome.pool_id,
                        name=outcome.name,
                        group=outcome.group,
                        category=outcome.category,
                        tier_id=outcome.tier_id,
                        tier_label=outcome.tier_label,
                        value_range=outcome.value_range,
                        required_item_level=outcome.required_item_level,
                        weight=weight,
                        verification_status=outcome.verification_status,
                        source_url=outcome.source_url,
                        source_section=outcome.source_section,
                        source_table=outcome.source_table,
                        source_row_key=outcome.source_row_key,
                    )
                )
        total = sum(outcome.weight for outcome in outcomes)
        return CraftPool(
            pool_id=pool_id,
            group=action.group,
            category=action.category,
            item_level=item.item_level,
            base_id=base.id,
            slot_limit_status=base.limit_status,
            outcomes=tuple(outcomes),
            total_weight=total,
            rule_evidence=CRAFT_RULES,
        )

    def attempt(
        self,
        item: EquipmentItem,
        action: CraftAction,
        *,
        randomizer: WeightedRandomizer | None = None,
    ) -> CraftResult:
        before_json = _snapshot(item)
        seed_used: int | None = action.seed if randomizer is None else None
        try:
            pool = self.build_pool(item, action)
            if pool.total_weight <= 0:
                raise CraftingError(
                    "This exact source pool has no positive eligible weights at this Item Level."
                )
            if randomizer is None and seed_used is None:
                seed_used = random.SystemRandom().getrandbits(64)
            picker = randomizer if randomizer is not None else random.Random(seed_used)
            ticket = picker.randrange(pool.total_weight)
            cursor = 0
            selected: CraftOutcome | None = None
            for outcome in pool.outcomes:
                if outcome.weight <= 0:
                    continue
                cursor += outcome.weight
                if ticket < cursor:
                    selected = outcome
                    break
            if selected is None:
                raise CraftingError("Weighted draw returned a ticket outside the source pool.")

            after = EquipmentItem.from_dict(json.loads(before_json))
            definition = self.catalog.affixes[selected.family_id]
            tier = next(option for option in definition.tiers if option.id == selected.tier_id)
            instance = AffixInstance.create(definition, tier, selected.value_range)
            group_items = [affix for affix in after.affixes if affix.group == action.group]
            target = group_items[action.slot_index] if action.slot_index < len(group_items) else None
            replaced_id = ""
            if target is not None:
                replaced_id = target.id
                instance.id = target.id
                position = next(index for index, affix in enumerate(after.affixes) if affix.id == target.id)
                after.affixes[position] = instance
            else:
                # Insert into the group-relative slot while preserving the
                # order and identity of every other affix.
                group_positions = [
                    index for index, affix in enumerate(after.affixes)
                    if affix.group == action.group
                ]
                if action.slot_index < len(group_positions):
                    after.affixes.insert(group_positions[action.slot_index], instance)
                else:
                    after.affixes.append(instance)
            return CraftResult(
                success=True,
                reason="One experimental TLIDB-weighted draw completed; numeric value roll was not simulated.",
                model_id=action.model_id,
                before_item_json=before_json,
                after_item_json=_snapshot(after),
                action=action,
                pool=pool,
                outcome=selected,
                replaced_instance_id=replaced_id,
                draw_ticket=ticket,
                draw_total=pool.total_weight,
                seed_used=seed_used,
                value_roll_simulated=False,
            )
        except (CraftingError, KeyError, StopIteration, ValueError) as exc:
            return CraftResult(
                success=False,
                reason=str(exc),
                model_id=action.model_id,
                before_item_json=before_json,
                after_item_json=before_json,
                action=action,
                seed_used=seed_used,
            )
