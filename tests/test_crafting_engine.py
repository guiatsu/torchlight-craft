from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import random

import pytest

from core.catalog import Catalog, load_catalog
from core.crafting import CraftAction, CraftingEngine, MODEL_ID, RuleStatus
from core.models import (
    AffixCategory,
    AffixDefinition,
    AffixGroup,
    AffixInstance,
    BaseDefinition,
    EquipmentItem,
    TierOption,
)


class FixedRandomizer:
    def __init__(self, ticket: int) -> None:
        self.ticket = ticket
        self.stop = None

    def randrange(self, stop: int) -> int:
        self.stop = stop
        assert 0 <= self.ticket < stop
        return self.ticket


def _base(*, prefix_limit: int | None = 3, suffix_limit: int | None = 3) -> BaseDefinition:
    return BaseDefinition(
        id="test-base",
        name="Test Base",
        category="Test",
        subcategory="Test Type",
        equipment_type="Test item",
        hands=1,
        character_level_requirement=None,
        minimum_item_level=1,
        prefix_limit=prefix_limit,
        suffix_limit=suffix_limit,
        limit_status="catalog_listed" if prefix_limit is not None else "unknown",
        source_id="test-category",
        crafting_class="standard_craftable",
        record_kind="base",
        editor_supported=True,
    )


def _definition(
    family_id: str,
    *weights: str | None,
    category: AffixCategory = AffixCategory.BASIC,
    group: AffixGroup = AffixGroup.PREFIX,
    pool_id: str = "test-pool",
    requirements: tuple[int, ...] | None = None,
    parse_status: str = "parsed_integer",
    source_family_id: str | None = None,
) -> AffixDefinition:
    requirements = requirements or tuple(1 for _ in weights)
    tiers = tuple(
        TierOption(
            id=f"{family_id}:tier:{index}",
            item_level_required=requirement,
            value_range=f"Range {index}",
            tier_label=f"T{index + 1}",
            weight_raw=weight,
            weight_parse_status=parse_status,
        )
        for index, (weight, requirement) in enumerate(zip(weights, requirements, strict=True))
    )
    return AffixDefinition(
        id=family_id,
        name=family_id,
        group=group,
        category=category,
        base_ids=("test-base",),
        tiers=tiers,
        value_editable=True,
        source_id="test-category",
        source_family_id=source_family_id or family_id,
        family_grouping_status="source_family_id",
        crafting_system_id="tlidb:standard-craft",
        pool_id=pool_id,
    )


def _synthetic_catalog(
    *definitions: AffixDefinition,
    base: BaseDefinition | None = None,
) -> Catalog:
    selected_base = base or _base()
    return Catalog(
        bases={selected_base.id: selected_base},
        affixes={definition.id: definition for definition in definitions},
        sources={},
    )


def _action(
    *,
    index: int = 0,
    group: AffixGroup = AffixGroup.PREFIX,
    category: AffixCategory = AffixCategory.BASIC,
    seed: int | None = 1,
    opted_in: bool = True,
) -> CraftAction:
    return CraftAction(
        group=group,
        slot_index=index,
        category=category,
        model_id=MODEL_ID,
        experimental_opt_in=opted_in,
        seed=seed,
    )


def _item(*, priceless: bool = False, level: int = 50) -> EquipmentItem:
    return EquipmentItem(
        id="equipment-1",
        name="Test Base",
        base_id="test-base",
        item_level=level,
        priceless=priceless,
    )


def test_exact_family_and_tier_probabilities_keep_zero_weight_rows_visible() -> None:
    cold = _definition("Cold", "0", "1")
    fire = _definition("Fire", "3")
    engine = CraftingEngine(_synthetic_catalog(cold, fire))
    pool = engine.build_pool(_item(), _action())

    assert [(row.tier_label, row.weight) for row in pool.outcomes if row.family_id == "Cold"] == [
        ("T1", 0),
        ("T2", 1),
    ]
    families = {row.family_id: row.probability for row in pool.family_probabilities}
    assert families == {"Cold": Fraction(1, 4), "Fire": Fraction(3, 4)}
    tiers = {(row.family_id, row.tier_label): row for row in pool.tier_probabilities}
    assert tiers[("Cold", "T1")].joint_probability == 0
    assert tiers[("Cold", "T1")].conditional_probability == 0
    assert tiers[("Cold", "T2")].joint_probability == Fraction(1, 4)
    assert tiers[("Cold", "T2")].conditional_probability == 1
    assert sum(row.probability for row in pool.family_probabilities) == 1
    assert sum(row.joint_probability for row in pool.tier_probabilities) == 1
    assert {entry.status for entry in pool.rule_evidence} == set(RuleStatus)


def test_weighted_draw_uses_ticket_boundaries_and_never_draws_zero_weight() -> None:
    zero_and_positive = _definition("A", "0", "1")
    heavier = _definition("B", "3")
    engine = CraftingEngine(_synthetic_catalog(zero_and_positive, heavier))

    first = engine.attempt(_item(), _action(), randomizer=FixedRandomizer(0))
    second = engine.attempt(_item(), _action(), randomizer=FixedRandomizer(1))
    assert first.success and first.outcome is not None
    assert (first.outcome.family_id, first.outcome.tier_label) == ("A", "T2")
    assert second.success and second.outcome is not None
    assert second.outcome.family_id == "B"
    assert first.draw_total == 4
    assert second.draw_total == 4
    assert set(first.after_item.to_dict()) == {
        "id", "name", "base_id", "item_level", "priceless", "rarity", "affixes"
    }


@pytest.mark.parametrize(
    ("weight", "status"),
    [(None, "parsed_integer"), ("1.5", "parsed_integer"), ("-1", "parsed_integer"), ("1", "missing")],
)
def test_missing_malformed_or_negative_weights_fail_without_mutation(weight, status) -> None:
    definition = _definition("Bad", weight, parse_status=status)
    catalog = _synthetic_catalog(definition)
    engine = CraftingEngine(catalog)
    item = _item()
    before = item.to_dict()

    result = engine.attempt(item, _action())

    assert not result.success
    assert result.after_item_json == result.before_item_json
    assert item.to_dict() == before
    assert any(word in result.reason for word in ("missing", "unparsed", "integer", "Negative"))


def test_zero_total_pool_is_blocked_and_input_remains_unchanged() -> None:
    definition = _definition("Never", "0", "0")
    catalog = _synthetic_catalog(definition)
    engine = CraftingEngine(catalog)
    item = _item()
    pool = engine.build_pool(item, _action())
    result = engine.attempt(item, _action())
    assert not result.success
    assert "no positive eligible weights" in result.reason
    assert len(pool.outcomes) == 2
    assert pool.total_weight == 0
    assert result.before_item_json == result.after_item_json
    assert item.affixes == []


def test_seeded_draw_is_reproducible_and_result_is_immutable() -> None:
    definitions = (_definition("A", "1"), _definition("B", "3"))
    engine = CraftingEngine(_synthetic_catalog(*definitions))
    action = _action(seed=90210)
    left = engine.attempt(_item(), action)
    right = engine.attempt(_item(), action)
    assert left.outcome == right.outcome
    assert left.draw_ticket == right.draw_ticket
    assert left.seed_used == 90210
    with pytest.raises(FrozenInstanceError):
        left.success = False


def test_item_level_filter_excludes_higher_tiers_before_weight_validation() -> None:
    definition = _definition("Level", "bad", "4", requirements=(100, 1))
    pool = CraftingEngine(_synthetic_catalog(definition)).build_pool(_item(level=50), _action())
    assert [row.tier_label for row in pool.outcomes] == ["T2"]
    assert pool.total_weight == 4


def test_add_requires_catalog_slot_and_priceless_for_ultimate() -> None:
    definition = _definition("Ultimate", "5", category=AffixCategory.ULTIMATE)
    engine = CraftingEngine(_synthetic_catalog(definition))
    blocked = engine.attempt(
        _item(priceless=False),
        _action(category=AffixCategory.ULTIMATE),
    )
    allowed = engine.attempt(
        _item(priceless=True),
        _action(category=AffixCategory.ULTIMATE),
    )
    unknown_limit = CraftingEngine(
        _synthetic_catalog(definition, base=_base(prefix_limit=None))
    ).attempt(_item(priceless=True), _action(category=AffixCategory.ULTIMATE))
    unverified_numeric_limit = CraftingEngine(
        _synthetic_catalog(
            definition,
            base=replace(_base(prefix_limit=3), limit_status="unknown"),
        )
    ).attempt(_item(priceless=True), _action(category=AffixCategory.ULTIMATE))
    assert not blocked.success and "Priceless" in blocked.reason
    assert allowed.success
    assert not unknown_limit.success and "limit" in unknown_limit.reason
    assert not unverified_numeric_limit.success and "limit" in unverified_numeric_limit.reason


@pytest.mark.parametrize(
    ("category", "priceless"),
    [(AffixCategory.ADVANCED, False), (AffixCategory.ULTIMATE, True)],
)
def test_category_caps_block_third_advanced_or_ultimate_but_allow_replacement(
    category, priceless
) -> None:
    definitions = [
        _definition(f"Tiered{index}", "1", category=category)
        for index in range(4)
    ]
    catalog = _synthetic_catalog(*definitions)
    item = _item(priceless=priceless)
    item.affixes = [
        AffixInstance.create(definitions[0], definitions[0].tiers[0]),
        AffixInstance.create(definitions[1], definitions[1].tiers[0]),
    ]
    engine = CraftingEngine(catalog)

    blocked = engine.attempt(item, _action(index=2, category=category))
    replacement = engine.attempt(
        item,
        _action(index=1, category=category),
        randomizer=FixedRandomizer(0),
    )
    assert not blocked.success and "maximum of 2" in blocked.reason
    assert replacement.success and replacement.replaced_instance_id == item.affixes[1].id
    assert replacement.after_item.affixes[1].id == item.affixes[1].id


def test_cross_group_selection_adds_only_to_selected_group() -> None:
    prefix = _definition("Prefix", "1")
    suffix = _definition("Suffix", "1", group=AffixGroup.SUFFIX, pool_id="suffix-pool")
    catalog = _synthetic_catalog(prefix, suffix)
    item = _item()
    item.affixes = [AffixInstance.create(prefix, prefix.tiers[0])]

    result = CraftingEngine(catalog).attempt(
        item,
        _action(group=AffixGroup.SUFFIX),
        randomizer=FixedRandomizer(0),
    )

    assert result.success
    assert len(result.after_item.affixes) == 2
    assert result.after_item.affixes[0].definition_id == "Prefix"
    assert result.after_item.affixes[1].group == AffixGroup.SUFFIX


def test_flat_weighted_model_has_a_stable_statistical_distribution() -> None:
    common = _definition("Common", "1")
    rare = _definition("Rare", "3")
    engine = CraftingEngine(_synthetic_catalog(common, rare))
    rng = random.Random(34587)
    observed = 0
    attempts = 2000
    for _ in range(attempts):
        result = engine.attempt(_item(), _action(seed=None), randomizer=rng)
        assert result.success
        observed += result.outcome.family_id == "Rare"
    assert 1400 <= observed <= 1600


def test_storage_order_does_not_change_exact_probabilities_or_duplicate_outcomes() -> None:
    first = _definition("Common", "1", "2")
    second = _definition("Rare", "7")
    left = CraftingEngine(_synthetic_catalog(first, second)).build_pool(_item(), _action())
    right = CraftingEngine(_synthetic_catalog(second, first)).build_pool(_item(), _action())
    left_chances = {row.family_id: row.probability for row in left.family_probabilities}
    right_chances = {row.family_id: row.probability for row in right.family_probabilities}
    assert left_chances == right_chances
    for pool in (left, right):
        keys = [(row.family_id, row.tier_id) for row in pool.outcomes]
        assert len(keys) == len(set(keys))


def test_special_system_rows_never_enter_standard_craft_pool() -> None:
    standard = _definition("Standard", "3")
    special = replace(_definition("Graft", "100"), crafting_system_id="tlidb:graft")
    pool = CraftingEngine(_synthetic_catalog(standard, special)).build_pool(_item(), _action())
    assert {row.family_id for row in pool.outcomes} == {"Standard"}


def test_duplicate_semantic_family_rows_block_instead_of_double_counting() -> None:
    first = replace(_definition("FamilyA", "1"), semantic_signature="same normalized family")
    second = replace(_definition("FamilyB", "9"), semantic_signature="same normalized family")
    result = CraftingEngine(_synthetic_catalog(first, second)).attempt(_item(), _action())
    assert not result.success
    assert "repeated semantic family" in result.reason


def _item_for_base(catalog, base_id: str, group: AffixGroup, category: AffixCategory):
    base = catalog.bases[base_id]
    definition = next(
        entry for entry in catalog.affixes.values()
        if not entry.is_legacy_alias
        and entry.source_id == base.source_id
        and base.id in entry.base_ids
        and entry.group == group
        and entry.category == category
        and entry.pool_id
        and entry.crafting_system_id == "tlidb:standard-craft"
    )
    item = EquipmentItem(
        id="sample-item",
        name=base.name,
        base_id=base.id,
        item_level=86,
        priceless=False,
        affixes=[AffixInstance.create(definition, definition.tiers[-1])],
    )
    return item, definition


@pytest.mark.parametrize(
    "base_id",
    [
        "sleeping-sages-cane",
        "tlidb-category-claw:base:Nailclaw",
        "tlidb-category-ring:base:Burning_Flame_Ring",
        "tlidb-category-two-handed-sword:base:Sundering_Greatsword",
    ],
)
def test_real_catalog_representative_pools_preserve_exact_boundaries(base_id) -> None:
    catalog = load_catalog()
    item, target = _item_for_base(catalog, base_id, AffixGroup.PREFIX, AffixCategory.BASIC)
    action = _action(index=0, seed=23)
    pool = CraftingEngine(catalog).build_pool(item, action)
    result = CraftingEngine(catalog).attempt(item, action)

    assert pool.pool_id == target.pool_id
    assert all(outcome.pool_id == pool.pool_id for outcome in pool.outcomes)
    assert pool.total_weight > 0
    assert result.success and result.outcome is not None
    assert result.outcome.group == AffixGroup.PREFIX
    assert len(result.after_item.affixes) == 1
    assert result.after_item.affixes[0].id == item.affixes[0].id


def test_claw_multistrike_family_stays_distinct_from_critical_rating() -> None:
    catalog = load_catalog()
    claw = "tlidb-category-claw:base:Nailclaw"
    base = catalog.bases[claw]
    multistrike = next(
        entry for entry in catalog.affixes.values()
        if not entry.is_legacy_alias
        and entry.source_id == base.source_id
        and entry.category == AffixCategory.ADVANCED
        and entry.group == AffixGroup.SUFFIX
        and "Multistrike" in entry.name
    )
    critical_rating = next(
        entry for entry in catalog.affixes.values()
        if not entry.is_legacy_alias
        and entry.source_id == base.source_id
        and entry.category == AffixCategory.ADVANCED
        and entry.group == AffixGroup.SUFFIX
        and "Critical Strike Rating" in entry.name
    )
    assert multistrike.id != critical_rating.id
    assert multistrike.semantic_signature != critical_rating.semantic_signature

    item = EquipmentItem(
        id="claw-sample",
        name=base.name,
        base_id=base.id,
        item_level=86,
        affixes=[AffixInstance.create(critical_rating, critical_rating.tiers[-1])],
    )
    pool = CraftingEngine(catalog).build_pool(
        item,
        _action(group=AffixGroup.SUFFIX, category=AffixCategory.ADVANCED),
    )
    assert multistrike.id in {row.family_id for row in pool.outcomes}


def test_selected_target_family_is_allowed_for_replace_and_other_families_are_excluded() -> None:
    first = _definition("Existing", "1")
    second = _definition("Other", "2")
    third = _definition("New", "3")
    catalog = _synthetic_catalog(first, second, third)
    item = _item()
    existing = AffixInstance.create(first, first.tiers[0])
    other = AffixInstance.create(second, second.tiers[0])
    item.affixes = [existing, other]
    pool = CraftingEngine(catalog).build_pool(item, _action(index=0))
    assert {outcome.family_id for outcome in pool.outcomes} == {"Existing", "New"}
