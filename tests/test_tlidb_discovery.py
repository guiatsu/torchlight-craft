from __future__ import annotations

from tools.tlidb.discovery import compare_reference_categories, discover_categories


def _home_page(names: list[tuple[str, str, str]]) -> str:
    links = "".join(
        f'<a href="{href}" data-i18n="item_type_list|name|{source_id}">{name}</a>'
        for name, href, source_id in names
    )
    return f"""
    <html><body><div class="card"><div class="card-header">Gear</div>
    <div class="card-body"><div class="py-1"><span>Weapons</span>{links}</div>
    <div class="py-1"><a href="Talent" data-i18n="handbook|name|30010">Talent</a></div>
    </div></div></body></html>
    """


def test_discovery_finds_new_categories_and_keeps_source_ids() -> None:
    html = _home_page([
        ("Cane", "Cane", "10512"),
        ("Ethereal Prism", "Ethereal_Prism", "100101"),
        ("Cane", "/en/Cane", "10512"),
    ])
    categories = discover_categories(html)
    assert [entry.name for entry in categories] == ["Cane", "Ethereal Prism"]
    assert categories[0].source_category_id == "10512"
    assert categories[0].group_label == "Weapons"
    assert categories[1].url == "https://tlidb.com/en/Ethereal_Prism"


def test_reference_control_list_reports_extra_without_hiding_it() -> None:
    categories = discover_categories(_home_page([
        ("Claw", "Claw", "10501"),
        ("Ethereal Prism", "Ethereal_Prism", "100101"),
    ]))
    comparison = compare_reference_categories(categories)
    assert "Ethereal Prism" in comparison["additional_on_site"]
    assert "Claw" not in comparison["missing_from_site"]


def test_missing_gear_navigation_is_an_error() -> None:
    import pytest

    with pytest.raises(ValueError, match="Gear navigation"):
        discover_categories("<html><body><div>no catalog links</div></body></html>")
