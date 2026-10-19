from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

from tools.tlidb.discovery import EquipmentCategoryLink, discovery_report
from tools.tlidb.parsers import parse_category_page
from tools.tlidb.reporting import build_reports
from tools.tlidb.storage import write_catalog_database
from tools.tlidb.validation import validate_catalog_database


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


def test_sqlite_import_is_normalized_and_reports_zero_vs_missing_weight(tmp_path: Path) -> None:
    category = _category()
    page = parse_category_page(
        category,
        FIXTURE.read_text(encoding="utf-8"),
        retrieved_at="2026-10-19T00:00:00+00:00",
        source_hash="fixture-hash",
    )
    database = tmp_path / "catalog.sqlite3"
    counts = write_catalog_database(
        database,
        [category],
        [page],
        homepage_hash="home-hash",
        processed_page_count=1,
        legacy_base_file=Path(__file__).parents[1] / "data" / "bases.json",
    )
    assert counts == {
        "categories": 1,
        "processed_pages": 1,
        "bases": 1,
        "affix_families": 2,
        "affix_tiers": 4,
        "source_table_rows": 0,
    }
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM equipment_bases").fetchone()[0] == 1
        assert connection.execute("SELECT weight_raw FROM affix_tiers WHERE tier_label='T0+'").fetchone()[0] == "0"
        assert connection.execute("SELECT weight_raw FROM affix_tiers WHERE tier_label='T3'").fetchone()[0] is None
        assert connection.execute("SELECT family_source_id FROM affix_families ORDER BY id").fetchall() == [
            ("88001",), ("88002",)
        ]
    assert validate_catalog_database(database)["valid"]


def test_reports_never_claim_complete_when_data_is_unresolved(tmp_path: Path) -> None:
    category = _category()
    page = parse_category_page(
        category,
        FIXTURE.read_text(encoding="utf-8"),
        retrieved_at="2026-10-19T00:00:00+00:00",
        source_hash="fixture-hash",
    )
    database = tmp_path / "catalog.sqlite3"
    write_catalog_database(
        database,
        [category],
        [page],
        homepage_hash="home-hash",
        processed_page_count=1,
        legacy_base_file=Path(__file__).parents[1] / "data" / "bases.json",
    )
    report_dir = tmp_path / "reports"
    coverage = build_reports(
        report_dir,
        [category],
        [page],
        discovery={"schema_version": 1, "categories": [category.to_dict()]},
        database=database,
        fetch_errors=[],
        discovered_at="2026-10-19T00:00:00+00:00",
    )
    assert coverage["overall_status"] == "partial"
    assert coverage["coverage_percent"] == 100.0
    assert coverage["summary"]["explicit_zero_weights"] == 2
    assert coverage["summary"]["missing_weights"] == 1
    expected_reports = {
        "tlidb-discovery.json",
        "tlidb-coverage.json",
        "tlidb-import-errors.json",
        "tlidb-unresolved.json",
        "tlidb-import-summary.md",
    }
    assert expected_reports <= {path.name for path in report_dir.iterdir()}
    written = json.loads((report_dir / "tlidb-coverage.json").read_text(encoding="utf-8"))
    assert written["overall_status"] == "partial"


def test_unresolved_report_tracks_detail_fetch_even_if_it_found_no_new_fields(tmp_path: Path) -> None:
    category = _category()
    page = parse_category_page(
        category,
        FIXTURE.read_text(encoding="utf-8"),
        retrieved_at="2026-10-19T00:00:00+00:00",
        source_hash="fixture-hash",
    )
    base = replace(page.bases[0], fields_missing=("properties",))
    page = replace(page, bases=(base,))
    database = tmp_path / "catalog.sqlite3"
    write_catalog_database(
        database,
        [category],
        [page],
        homepage_hash="home-hash",
        processed_page_count=1,
        legacy_base_file=Path(__file__).parents[1] / "data" / "bases.json",
    )

    build_reports(
        tmp_path / "reports",
        [category],
        [page],
        discovery={"schema_version": 1, "categories": [category.to_dict()]},
        database=database,
        fetch_errors=[],
        discovered_at="2026-10-19T00:00:00+00:00",
        detail_page_count=1,
        detail_page_urls={"https://tlidb.com/en/Sample_Base"},
    )
    unresolved = json.loads((tmp_path / "reports" / "tlidb-unresolved.json").read_text(encoding="utf-8"))["unresolved"]
    field_issue = next(item for item in unresolved if item["issue"] == "source_field_not_present_in_category_card")
    assert field_issue["detail_url"] == "https://tlidb.com/en/Sample_Base"
    assert field_issue["detail_page_inspected"] is True
    assert field_issue["detail_page_status"] == "inspected"


def test_unresolved_report_marks_item_urls_that_are_the_category_page(tmp_path: Path) -> None:
    category = _category()
    page = parse_category_page(
        category,
        FIXTURE.read_text(encoding="utf-8"),
        retrieved_at="2026-10-19T00:00:00+00:00",
        source_hash="fixture-hash",
    )
    base = replace(page.bases[0], source_item_id="Sample", fields_missing=("character_level_requirement",))
    page = replace(page, bases=(base,))
    database = tmp_path / "catalog.sqlite3"
    write_catalog_database(
        database,
        [category],
        [page],
        homepage_hash="home-hash",
        processed_page_count=1,
        legacy_base_file=Path(__file__).parents[1] / "data" / "bases.json",
    )

    build_reports(
        tmp_path / "reports",
        [category],
        [page],
        discovery={"schema_version": 1, "categories": [category.to_dict()]},
        database=database,
        fetch_errors=[],
        discovered_at="2026-10-19T00:00:00+00:00",
    )
    unresolved = json.loads((tmp_path / "reports" / "tlidb-unresolved.json").read_text(encoding="utf-8"))["unresolved"]
    field_issue = next(item for item in unresolved if item["issue"] == "source_field_not_present_in_category_card")
    assert field_issue["detail_url"] == category.url
    assert field_issue["detail_page_inspected"] is False
    assert field_issue["detail_page_status"] == "same_as_category_page"
