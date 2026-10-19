"""Normalized SQLite output for a reproducible TLIDB catalog import."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from tools.tlidb.discovery import EquipmentCategoryLink
from tools.tlidb.fetcher import FetchedPage
from tools.tlidb.parsers import ParsedCategoryPage


CATALOG_SCHEMA_VERSION = 2
SEASON_REFERENCE = "SS14 — Tartarus (community source; not independently verified)"
CRAFTING_SYSTEMS = {
    "tlidb:standard-craft": (
        "Conventional Craft",
        "standard_craftable",
        "Affix tables are published under a category Craft tab.",
    ),
    "tlidb:graft": (
        "Graft",
        "special_craftable",
        "A category page explicitly publishes a Graft section.",
    ),
    "tlidb:corrosion": (
        "Corrosion",
        "special_craftable",
        "A category page lists a Legendary Gear Corroded variant.",
    ),
    "tlidb:gear-empowerment": (
        "Gear Empowerment",
        "special_craftable",
        "A category page publishes a Gear Empowerment table.",
    ),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _legacy_bases(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("bases", []))


def _compatibility_id(
    record,
    legacy: list[dict[str, object]],
    used: set[str],
) -> str:
    name_key = _name_key(record.name)
    subcategory_key = _name_key(record.category_name)
    matches = [
        row for row in legacy
        if _name_key(str(row.get("name", ""))) == name_key
        and _name_key(str(row.get("subcategory", ""))) == subcategory_key
    ]
    if len(matches) == 1:
        candidate = str(matches[0]["id"])
        if candidate not in used:
            return candidate
    return record.id


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE source_references (
            id TEXT PRIMARY KEY,
            source_site TEXT NOT NULL,
            source_url TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            season TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            sha256 TEXT NOT NULL
        );
        CREATE TABLE equipment_categories (
            id TEXT PRIMARY KEY,
            source_category_id TEXT,
            name TEXT NOT NULL,
            source_url TEXT NOT NULL UNIQUE,
            source_href TEXT NOT NULL,
            group_label TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            source_reference_id TEXT NOT NULL REFERENCES source_references(id)
        );
        CREATE TABLE category_sections (
            id TEXT PRIMARY KEY,
            category_id TEXT NOT NULL REFERENCES equipment_categories(id),
            title TEXT NOT NULL,
            section_type TEXT NOT NULL,
            announced_count INTEGER,
            discovered_record_count INTEGER NOT NULL,
            source_tab_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_hash TEXT NOT NULL
        );
        CREATE TABLE crafting_systems (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            classification TEXT NOT NULL,
            editor_support TEXT NOT NULL,
            evidence_rule TEXT NOT NULL
        );
        CREATE TABLE category_crafting_systems (
            category_id TEXT NOT NULL REFERENCES equipment_categories(id),
            system_id TEXT NOT NULL REFERENCES crafting_systems(id),
            source_section TEXT NOT NULL,
            source_url TEXT NOT NULL,
            PRIMARY KEY(category_id, system_id, source_section)
        );
        CREATE TABLE equipment_bases (
            id TEXT PRIMARY KEY,
            source_record_id TEXT NOT NULL UNIQUE,
            category_id TEXT NOT NULL REFERENCES equipment_categories(id),
            source_item_id TEXT NOT NULL,
            name TEXT NOT NULL,
            section_id TEXT NOT NULL REFERENCES category_sections(id),
            record_kind TEXT NOT NULL,
            crafting_class TEXT NOT NULL,
            character_level_requirement INTEGER,
            character_level_requirement_raw TEXT,
            minimum_item_level INTEGER,
            equipment_type TEXT,
            hands INTEGER,
            prefix_limit INTEGER,
            suffix_limit INTEGER,
            limit_status TEXT NOT NULL,
            restrictions_json TEXT NOT NULL,
            properties_missing_json TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_section TEXT NOT NULL,
            source_row_key TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            classification_evidence TEXT
        );
        CREATE TABLE base_properties (
            id INTEGER PRIMARY KEY,
            base_id TEXT NOT NULL REFERENCES equipment_bases(id) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL,
            source_modifier_id TEXT,
            description TEXT NOT NULL,
            description_html TEXT NOT NULL,
            UNIQUE(base_id, ordinal)
        );
        CREATE TABLE base_crafting_systems (
            base_id TEXT NOT NULL REFERENCES equipment_bases(id) ON DELETE CASCADE,
            system_id TEXT NOT NULL REFERENCES crafting_systems(id),
            evidence TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_section TEXT NOT NULL,
            PRIMARY KEY(base_id, system_id)
        );
        CREATE TABLE affix_pools (
            id TEXT PRIMARY KEY,
            category_id TEXT NOT NULL REFERENCES equipment_categories(id),
            section_id TEXT NOT NULL REFERENCES category_sections(id),
            crafting_system_id TEXT NOT NULL REFERENCES crafting_systems(id),
            group_name TEXT NOT NULL,
            source_table TEXT NOT NULL
        );
        CREATE TABLE affix_families (
            id TEXT PRIMARY KEY,
            pool_id TEXT NOT NULL REFERENCES affix_pools(id),
            family_source_id TEXT,
            display_name TEXT NOT NULL,
            grouping_status TEXT NOT NULL,
            library TEXT,
            library_category TEXT,
            source_section TEXT NOT NULL,
            source_url TEXT NOT NULL
        );
        CREATE TABLE affix_tiers (
            id TEXT PRIMARY KEY,
            family_id TEXT NOT NULL REFERENCES affix_families(id) ON DELETE CASCADE,
            source_modifier_id TEXT,
            tier_label TEXT,
            description TEXT NOT NULL,
            requirement_level INTEGER,
            requirement_level_raw TEXT,
            weight_raw TEXT,
            weight_parse_status TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_section TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_row_key TEXT NOT NULL,
            source_row_number INTEGER NOT NULL
        );
        CREATE TABLE source_table_rows (
            id TEXT PRIMARY KEY,
            category_id TEXT NOT NULL REFERENCES equipment_categories(id),
            section_id TEXT NOT NULL REFERENCES category_sections(id),
            source_table_id TEXT NOT NULL,
            source_table_name TEXT NOT NULL,
            row_number INTEGER NOT NULL,
            headers_json TEXT NOT NULL,
            values_json TEXT NOT NULL,
            values_html_json TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_section TEXT NOT NULL,
            source_row_key TEXT NOT NULL
        );
        CREATE TABLE import_manifest (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            generated_at TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_home_sha256 TEXT NOT NULL,
            source_category_count INTEGER NOT NULL,
            processed_page_count INTEGER NOT NULL,
            base_record_count INTEGER NOT NULL,
            affix_tier_count INTEGER NOT NULL,
            source_table_row_count INTEGER NOT NULL,
            season_reference TEXT NOT NULL,
            verification_status TEXT NOT NULL
        );
        CREATE INDEX idx_bases_category ON equipment_bases(category_id, name);
        CREATE INDEX idx_bases_class ON equipment_bases(crafting_class);
        CREATE INDEX idx_tiers_family ON affix_tiers(family_id, tier_label);
        CREATE INDEX idx_families_pool ON affix_families(pool_id);
        """
    )


def write_catalog_database(
    destination: Path,
    categories: list[EquipmentCategoryLink],
    pages: list[ParsedCategoryPage],
    *,
    homepage_hash: str,
    processed_page_count: int,
    legacy_base_file: Path,
    detail_pages: list[FetchedPage] | None = None,
) -> dict[str, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.unlink(missing_ok=True)
    legacy = _legacy_bases(legacy_base_file)
    detail_pages = detail_pages or []
    used_base_ids: set[str] = set()
    try:
        with sqlite3.connect(temporary) as connection:
            _create_schema(connection)
            connection.execute("PRAGMA user_version = 2")
            for key, value in {
                "catalog_schema_version": str(CATALOG_SCHEMA_VERSION),
                "season_reference": SEASON_REFERENCE,
                "verification_status": "community_reference_season_unverified",
            }.items():
                connection.execute("INSERT INTO metadata(key,value) VALUES(?,?)", (key, value))
            for system_id, (name, classification, evidence) in CRAFTING_SYSTEMS.items():
                support = "selection_only" if system_id == "tlidb:standard-craft" else "not_implemented"
                connection.execute(
                    "INSERT INTO crafting_systems VALUES(?,?,?,?,?)",
                    (system_id, name, classification, support, evidence),
                )

            pages_by_category = {page.category.id: page for page in pages}
            for category in categories:
                page = pages_by_category.get(category.id)
                fetched_at = page.retrieved_at if page else "unavailable"
                page_hash = page.source_hash if page else ""
                reference_id = category.id
                connection.execute(
                    "INSERT INTO source_references VALUES(?,?,?,?,?,?,?)",
                    (
                        reference_id,
                        "TLIDB",
                        category.url,
                        fetched_at,
                        "SS14 — Tartarus (site season label; community data)",
                        "community_reference_season_unverified",
                        page_hash,
                    ),
                )
                connection.execute(
                    "INSERT INTO equipment_categories VALUES(?,?,?,?,?,?,?,?)",
                    (
                        category.id,
                        category.source_category_id,
                        category.name,
                        category.url,
                        category.source_href,
                        category.group_label,
                        "community_reference_season_unverified",
                        reference_id,
                    ),
                )

            for detail_page in detail_pages:
                detail_reference_id = "tlidb-item-detail:" + hashlib.sha256(
                    detail_page.url.encode("utf-8")
                ).hexdigest()[:20]
                connection.execute(
                    "INSERT INTO source_references VALUES(?,?,?,?,?,?,?)",
                    (
                        detail_reference_id,
                        "TLIDB",
                        detail_page.url,
                        detail_page.retrieved_at,
                        "SS14 — Tartarus (site season label; community data)",
                        "community_reference_season_unverified",
                        detail_page.sha256,
                    ),
                )
            total_bases = total_tiers = total_source_rows = 0
            family_records: dict[str, object] = {}
            pool_records: dict[str, tuple[str, object]] = {}
            for page in pages:
                category = page.category
                for section in page.sections:
                    connection.execute(
                        "INSERT INTO category_sections VALUES(?,?,?,?,?,?,?,?,?)",
                        (
                            section.id,
                            section.category_id,
                            section.title,
                            section.section_type,
                            section.announced_count,
                            section.discovered_record_count,
                            section.source_tab_id,
                            section.source_url,
                            section.source_hash,
                        ),
                    )
                    for system_id, (_, _, evidence) in CRAFTING_SYSTEMS.items():
                        applies = (
                            system_id == "tlidb:standard-craft" and section.section_type == "craft"
                            or system_id == "tlidb:graft" and section.section_type == "special_craft"
                            or system_id == "tlidb:corrosion" and section.section_type == "legendary_corroded"
                            or system_id == "tlidb:gear-empowerment" and section.section_type == "gear_empowerment"
                        )
                        if applies:
                            connection.execute(
                                "INSERT OR IGNORE INTO category_crafting_systems VALUES(?,?,?,?)",
                                (category.id, system_id, section.title, category.url),
                            )

                legacy_by_id = {str(row["id"]): row for row in legacy}
                for record in page.bases:
                    base_id = _compatibility_id(record, legacy, used_base_ids)
                    used_base_ids.add(base_id)
                    prior = legacy_by_id.get(base_id, {})
                    connection.execute(
                        """INSERT INTO equipment_bases VALUES(
                            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                        )""",
                        (
                            base_id,
                            record.id,
                            category.id,
                            record.source_item_id,
                            record.name,
                            record.section_id,
                            record.record_kind,
                            record.crafting_class,
                            record.character_level_requirement,
                            record.character_level_requirement_raw,
                            prior.get("minimum_item_level"),
                            record.equipment_type,
                            record.hands if record.hands is not None else prior.get("hands"),
                            prior.get("prefix_limit"),
                            prior.get("suffix_limit"),
                            str(prior.get("limit_status", "unknown")),
                            _json(prior.get("restrictions", [])),
                            _json(record.fields_missing),
                            record.source_url,
                            record.source_section,
                            record.source_row_key,
                            record.verification_status,
                            record.classification_evidence,
                        ),
                    )
                    for ordinal, prop in enumerate(record.properties):
                        connection.execute(
                            "INSERT INTO base_properties(base_id,ordinal,source_modifier_id,description,description_html) VALUES(?,?,?,?,?)",
                            (
                                base_id,
                                ordinal,
                                prop.get("source_modifier_id"),
                                prop.get("description", ""),
                                prop.get("description_html", ""),
                            ),
                        )
                    if record.crafting_system_id:
                        connection.execute(
                            "INSERT OR IGNORE INTO base_crafting_systems VALUES(?,?,?,?,?)",
                            (
                                base_id,
                                record.crafting_system_id,
                                record.classification_evidence or "Source section identifies the system.",
                                record.source_url,
                                record.source_section,
                            ),
                        )
                    total_bases += 1

                for tier in page.tiers:
                    pool_records[tier.pool_id] = (category.id, tier)
                    family_records[tier.family_id] = tier
                for row in page.source_rows:
                    connection.execute(
                        "INSERT INTO source_table_rows VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            row.id,
                            row.category_id,
                            row.section_id,
                            row.source_table_id,
                            row.source_table_name,
                            row.row_number,
                            _json(row.headers),
                            _json(row.values),
                            _json(row.values_html),
                            row.source_url,
                            row.source_section,
                            row.source_row_key,
                        ),
                    )
                    total_source_rows += 1

            for pool_id, (category_id, tier) in pool_records.items():
                section_id = pool_id.split(":pool:", 1)[1].rsplit(":", 1)[0]
                connection.execute(
                    "INSERT INTO affix_pools VALUES(?,?,?,?,?,?)",
                    (
                        pool_id,
                        category_id,
                        section_id,
                        tier.crafting_system_id,
                        tier.group,
                        tier.source_table,
                    ),
                )
            for family_id, tier in family_records.items():
                connection.execute(
                    "INSERT INTO affix_families VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        family_id,
                        tier.pool_id,
                        tier.family_source_id,
                        tier.display_name,
                        tier.family_grouping_status,
                        tier.library,
                        tier.library_category,
                        tier.source_section,
                        tier.source_url,
                    ),
                )
            for page in pages:
                for tier in page.tiers:
                    connection.execute(
                        "INSERT INTO affix_tiers VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            tier.id,
                            tier.family_id,
                            tier.source_modifier_id,
                            tier.tier,
                            tier.description,
                            tier.requirement_level,
                            tier.requirement_level_raw,
                            tier.weight_raw,
                            tier.weight_parse_status,
                            tier.source_url,
                            tier.source_section,
                            tier.source_table,
                            tier.source_row_key,
                            tier.source_row_number,
                        ),
                    )
                    total_tiers += 1

            counts = {
                "categories": len(categories),
                "processed_pages": processed_page_count,
                "bases": total_bases,
                "affix_families": len(family_records),
                "affix_tiers": total_tiers,
                "source_table_rows": total_source_rows,
            }
            for key, value in counts.items():
                connection.execute("INSERT INTO metadata(key,value) VALUES(?,?)", (key, str(value)))
            connection.execute(
                "INSERT INTO metadata(key,value) VALUES(?,?)",
                ("item_detail_pages_inspected", str(len(detail_pages))),
            )
            connection.execute(
                """INSERT INTO import_manifest VALUES(1,?,?,?,?,?,?,?,?,?,?)""",
                (
                    _now(),
                    "https://tlidb.com/en/",
                    homepage_hash,
                    len(categories),
                    processed_page_count,
                    total_bases,
                    total_tiers,
                    total_source_rows,
                    SEASON_REFERENCE,
                    "community_reference_season_unverified",
                ),
            )
            connection.commit()
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise sqlite3.IntegrityError(f"SQLite integrity check failed: {integrity}")
            foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_key_errors:
                raise sqlite3.IntegrityError(f"SQLite has foreign key errors: {foreign_key_errors[:10]}")
        temporary.replace(destination)
        return counts
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
