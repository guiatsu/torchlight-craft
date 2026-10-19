from core.models import AffixInstance, EquipmentItem
from core.serialization import deserialize_item, serialize_item
from core.catalog import load_catalog


def test_new_equipment_has_a_stable_typed_shape():
    item = EquipmentItem()
    assert item.base_id == "sleeping-sages-cane"
    assert item.item_level == 86
    assert item.priceless is False
    assert item.rarity is None
    assert item.affixes == []


def test_priceless_and_rarity_are_separate_fields():
    item = EquipmentItem(priceless=True, rarity="Rare")
    restored = deserialize_item(serialize_item(item))
    assert restored.priceless is True
    assert restored.rarity == "Rare"


def test_catalog_affix_can_be_instanced_with_unique_ids():
    catalog = load_catalog()
    definition = catalog.affixes["cane-physical-damage-prefix"]
    tier = definition.tiers[0]
    first = AffixInstance.create(definition, tier)
    second = AffixInstance.create(definition, tier)
    assert first.group.value == "prefix"
    assert first.id != second.id
    assert first.value == tier.value_range


def test_schema_v1_item_shape_survives_deserialize_serialize_round_trip():
    legacy_document = {
        "schema_version": 1,
        "item": {
            "id": "item-existing-1",
            "name": "Existing cane",
            "base_id": "sleeping-sages-cane",
            "item_level": 86,
            "priceless": False,
            "rarity": None,
            "affixes": [],
        },
    }

    item = deserialize_item(legacy_document)

    assert serialize_item(item) == legacy_document
