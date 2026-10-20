from __future__ import annotations

import sqlite3
from dataclasses import replace
from pathlib import Path

from app.viewmodels.affix_browser import AffixBrowserViewModel
from app.viewmodels.item_editor import ItemEditorViewModel
from core.catalog import load_catalog
from core.models import AffixInstance, EquipmentItem, TierOption, resolve_tier_reference
from core.validation import validate_item
from services.affix_browser import AffixBrowser
from services.item_editor_service import ItemEditError, ItemEditorService
from tools.tlidb.validation import validate_catalog_database


def _claw_affixes():
    catalog = load_catalog()
    claw_id = next(
        category_id
        for category_id, category in catalog.categories.items()
        if category["name"] == "Claw"
    )
    return catalog, [
        definition
        for definition in catalog.affixes.values()
        if definition.source_id == claw_id and not definition.is_legacy_alias
    ]


def test_claw_multistrike_and_attack_critical_have_their_own_source_rows() -> None:
    catalog, claw_affixes = _claw_affixes()
    multistrike = next(item for item in claw_affixes if "chance to multistrike" in item.name.casefold())
    attack_critical = next(item for item in claw_affixes if "attack critical strike rating" in item.name.casefold())

    assert [tier.tier_label for tier in multistrike.tiers] == ["T0+", "T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7"]
    assert [tier.tier_label for tier in attack_critical.tiers] == ["T0+", "T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7"]
    assert all("Multistrike" in tier.value_range for tier in multistrike.tiers)
    assert all("Multistrike" not in tier.value_range for tier in attack_critical.tiers)
    assert [tier.weight_raw for tier in multistrike.tiers] == ["0", "0", "100", "200", "800", "3200", "3200", "6250", "6250"]
    assert [tier.weight_raw for tier in attack_critical.tiers] == ["0", "0", "100", "200", "800", "3200", "3200", "6250", "6250"]
    assert [tier.item_level_required for tier in multistrike.tiers] == [100, 100, 86, 82, 76, 68, 58, 40, 1]
    assert len({tier.id for tier in multistrike.tiers}) == len(multistrike.tiers)
    assert all(tier.id != tier.tier_label for tier in multistrike.tiers)

    browser = AffixBrowser(catalog)
    browser.select_definition(multistrike, item_level=86)
    t1 = next(tier for tier in multistrike.tiers if tier.tier_label == "T1")
    assert browser.set_tier(t1.id, item_level=86) == t1
    assert browser.selected_tier() is t1
    assert browser.selected_tier().weight_raw == "100"


def test_v020_ambiguous_claw_family_and_legacy_tier_label_are_signaled() -> None:
    catalog = load_catalog()
    old_id = next(
        definition.id
        for definition in catalog.affixes.values()
        if definition.is_legacy_alias
        and ":section:ClawCraft:suffix:Advanced:200010" in definition.id
    )
    old_definition = catalog.affixes[old_id]

    resolved, ambiguous = resolve_tier_reference(old_definition.tiers, "T0+")
    assert resolved is None
    assert ambiguous

    item = EquipmentItem(
        base_id="sleeping-sages-cane",
        affixes=[AffixInstance(
            id="legacy-claw-affix",
            definition_id=old_id,
            group=old_definition.group,
            category=old_definition.category,
            tier_id="T0+",
            value="legacy value",
        )],
    )
    errors = validate_item(item, catalog.bases, catalog.affixes)
    assert any("ambiguous legacy tier label T0+" in error for error in errors)


def test_resolved_legacy_affix_cannot_be_added_again_under_its_new_family_id() -> None:
    catalog, claw_affixes = _claw_affixes()
    multistrike = next(item for item in claw_affixes if "chance to multistrike" in item.name.casefold())
    tier = next(option for option in multistrike.tiers if option.tier_label == "T7")
    old_id = next(
        definition.id
        for definition in catalog.affixes.values()
        if definition.is_legacy_alias
        and ":section:ClawCraft:suffix:Advanced:200010" in definition.id
    )
    legacy = catalog.affixes[old_id]
    base_id = multistrike.base_ids[0]
    instance = AffixInstance(
        id="resolved-legacy-affix",
        definition_id=old_id,
        group=legacy.group,
        category=legacy.category,
        tier_id=tier.id,
        value=tier.value_range,
    )
    service = ItemEditorService(catalog, EquipmentItem(base_id=base_id, item_level=86, affixes=[instance]))

    try:
        service.add_or_update_affix(multistrike, tier, tier.value_range)
    except ItemEditError as exc:
        assert "already on this equipment" in str(exc)
    else:
        raise AssertionError("A resolved legacy tier must block adding the same canonical affix again.")

    ambiguous_instance = AffixInstance(
        id="ambiguous-legacy-affix",
        definition_id=old_id,
        group=legacy.group,
        category=legacy.category,
        tier_id="T0+",
        value="legacy value",
    )
    ambiguous_service = ItemEditorService(
        catalog,
        EquipmentItem(base_id=base_id, item_level=100, affixes=[ambiguous_instance]),
    )
    try:
        ambiguous_service.add_or_update_affix(multistrike, tier, tier.value_range)
    except ItemEditError as exc:
        assert "already on this equipment" in str(exc)
    else:
        raise AssertionError("An ambiguous legacy label must not allow a possible duplicate family.")


def test_catalog_validation_checks_semantics_and_retains_every_tier_row() -> None:
    database = Path(__file__).parents[1] / "data" / "catalog.sqlite3"
    report = validate_catalog_database(database)
    assert report["valid"] is True
    assert report["schema_version"] == 3
    assert report["counts"]["tier_rows"] == 13_303
    assert report["counts"]["legacy_family_ids_split"] > 0
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM affix_tiers").fetchone()[0] == 13_303
        assert connection.execute("SELECT COUNT(DISTINCT id) FROM affix_tiers").fetchone()[0] == 13_303


def test_affix_browser_exposes_all_records_for_a_large_family() -> None:
    catalog, claw_affixes = _claw_affixes()
    base = next(base for base in catalog.bases.values() if base.id == "sleeping-sages-cane")
    template = claw_affixes[0]
    family = replace(
        template,
        id="test-large-family",
        name="Large test family",
        base_ids=(base.id,),
        tiers=tuple(
            TierOption(
                id=f"source-record-{index}",
                tier_label=f"T{index}",
                item_level_required=index + 1,
                value_range=f"Long source property description {index}",
            )
            for index in range(30)
        ),
    )
    catalog.affixes[family.id] = family
    editor = ItemEditorService(catalog, EquipmentItem(base_id=base.id, item_level=100))
    browser = AffixBrowser(catalog)
    view_model = AffixBrowserViewModel(browser, editor)

    view_model.selectDefinition(family.id)
    assert len(view_model.tierOptions) == 30
    assert len({row["id"] for row in view_model.tierOptions}) == 30
    assert view_model.tierOptions[-1]["valueRange"].endswith("29")


def test_base_suggestions_use_verified_minimum_item_level_and_keep_existing_base() -> None:
    catalog = load_catalog()
    available = [
        base for base in catalog.bases.values()
        if base.category == "One-handed"
        and base.subcategory == "Cane"
        and base.crafting_class == "standard_craftable"
        and not base.is_legacy_alias
    ]
    low, high = available[:2]
    catalog.bases[low.id] = replace(low, minimum_item_level=80)
    catalog.bases[high.id] = replace(high, minimum_item_level=85)

    item = EquipmentItem(base_id=low.id, item_level=86)
    service = ItemEditorService(catalog, item)
    view_model = ItemEditorViewModel(service)
    assert [entry["id"] for entry in view_model.suggestedBaseOptions] == [high.id]
    assert item.base_id == low.id

    view_model.setItemLevel(84)
    assert item.base_id == low.id
    assert [entry["id"] for entry in view_model.suggestedBaseOptions] == [low.id]

    view_model.setItemLevel(86)
    view_model.applySuggestedBase()
    assert item.base_id == high.id


def test_item_level_and_base_filters_never_replace_or_delete_saved_item_data() -> None:
    catalog = load_catalog()
    item = EquipmentItem(base_id="sleeping-sages-cane", item_level=86)
    service = ItemEditorService(catalog, item)
    definition = next(
        option for option in catalog.affixes.values()
        if not option.is_legacy_alias
        and item.base_id in option.base_ids
        and option.tiers
        and (option.tiers[-1].item_level_required is None or option.tiers[-1].item_level_required <= 86)
    )
    tier = next(
        option for option in definition.tiers
        if option.item_level_required is None or option.item_level_required <= 86
    )
    instance = service.add_or_update_affix(definition, tier, tier.value_range)
    view_model = ItemEditorViewModel(service)

    view_model.setItemLevel(80)
    assert item.base_id == "sleeping-sages-cane"
    assert [affix.id for affix in item.affixes] == [instance.id]

    current_category = catalog.bases[item.base_id].category
    another_category = next(category for category in view_model.baseCategories if category["id"] != current_category)
    view_model.setBaseCategory(another_category["id"])
    assert item.base_id == "sleeping-sages-cane"

    special = next(
        base for base in catalog.bases.values()
        if not base.is_legacy_alias and base.crafting_class == "special_craftable"
    )
    view_model.setBaseCategory(special.category)
    view_model.setBaseSubcategory(special.subcategory)
    view_model.setBaseClassFilter("special_craftable")
    assert view_model.baseOptions
    assert all(entry["craftingClass"] == "special_craftable" for entry in view_model.baseOptions)
    assert item.base_id == "sleeping-sages-cane"

    view_model.setBaseClassFilter("standard_craftable")
    assert all(entry["craftingClass"] == "standard_craftable" for entry in view_model.baseOptions)
    assert item.base_id == "sleeping-sages-cane"
