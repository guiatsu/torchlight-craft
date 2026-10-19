from core.catalog import load_catalog
from core.models import AffixGroup, AffixInstance, EquipmentItem
from services.affix_browser import AffixBrowser
from services.item_editor_service import ItemEditorService
from services.item_library_service import ItemLibraryService
from services.item_repository import ItemRepository


def test_editor_keeps_one_item_and_returns_explicit_empty_known_slots():
    catalog = load_catalog()
    item = EquipmentItem()
    editor = ItemEditorService(catalog, item)

    assert editor.item is item
    assert len(editor.slots(AffixGroup.PREFIX)) == 3
    assert all(slot["kind"] == "empty" for slot in editor.slots(AffixGroup.PREFIX))

    editor.change_base("blue-amber-cane")

    assert editor.slots(AffixGroup.PREFIX) == []


def test_editor_adds_replaces_and_removes_only_the_target_instance():
    catalog = load_catalog()
    editor = ItemEditorService(catalog, EquipmentItem())
    fire = catalog.affixes["cane-fire-damage-prefix"]
    fire_instance = editor.add_or_update_affix(fire, fire.tiers[0], "fire value")
    physical = catalog.affixes["cane-physical-damage-prefix"]
    other = editor.add_or_update_affix(physical, physical.tiers[-1], "physical value")
    other_snapshot = other.__dict__.copy() if hasattr(other, "__dict__") else (
        other.id, other.definition_id, other.group, other.category, other.tier_id, other.value
    )

    critical = catalog.affixes["cane-critical-damage-suffix"]
    editor.add_or_update_affix(
        critical,
        critical.tiers[0],
        "critical value",
        instance_id=fire_instance.id,
    )

    assert len(editor.item.affixes) == 2
    assert editor.item.affixes[0].id == fire_instance.id
    assert editor.item.affixes[0].definition_id == critical.id
    assert (other.id, other.definition_id, other.group, other.category, other.tier_id, other.value) == other_snapshot
    assert editor.remove_affix(fire_instance.id)
    assert [affix.id for affix in editor.item.affixes] == [other.id]


def test_base_change_preserves_incompatible_affix_until_explicit_removal():
    catalog = load_catalog()
    editor = ItemEditorService(catalog, EquipmentItem())
    definition = catalog.affixes["cane-fire-damage-prefix"]
    instance = editor.add_or_update_affix(definition, definition.tiers[0], "kept value")

    incompatible = editor.change_base("ring")

    assert len(editor.item.affixes) == 1
    assert incompatible[0].instance is instance
    assert editor.validation_errors()
    assert editor.remove_incompatible_affixes({instance.id}) == 1
    assert editor.item.affixes == []


def test_incompatibility_blocks_new_affix_but_can_be_fixed_by_replacing_target():
    catalog = load_catalog()
    editor = ItemEditorService(catalog, EquipmentItem())
    cane_definition = catalog.affixes["cane-fire-damage-prefix"]
    instance = editor.add_or_update_affix(cane_definition, cane_definition.tiers[0], "fire value")
    editor.change_base("ring")
    ring_definition = catalog.affixes["ring-fire-damage-advanced-prefix"]

    try:
        editor.add_or_update_affix(
            ring_definition, ring_definition.tiers[0], "ring value"
        )
    except ValueError as exc:
        assert "Resolve the other incompatible affixes" in str(exc)
    else:
        raise AssertionError("An unrelated addition should be blocked while incompatibilities remain.")

    editor.add_or_update_affix(
        ring_definition,
        ring_definition.tiers[0],
        "ring value",
        instance_id=instance.id,
    )

    assert editor.incompatible_affixes() == []


def test_affix_browser_distinguishes_add_edit_and_replace_modes():
    catalog = load_catalog()
    browser = AffixBrowser(catalog)
    definition = catalog.affixes["cane-fire-damage-prefix"]
    browser.begin_add(AffixGroup.PREFIX)
    browser.select_definition(definition, item_level=86)
    assert browser.mode == "add"

    instance = AffixInstance.create(definition, definition.tiers[0])
    browser.select_instance(instance)
    assert browser.mode == "edit"
    browser.select_definition(catalog.affixes["cane-physical-damage-prefix"], item_level=86)
    assert browser.mode == "replace"


def test_library_duplicate_has_new_identity_and_does_not_mutate_source(tmp_path):
    source = EquipmentItem(name="Saved cane")
    service = ItemLibraryService(ItemRepository(tmp_path / "items.json"))

    duplicate = service.duplicate(source)

    assert duplicate.id != source.id
    assert duplicate.name == "Saved cane Copy"
    assert source.name == "Saved cane"
