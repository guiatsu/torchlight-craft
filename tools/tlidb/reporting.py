"""Coverage, errors and unresolved-record reports for TLIDB imports."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from tools.tlidb.discovery import (
    EquipmentCategoryLink,
    compare_reference_categories,
    discovery_report,
)
from tools.tlidb.parsers import ParsedCategoryPage


_BASE_SECTIONS = {"base_list", "legendary", "legendary_corroded", "special_craft"}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def _db_counts_by_category(database: Path) -> dict[str, dict[str, int]]:
    import sqlite3

    counts: dict[str, dict[str, int]] = {}
    if not database.is_file():
        return counts
    with sqlite3.connect(database) as connection:
        for category_id, name, bases, families, tiers, rows in connection.execute(
            """SELECT c.id,c.name,
                 (SELECT COUNT(*) FROM equipment_bases b WHERE b.category_id=c.id),
                 (SELECT COUNT(DISTINCT f.id) FROM affix_families f JOIN affix_pools p ON p.id=f.pool_id WHERE p.category_id=c.id),
                 (SELECT COUNT(*) FROM affix_tiers t JOIN affix_families f ON f.id=t.family_id JOIN affix_pools p ON p.id=f.pool_id WHERE p.category_id=c.id),
                 (SELECT COUNT(*) FROM source_table_rows r WHERE r.category_id=c.id)
                 FROM equipment_categories c"""
        ):
            counts[category_id] = {
                "bases_imported": int(bases),
                "affixes_imported": int(families),
                "tier_rows_imported": int(tiers),
                "source_table_rows_imported": int(rows),
            }
    return counts


def build_reports(
    report_dir: Path,
    categories: list[EquipmentCategoryLink],
    pages: list[ParsedCategoryPage],
    *,
    discovery: dict[str, Any],
    database: Path,
    fetch_errors: list[dict[str, object]],
    discovered_at: str,
    detail_page_count: int = 0,
    detail_records_enriched: int = 0,
    detail_page_urls: set[str] | None = None,
) -> dict[str, Any]:
    inspected_detail_urls = detail_page_urls or set()
    pages_by_id = {page.category.id: page for page in pages}
    imported_counts = _db_counts_by_category(database)
    reference_difference = compare_reference_categories(categories)
    page_reports: list[dict[str, object]] = []
    errors: list[dict[str, object]] = list(fetch_errors)
    unresolved: list[dict[str, object]] = []
    totals = Counter()
    classification = Counter()
    complete_categories = 0

    for category in categories:
        page = pages_by_id.get(category.id)
        db = imported_counts.get(category.id, {})
        if page is None:
            failure_count = sum(1 for item in fetch_errors if item.get("category_id") == category.id)
            page_reports.append({
                "category": category.name,
                "category_id": category.id,
                "url": category.url,
                "bases_announced": 0,
                "bases_discovered": 0,
                "bases_imported": db.get("bases_imported", 0),
                "bases_classified": 0,
                "affixes_found": 0,
                "tier_rows_discovered": 0,
                "tier_rows_imported": db.get("tier_rows_imported", 0),
                "source_table_rows_discovered": 0,
                "source_table_rows_imported": db.get("source_table_rows_imported", 0),
                "weights_imported": 0,
                "failures": failure_count,
                "status": "failed",
            })
            continue

        bases_announced = sum(
            section.announced_count or 0
            for section in page.sections
            if section.section_type in _BASE_SECTIONS
        )
        bases_discovered = len(page.bases)
        bases_imported = db.get("bases_imported", 0)
        classified = sum(base.crafting_class != "unknown" for base in page.bases)
        for base in page.bases:
            classification[base.crafting_class] += 1
            if base.crafting_class == "unknown":
                unresolved.append({
                    "category_id": category.id,
                    "category": category.name,
                    "url": category.url,
                    "record_type": "equipment_base",
                    "record_id": base.id,
                    "name": base.name,
                    "issue": "crafting_class_unknown",
                    "source_section": base.source_section,
                })
            if base.fields_missing:
                for field_name in base.fields_missing:
                    detail_url = (
                        base.source_url
                        if base.source_url != category.url
                        else f"https://tlidb.com/en/{quote(base.source_item_id, safe='')}"
                        if base.source_item_id
                        else None
                    )
                    if detail_url is None:
                        detail_status = "no_item_detail_link"
                    elif detail_url == category.url:
                        detail_status = "same_as_category_page"
                    elif detail_url in inspected_detail_urls:
                        detail_status = "inspected"
                    else:
                        detail_status = "not_inspected"
                    unresolved.append({
                        "category_id": category.id,
                        "category": category.name,
                        "url": category.url,
                        "record_type": "equipment_base",
                        "record_id": base.id,
                        "name": base.name,
                        "issue": "source_field_not_present_in_category_card",
                        "field": field_name,
                        "category_source_url": category.url,
                        "detail_url": detail_url,
                        "detail_page_inspected": detail_url in inspected_detail_urls,
                        "detail_page_status": detail_status,
                    })
        tier_discovered = len(page.tiers)
        tier_imported = db.get("tier_rows_imported", 0)
        source_rows_discovered = len(page.source_rows)
        source_rows_imported = db.get("source_table_rows_imported", 0)
        affixes = len({tier.family_id for tier in page.tiers})
        canonical_ids_by_legacy: dict[str, set[str]] = {}
        for tier in page.tiers:
            if tier.legacy_family_id:
                canonical_ids_by_legacy.setdefault(tier.legacy_family_id, set()).add(tier.family_id)
        split_legacy_families = sum(len(canonical_ids) > 1 for canonical_ids in canonical_ids_by_legacy.values())
        weights_imported = sum(tier.weight_raw is not None for tier in page.tiers)
        explicit_zero_weights = sum(tier.weight_raw == "0" for tier in page.tiers)
        missing_weights = sum(tier.weight_parse_status == "missing" for tier in page.tiers)
        unparsed_weights = sum(tier.weight_parse_status == "unparsed" for tier in page.tiers)
        errors.extend({"category_id": category.id, **entry} for entry in page.errors)
        unresolved.extend({**entry, "category_id": category.id} for entry in page.unresolved)
        mismatch = any(
            section.announced_count is not None
            and section.announced_count != section.discovered_record_count
            for section in page.sections
        )
        category_errors = len(page.errors) + sum(
            1 for entry in fetch_errors if entry.get("category_id") == category.id
        )
        category_unresolved = sum(1 for entry in unresolved if entry.get("category_id") == category.id)
        counts_match = (
            bases_announced == bases_discovered == bases_imported
            and tier_discovered == tier_imported
            and source_rows_discovered == source_rows_imported
        )
        status = "complete" if not category_errors and not category_unresolved and not mismatch and counts_match else "partial"
        if status == "complete":
            complete_categories += 1
        row = {
            "category": category.name,
            "category_id": category.id,
            "url": category.url,
            "group_label": category.group_label,
            "bases_announced": bases_announced,
            "bases_discovered": bases_discovered,
            "bases_imported": bases_imported,
            "bases_classified": classified,
            "crafting_class_counts": dict(Counter(base.crafting_class for base in page.bases)),
            "affixes_found": affixes,
            "legacy_family_ids_split": split_legacy_families,
            "craft_tables_discovered": page.craft_tables_discovered,
            "craft_tables_parsed": page.craft_tables_parsed,
            "tier_rows_discovered": tier_discovered,
            "tier_rows_imported": tier_imported,
            "source_tables_discovered": page.source_tables_discovered,
            "source_table_rows_discovered": source_rows_discovered,
            "source_table_rows_imported": source_rows_imported,
            "weights_imported": weights_imported,
            "explicit_zero_weights": explicit_zero_weights,
            "missing_weights": missing_weights,
            "unparsed_weights": unparsed_weights,
            "failures": category_errors,
            "unresolved_count": category_unresolved,
            "count_mismatch": mismatch,
            "status": status,
        }
        page_reports.append(row)
        for key in (
            "bases_announced", "bases_discovered", "bases_imported", "bases_classified",
            "affixes_found", "legacy_family_ids_split", "craft_tables_discovered", "craft_tables_parsed",
            "tier_rows_discovered", "tier_rows_imported", "source_tables_discovered",
            "source_table_rows_discovered", "source_table_rows_imported", "weights_imported",
            "explicit_zero_weights", "missing_weights", "unparsed_weights", "failures",
        ):
            totals[key] += int(row[key])

    if reference_difference["missing_from_site"]:
        errors.append({
            "issue": "reference_categories_missing_from_live_gear_navigation",
            "categories": reference_difference["missing_from_site"],
        })
    rows_discovered = (
        totals["bases_discovered"]
        + totals["tier_rows_discovered"]
        + totals["source_table_rows_discovered"]
    )
    rows_imported = (
        totals["bases_imported"]
        + totals["tier_rows_imported"]
        + totals["source_table_rows_imported"]
    )
    record_coverage = round(100 * rows_imported / rows_discovered, 2) if rows_discovered else 0.0
    processed = len(pages)
    category_count = len(categories)
    overall_status = (
        "complete"
        if processed == category_count and complete_categories == category_count and not errors and not unresolved
        else "partial"
    )
    coverage_report = {
        "schema_version": 1,
        "generated_at": discovered_at,
        "source": "TLIDB",
        "season_reference": "SS14 — Tartarus; source data remains community-unverified",
        "overall_status": overall_status,
        "coverage_percent": record_coverage,
        "coverage_definition": "Imported base, affix-tier and non-affix table-row records divided by records discovered in fetched category pages. This is record retention, not game-data verification.",
        "summary": {
            "category_pages_discovered": category_count,
            "category_pages_processed": processed,
            "category_pages_complete": complete_categories,
            "category_pages_partial_or_failed": category_count - complete_categories,
            "categories_missing_from_control_list": reference_difference["missing_from_site"],
            "categories_additional_on_site": reference_difference["additional_on_site"],
            "equipment_bases_announced": totals["bases_announced"],
            "equipment_bases_discovered": totals["bases_discovered"],
            "equipment_bases_imported": totals["bases_imported"],
            "standard_craftable_bases": classification["standard_craftable"],
            "special_craftable_bases": classification["special_craftable"],
            "non_craftable_bases": classification["non_craftable"],
            "unknown_classification_bases": classification["unknown"],
            "affix_entries_discovered": totals["affixes_found"],
            "canonical_affix_families_imported": totals["affixes_found"],
            "legacy_family_ids_split": totals["legacy_family_ids_split"],
            "family_grouping_explanation": (
                "The previous importer treated a broad source comment as one family. "
                "The new importer also checks the source modifier family and normalized property text, "
                "so semantically different affixes receive separate canonical family IDs. "
                "The old source key remains available as a legacy alias; no tier rows are removed."
            ),
            "craft_tables_discovered": totals["craft_tables_discovered"],
            "craft_tables_parsed": totals["craft_tables_parsed"],
            "tier_rows_discovered": totals["tier_rows_discovered"],
            "tier_rows_imported": totals["tier_rows_imported"],
            "weights_imported": totals["weights_imported"],
            "explicit_zero_weights": totals["explicit_zero_weights"],
            "missing_weights": totals["missing_weights"],
            "unparsed_weights": totals["unparsed_weights"],
            "non_affix_source_table_rows_discovered": totals["source_table_rows_discovered"],
            "non_affix_source_table_rows_imported": totals["source_table_rows_imported"],
            "records_discovered": rows_discovered,
            "records_imported": rows_imported,
            "missing_records": max(0, rows_discovered - rows_imported),
            "parsing_errors": len(errors),
            "unresolved_records": len(unresolved),
            "unresolved_classifications": classification["unknown"],
            "item_detail_pages_inspected": detail_page_count,
            "records_enriched_from_item_details": detail_records_enriched,
            "record_coverage_percent": record_coverage,
        },
        "categories": page_reports,
        "classification_counts": dict(classification),
    }

    _write_json(report_dir / "tlidb-discovery.json", discovery)
    _write_json(report_dir / "tlidb-coverage.json", coverage_report)
    _write_json(report_dir / "tlidb-import-errors.json", {"errors": errors})
    _write_json(report_dir / "tlidb-unresolved.json", {"unresolved": unresolved})
    (report_dir / "tlidb-import-summary.md").write_text(
        _markdown_summary(coverage_report, page_reports, errors, unresolved), encoding="utf-8"
    )
    return coverage_report


def _markdown_summary(
    coverage_report: dict[str, Any],
    categories: list[dict[str, object]],
    errors: list[dict[str, object]],
    unresolved: list[dict[str, object]],
) -> str:
    summary = coverage_report["summary"]
    lines = [
        "# TLIDB catalog import summary",
        "",
        f"Generated at: {coverage_report['generated_at']}",
        f"Overall status: **{coverage_report['overall_status']}**",
        f"Record retention coverage: **{coverage_report['coverage_percent']:.2f}%**",
        "",
        "Coverage counts fetched and retained records; it does not confirm game rules or SS14 accuracy.",
        "",
        "## Totals",
        "",
        f"- Category pages discovered: {summary['category_pages_discovered']}",
        f"- Category pages processed: {summary['category_pages_processed']}",
        f"- Equipment bases announced: {summary['equipment_bases_announced']}",
        f"- Equipment bases discovered/imported: {summary['equipment_bases_discovered']} / {summary['equipment_bases_imported']}",
        f"- Standard craftable bases: {summary['standard_craftable_bases']}",
        f"- Special craftable bases: {summary['special_craftable_bases']}",
        f"- Non-craftable bases: {summary['non_craftable_bases']}",
        f"- Unknown classification: {summary['unknown_classification_bases']}",
        f"- Craft tables discovered/parsed: {summary['craft_tables_discovered']} / {summary['craft_tables_parsed']}",
        f"- Affix families discovered: {summary['affix_entries_discovered']}",
        f"- Broad legacy family IDs split into semantic families: {summary['legacy_family_ids_split']}",
        f"- Why family counts changed: {summary['family_grouping_explanation']}",
        f"- Tier rows discovered/imported: {summary['tier_rows_discovered']} / {summary['tier_rows_imported']}",
        f"- Weights imported (including zero): {summary['weights_imported']}",
        f"- Explicit zero weights: {summary['explicit_zero_weights']}",
        f"- Missing/unparsed weights: {summary['missing_weights']} / {summary['unparsed_weights']}",
        f"- Non-affix table rows discovered/imported: {summary['non_affix_source_table_rows_discovered']} / {summary['non_affix_source_table_rows_imported']}",
        f"- Item detail pages inspected: {summary['item_detail_pages_inspected']}",
        f"- Base records enriched from item detail pages: {summary['records_enriched_from_item_details']}",
        f"- Missing records: {summary['missing_records']}",
        f"- Parsing/import errors: {len(errors)}",
        f"- Unresolved items: {len(unresolved)}",
        "",
        "## Per-category coverage",
        "",
        "| Category | Bases announced / discovered / imported | Affixes | Tiers discovered / imported | Weights | Errors | Unresolved | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in categories:
        lines.append(
            f"| {row['category']} | {row['bases_announced']} / {row['bases_discovered']} / {row['bases_imported']} "
            f"| {row['affixes_found']} | {row['tier_rows_discovered']} / {row['tier_rows_imported']} "
            f"| {row['weights_imported']} | {row['failures']} | {row.get('unresolved_count', 0)} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `complete` means every announced/parsed record in the fetched page set was retained and reconciled, with no unresolved classification or parsing issue.",
            "- An `unknown` crafting classification is preserved as unknown and prevents an overall complete status.",
            "- Additional live categories are included; missing control-list categories are reported as errors for investigation.",
            "- The source is community-maintained TLIDB data and is not independently verified for the current season.",
            "",
        ]
    )
    return "\n".join(lines)
