from core.catalog import load_catalog
from core.models import EquipmentItem
from app.viewmodels.item_editor import ItemEditorViewModel
from services.affix_browser import AffixBrowser
from services.item_editor_service import ItemEditorService


def test_runtime_sqlite_catalog_is_exhaustive_and_keeps_legacy_ids() -> None:
    catalog = load_catalog()

    assert len(catalog.categories) == 49
    assert len(catalog.bases) >= 2194
    assert len(catalog.affixes) >= 642
    assert catalog.bases["sleeping-sages-cane"].prefix_limit == 3
    assert catalog.bases["sleeping-sages-cane"].suffix_limit == 3
    assert catalog.bases["ring"].is_legacy_alias
    assert "cane-fire-damage-prefix" in catalog.affixes
    assert catalog.affixes["cane-fire-damage-prefix"].is_legacy_alias


def test_imported_affixes_keep_unique_tier_records_and_exact_zero_weights() -> None:
    catalog = load_catalog()
    browser = AffixBrowser(catalog)
    definitions = browser.definitions_for("sleeping-sages-cane")

    assert definitions
    assert all(not definition.is_legacy_alias for definition in definitions)
    assert all(definition.crafting_system_id == "tlidb:standard-craft" for definition in definitions)
    zero_tier = next(
        tier
        for definition in definitions
        for tier in definition.tiers
        if tier.tier_label in {"T0+", "T0"} and tier.weight_raw == "0"
    )
    assert zero_tier.weight_raw == "0"
    assert any(tier.tier_label == "T7" for definition in definitions for tier in definition.tiers)
    assert all(tier.id != tier.tier_label for definition in definitions for tier in definition.tiers)


def test_base_browser_filters_a_large_catalog_without_truncating_results() -> None:
    catalog = load_catalog()
    editor = ItemEditorService(catalog, EquipmentItem())
    view_model = ItemEditorViewModel(editor)

    assert len(view_model.allBaseOptions) > 100
    assert len(view_model.baseCategories) >= 8
    view_model.setBaseSearch("Dragonblood")
    assert [entry["name"] for entry in view_model.baseOptions] == ["Dragonblood Cane"]
    view_model.setBaseSearch("no such base")
    assert view_model.baseOptions == []
    assert view_model.baseResultSummary == "0 matching base(s)"
