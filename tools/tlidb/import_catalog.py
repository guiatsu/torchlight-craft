"""Discover, import and audit the offline TLIDB equipment catalog.

Examples from the project root::

    .venv/bin/python tools/tlidb/import_catalog.py discover
    .venv/bin/python tools/tlidb/import_catalog.py import
    .venv/bin/python tools/tlidb/import_catalog.py validate
    .venv/bin/python tools/tlidb/import_catalog.py diff old.sqlite new.sqlite

The app never imports or executes this module during startup.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.tlidb.diff import compare_catalogs
from tools.tlidb.discovery import TLIDB_HOME, compare_reference_categories, discovery_report, discover_categories
from tools.tlidb.fetcher import FetchError, FetchedPage, PageFetcher
from tools.tlidb.parsers import ParsedCategoryPage, parse_category_page, parse_item_detail_page
from tools.tlidb.reporting import build_reports
from tools.tlidb.storage import write_catalog_database
from tools.tlidb.validation import validate_catalog_database, write_validation_report


ROOT = PROJECT_ROOT
DEFAULT_CACHE = ROOT / ".cache" / "tlidb"
DEFAULT_DATABASE = ROOT / "data" / "catalog.sqlite3"
DEFAULT_REPORTS = ROOT / "reports"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import and audit TLIDB equipment catalog data.")
    parser.add_argument("command", choices=("discover", "import", "validate", "diff"))
    parser.add_argument("before", nargs="?", type=Path, help="Previous database for diff")
    parser.add_argument("after", nargs="?", type=Path, help="New database for diff")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--validation-report", type=Path)
    parser.add_argument("--category", action="append", default=[], help="Import only this discovered category; repeat as needed")
    parser.add_argument("--offline", action="store_true", help="Use only verified cached pages")
    parser.add_argument("--refresh", action="store_true", help="Fetch pages again instead of using cache")
    parser.add_argument("--minimum-interval", type=float, default=1.0, help="Minimum seconds between source requests")
    return parser


def _discover(fetcher: PageFetcher, *, refresh: bool) -> tuple[list, object, dict]:
    homepage = fetcher.fetch(TLIDB_HOME, refresh=refresh)
    categories = discover_categories(homepage.html, base_url=homepage.url)
    report = discovery_report(
        categories,
        retrieved_at=homepage.retrieved_at,
        source_hash=homepage.sha256,
    )
    return categories, homepage, report


def _write_discovery(report_dir: Path, discovery: dict) -> None:
    path = report_dir / "tlidb-discovery.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(discovery, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _enrich_from_item_details(
    fetcher: PageFetcher,
    pages: list[ParsedCategoryPage],
    *,
    refresh: bool,
    errors: list[dict[str, object]],
) -> tuple[list[FetchedPage], int]:
    """Inspect item pages only when category cards leave relevant fields blank."""
    category_urls = {page.category.url for page in pages}
    targets: dict[str, list[tuple[ParsedCategoryPage, int]]] = {}
    for page in pages:
        for index, record in enumerate(page.bases):
            if not record.fields_missing or not record.source_item_id:
                continue
            detail_url = urljoin(TLIDB_HOME, quote(record.source_item_id, safe=""))
            if detail_url in category_urls:
                continue
            targets.setdefault(detail_url, []).append((page, index))

    detail_pages: list[FetchedPage] = []
    enriched_records = 0
    for index, (url, records) in enumerate(sorted(targets.items()), 1):
        print(f"[{index}/{len(targets)}] Inspecting item details: {url}", flush=True)
        try:
            detail_page = fetcher.fetch(url, refresh=refresh)
        except FetchError as exc:
            for page, record_index in records:
                record = page.bases[record_index]
                errors.append({
                    "category_id": page.category.id,
                    "category": page.category.name,
                    "record_id": record.id,
                    "name": record.name,
                    "url": url,
                    "issue": "item_detail_fetch_failed",
                    "detail": str(exc),
                })
            continue
        detail_pages.append(detail_page)
        parsed = parse_item_detail_page(detail_page.html)
        for page, record_index in records:
            record = page.bases[record_index]
            if _name_key(parsed.title) != _name_key(record.name):
                errors.append({
                    "category_id": page.category.id,
                    "category": page.category.name,
                    "record_id": record.id,
                    "name": record.name,
                    "url": url,
                    "detail_page_title": parsed.title,
                    "issue": "item_detail_title_mismatch",
                })
                continue

            properties = list(record.properties)
            property_keys = {
                (prop.get("source_modifier_id"), prop.get("description"))
                for prop in properties
            }
            for prop in parsed.properties:
                key = (prop.get("source_modifier_id"), prop.get("description"))
                if key not in property_keys:
                    properties.append(prop)
                    property_keys.add(key)

            missing = list(record.fields_missing)
            level = record.character_level_requirement
            level_raw = record.character_level_requirement_raw
            if "character_level_requirement" in missing and len(parsed.requirement_levels) == 1:
                level = parsed.requirement_levels[0]
                level_raw = str(level)
                missing.remove("character_level_requirement")
            if "properties" in missing and properties:
                missing.remove("properties")

            if len(missing) != len(record.fields_missing):
                enriched_records += 1
            page.bases[record_index] = replace(
                record,
                character_level_requirement=level,
                character_level_requirement_raw=level_raw,
                properties=tuple(properties),
                fields_missing=tuple(missing),
                source_url=detail_page.url,
                source_section=f"{record.source_section} · item detail",
            )
    return detail_pages, enriched_records


def run_discovery(args: argparse.Namespace) -> int:
    fetcher = PageFetcher(args.cache_dir, offline=args.offline, minimum_interval=args.minimum_interval)
    categories, homepage, discovery = _discover(fetcher, refresh=args.refresh)
    _write_discovery(args.reports_dir, discovery)
    comparison = compare_reference_categories(categories)
    print(f"Category pages discovered: {len(categories)}")
    print(f"Reference categories: {discovery['reference_category_count']}")
    print(f"Additional categories included: {len(comparison['additional_on_site'])}")
    if comparison["additional_on_site"]:
        for name in comparison["additional_on_site"]:
            print(f"  + {name}")
    if comparison["missing_from_site"]:
        print("Missing reference categories:")
        for name in comparison["missing_from_site"]:
            print(f"  ! {name}")
    print(f"Discovery report: {args.reports_dir / 'tlidb-discovery.json'}")
    return 2 if comparison["missing_from_site"] else 0


def run_import(args: argparse.Namespace) -> int:
    if args.category and args.database.resolve() == DEFAULT_DATABASE.resolve():
        print("Refusing to overwrite the full catalog with a category-only pilot. Specify --database outside data/catalog.sqlite3.", file=sys.stderr)
        return 2
    fetcher = PageFetcher(args.cache_dir, offline=args.offline, minimum_interval=args.minimum_interval)
    try:
        categories, homepage, discovery = _discover(fetcher, refresh=args.refresh)
    except FetchError as exc:
        print(f"Discovery failed: {exc}", file=sys.stderr)
        return 2

    if args.category:
        requested = {name.casefold() for name in args.category}
        selected = [category for category in categories if category.name.casefold() in requested]
        missing = requested - {category.name.casefold() for category in selected}
        if missing:
            print(f"Unknown category name(s): {', '.join(sorted(missing))}", file=sys.stderr)
            return 2
    else:
        selected = categories

    pages = []
    fetch_errors: list[dict[str, object]] = []
    for index, category in enumerate(selected, 1):
        print(f"[{index}/{len(selected)}] Fetching {category.name}: {category.url}", flush=True)
        try:
            fetched = fetcher.fetch(category.url, refresh=args.refresh)
        except FetchError as exc:
            fetch_errors.append({
                "category_id": category.id,
                "category": category.name,
                "url": category.url,
                "issue": "page_fetch_failed",
                "detail": str(exc),
            })
            print(f"  FAILED: {exc}", file=sys.stderr, flush=True)
            continue
        try:
            page = parse_category_page(
                category,
                fetched.html,
                retrieved_at=fetched.retrieved_at,
                source_hash=fetched.sha256,
            )
            pages.append(page)
            print(
                f"  bases={len(page.bases)} tier_rows={len(page.tiers)} "
                f"tables={page.craft_tables_parsed}/{page.craft_tables_discovered} "
                f"errors={len(page.errors)} unresolved={len(page.unresolved)}",
                flush=True,
            )
        except Exception as exc:  # preserve the page failure in the audit report
            fetch_errors.append({
                "category_id": category.id,
                "category": category.name,
                "url": category.url,
                "issue": "page_parse_failed",
                "detail": f"{type(exc).__name__}: {exc}",
            })
            print(f"  PARSE FAILED: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)

    missing_reference = compare_reference_categories(categories)["missing_from_site"]
    if missing_reference:
        fetch_errors.append({
            "issue": "reference_categories_missing_from_live_gear_navigation",
            "categories": missing_reference,
        })

    detail_pages, detail_records_enriched = _enrich_from_item_details(
        fetcher,
        pages,
        refresh=args.refresh,
        errors=fetch_errors,
    )

    try:
        database_counts = write_catalog_database(
            args.database,
            categories,
            pages,
            homepage_hash=homepage.sha256,
            processed_page_count=len(pages),
            legacy_base_file=ROOT / "data" / "bases.json",
            detail_pages=detail_pages,
        )
    except Exception as exc:
        print(f"Database generation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    coverage = build_reports(
        args.reports_dir,
        categories,
        pages,
        discovery=discovery,
        database=args.database,
        fetch_errors=fetch_errors,
        discovered_at=_timestamp(),
        detail_page_count=len(detail_pages),
        detail_records_enriched=detail_records_enriched,
        detail_page_urls={detail.url for detail in detail_pages},
    )
    validation = validate_catalog_database(args.database)
    write_validation_report(args.reports_dir / "tlidb-validation.json", validation)
    summary = coverage["summary"]
    print(f"Catalog database: {args.database}")
    print(f"Generated rows: {database_counts}")
    print(f"Record retention coverage: {coverage['coverage_percent']:.2f}%")
    print(f"Coverage status: {coverage['overall_status']}")
    print(f"Parsing/import errors: {summary['parsing_errors']}; unresolved records: {summary['unresolved_records']}")
    print(f"Item detail pages inspected: {summary['item_detail_pages_inspected']}; records enriched: {summary['records_enriched_from_item_details']}")
    print(f"Summary report: {args.reports_dir / 'tlidb-import-summary.md'}")
    return 0 if validation["valid"] and coverage["overall_status"] == "complete" else 2


def run_validate(args: argparse.Namespace) -> int:
    report = validate_catalog_database(args.database)
    if args.validation_report:
        write_validation_report(args.validation_report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


def run_diff(args: argparse.Namespace) -> int:
    if args.before is None or args.after is None:
        print("diff requires both BEFORE and AFTER database paths.", file=sys.stderr)
        return 2
    try:
        report = compare_catalogs(args.before, args.after)
    except Exception as exc:
        print(f"Catalog diff failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    args = _parser().parse_args()
    if args.command == "discover":
        return run_discovery(args)
    if args.command == "import":
        return run_import(args)
    if args.command == "validate":
        return run_validate(args)
    return run_diff(args)


if __name__ == "__main__":
    raise SystemExit(main())
