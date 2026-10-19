"""Integrity checks for generated catalog databases and import reports."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def validate_catalog_database(path: Path) -> dict[str, Any]:
    issues: list[dict[str, object]] = []
    if not path.is_file():
        return {"valid": False, "issues": [{"issue": "database_not_found", "path": str(path)}]}
    try:
        with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                issues.append({"issue": "sqlite_integrity_check_failed", "result": integrity})
            for row in connection.execute("PRAGMA foreign_key_check"):
                issues.append({"issue": "foreign_key_violation", "table": row[0], "rowid": row[1]})
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version != 2:
                issues.append({"issue": "unsupported_catalog_schema_version", "version": version})
            duplicate_rows = connection.execute(
                "SELECT id,COUNT(*) FROM equipment_bases GROUP BY id HAVING COUNT(*)>1"
            ).fetchall()
            if duplicate_rows:
                issues.append({"issue": "duplicate_base_ids", "ids": [row[0] for row in duplicate_rows]})
            missing_source = connection.execute(
                """SELECT id FROM equipment_categories c
                   WHERE NOT EXISTS(SELECT 1 FROM source_references s WHERE s.id=c.source_reference_id)"""
            ).fetchall()
            if missing_source:
                issues.append({"issue": "category_source_reference_missing", "ids": [row[0] for row in missing_source]})
            invalid_tiers = connection.execute(
                """SELECT t.id FROM affix_tiers t
                   JOIN affix_families f ON f.id=t.family_id
                   JOIN affix_pools p ON p.id=f.pool_id
                   WHERE t.description='' OR t.tier_label IS NULL OR p.group_name='unknown'"""
            ).fetchall()
            if invalid_tiers:
                issues.append({"issue": "tier_requires_review", "ids": [row[0] for row in invalid_tiers]})
            invalid_weights = connection.execute(
                """SELECT id,weight_raw,weight_parse_status FROM affix_tiers
                   WHERE weight_parse_status='parsed_integer' AND (weight_raw IS NULL OR weight_raw NOT GLOB '[0-9]*')"""
            ).fetchall()
            if invalid_weights:
                issues.append({"issue": "weight_parse_mismatch", "ids": [row[0] for row in invalid_weights]})
            counts = {
                "categories": connection.execute("SELECT COUNT(*) FROM equipment_categories").fetchone()[0],
                "bases": connection.execute("SELECT COUNT(*) FROM equipment_bases").fetchone()[0],
                "affix_families": connection.execute("SELECT COUNT(*) FROM affix_families").fetchone()[0],
                "tier_rows": connection.execute("SELECT COUNT(*) FROM affix_tiers").fetchone()[0],
                "source_table_rows": connection.execute("SELECT COUNT(*) FROM source_table_rows").fetchone()[0],
            }
            for table, count_key, fk_column in (
                ("base_properties", "bases", "base_id"),
                ("affix_tiers", "affix_families", "family_id"),
                ("source_table_rows", "equipment_categories", "category_id"),
            ):
                _ = (table, count_key, fk_column)
    except (sqlite3.Error, OSError, json.JSONDecodeError) as exc:
        issues.append({"issue": "database_read_failed", "detail": str(exc)})
        counts = {}
    return {"valid": not issues, "schema_version": 2, "counts": counts, "issues": issues}


def write_validation_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
