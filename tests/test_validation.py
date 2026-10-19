from core.catalog import load_catalog
from core.models import AffixCategory, AffixGroup, AffixInstance, EquipmentItem
from core.validation import validate_item


def _catalog():
    return load_catalog()


def test_valid_item_and_base_are_accepted():
    catalog = _catalog()
    item = EquipmentItem()
    assert validate_item(item, catalog.bases, catalog.affixes) == []


def test_item_level_rejects_negative_and_above_catalog_range():
    catalog = _catalog()
    item = EquipmentItem(item_level=-1)
    assert any("between 1 and 100" in error for error in validate_item(item, catalog.bases, catalog.affixes))
    item.item_level = 101
    assert any("between 1 and 100" in error for error in validate_item(item, catalog.bases, catalog.affixes))


def test_character_requirement_is_not_mistaken_for_item_level():
    catalog = _catalog()
    item = EquipmentItem(item_level=85)
    assert validate_item(item, catalog.bases, catalog.affixes) == []


def test_affix_group_and_tier_must_match_catalog():
    catalog = _catalog()
    item = EquipmentItem()
    definition = catalog.affixes["cane-physical-damage-prefix"]
    instance = AffixInstance.create(definition, definition.tiers[0])
    instance.group = AffixGroup.SUFFIX
    instance.tier_id = "T99"
    item.affixes.append(instance)
    errors = validate_item(item, catalog.bases, catalog.affixes)
    assert any("wrong group" in error for error in errors)
    assert any("unsupported tier" in error for error in errors)


def test_duplicate_affix_instance_ids_are_rejected():
    catalog = _catalog()
    definition = catalog.affixes["cane-physical-damage-prefix"]
    first = AffixInstance.create(definition, definition.tiers[0])
    second = AffixInstance.create(definition, definition.tiers[0])
    second.id = first.id
    item = EquipmentItem(affixes=[first, second])
    assert any("unique instance ID" in error for error in validate_item(item, catalog.bases, catalog.affixes))


def test_screenshot_slot_count_is_provisional_and_enforced_only_for_that_base():
    catalog = _catalog()
    definition = catalog.affixes["cane-physical-damage-prefix"]
    instances = [AffixInstance.create(definition, definition.tiers[0]) for _ in range(4)]
    cane = EquipmentItem(affixes=instances)
    assert any("provisional prefix limit of 3" in error for error in validate_item(cane, catalog.bases, catalog.affixes))

    ring_definition = catalog.affixes["ring-fire-damage-advanced-prefix"]
    ring_affixes = [AffixInstance.create(ring_definition, ring_definition.tiers[0]) for _ in range(4)]
    ring = EquipmentItem(base_id="ring", item_level=86, affixes=ring_affixes)
    assert not any("prefix limit" in error for error in validate_item(ring, catalog.bases, catalog.affixes))
