from __future__ import annotations

from pathlib import Path

from tools.tlidb.discovery import EquipmentCategoryLink
from tools.tlidb.parsers import parse_category_page, parse_item_detail_page


FIXTURE = Path(__file__).parent / "fixtures" / "tlidb" / "category-sample.html"


def _category() -> EquipmentCategoryLink:
    return EquipmentCategoryLink(
        id="tlidb-category-sample",
        name="Sample",
        url="https://tlidb.com/en/Sample",
        source_href="Sample",
        source_category_id="99901",
        group_label="One-handed",
    )


def _parse():
    return parse_category_page(
        _category(),
        FIXTURE.read_text(encoding="utf-8"),
        retrieved_at="2026-10-19T00:00:00+00:00",
        source_hash="fixture-hash",
    )


def test_parses_base_requirements_and_source_properties() -> None:
    parsed = _parse()
    assert len(parsed.bases) == 1
    base = parsed.bases[0]
    assert base.name == "Sample Base"
    assert base.source_item_id == "Sample_Base"
    assert base.character_level_requirement == 42
    assert base.hands == 1
    assert base.properties[0]["source_modifier_id"] == "71001"
    assert base.properties[0]["description"] == "100 Armor"
    assert base.crafting_class == "standard_craftable"
    assert base.classification_evidence
    assert parsed.errors == []


def test_preserves_all_tiers_family_keys_and_explicit_zero_weights() -> None:
    parsed = _parse()
    prefix = [tier for tier in parsed.tiers if tier.group == "prefix"]
    assert [tier.tier for tier in prefix] == ["T0+", "T0", "T3"]
    assert {tier.family_source_id for tier in prefix} == {"88001"}
    assert all(tier.family_grouping_status == "source_family_id" for tier in prefix)
    assert [tier.weight_raw for tier in prefix] == ["0", "0", None]
    assert [tier.weight_parse_status for tier in prefix] == [
        "parsed_integer", "parsed_integer", "missing"
    ]
    assert prefix[0].description == "Adds (10–12) Fire Damage"
    assert prefix[0].source_modifier_id == "990080"
    assert prefix[0].requirement_level == 90


def test_parses_suffix_and_library_independently() -> None:
    parsed = _parse()
    suffix = next(tier for tier in parsed.tiers if tier.group == "suffix")
    assert suffix.tier == "T2"
    assert suffix.library == "Ultimate"
    assert suffix.description == "+5% Special"
    assert suffix.weight_raw == "12"
    assert suffix.family_source_id == "88002"


def test_announced_and_discovered_counts_are_auditable() -> None:
    parsed = _parse()
    normal = next(section for section in parsed.sections if section.section_type == "base_list")
    assert normal.announced_count == normal.discovered_record_count == 1
    assert parsed.craft_tables_discovered == parsed.craft_tables_parsed == 2


def test_item_detail_parser_only_returns_explicit_fields() -> None:
    fixture = Path(__file__).parent / "fixtures" / "tlidb" / "item-detail-sample.html"
    parsed = parse_item_detail_page(fixture.read_text(encoding="utf-8"))
    assert parsed.title == "Sample Helmet"
    assert parsed.requirement_levels == (42,)
    assert parsed.properties == ({
        "source_modifier_id": "71001",
        "description": "+120 Gear Armor",
        "description_html": '<span class="text-mod">+120</span> Gear Armor',
    },)
