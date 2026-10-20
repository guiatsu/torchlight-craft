"""Integrity checks for generated catalog databases and import reports."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any


_NUMBER_RANGE_RE = re.compile(
    r"\(\s*([+-]?)\s*\d+(?:[.,]\d+)?\s*(?:[–—-]\s*[+-]?\s*\d+(?:[.,]\d+)?)?\s*\)(%?)"
)
_STANDALONE_RANGE_RE = re.compile(
    r"(?<![A-Za-z])([+-]?)\s*\d+(?:[.,]\d+)?\s*[–—-]\s*[+-]?\s*\d+(?:[.,]\d+)?(%?)"
)
_NUMBER_RE = re.compile(r"(?<![A-Za-z])([+-]?)\s*\d+(?:[.,]\d+)?(%?)")


def _semantic_signature(description: str) -> str:
    value = _NUMBER_RANGE_RE.sub(
        lambda match: f"{match.group(1)}#{match.group(2)}", description.casefold()
    )
    value = _STANDALONE_RANGE_RE.sub(
        lambda match: f"{match.group(1)}#-#{match.group(2)}", value
    )
    value = _NUMBER_RE.sub(lambda match: f"{match.group(1)}#{match.group(2)}", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*([,;])\s*", r"\1 ", value)
    return value.strip()


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
            if version != 3:
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
            duplicate_tiers = connection.execute(
                """SELECT family_id,tier_label,COUNT(*) AS row_count
                   FROM affix_tiers GROUP BY family_id,tier_label HAVING COUNT(*)>1
                   ORDER BY family_id,tier_label"""
            ).fetchall()
            if duplicate_tiers:
                issues.append({
                    "issue": "duplicate_tier_labels_within_canonical_family",
                    "families": [
                        {"family_id": row[0], "tier_label": row[1], "row_count": row[2]}
                        for row in duplicate_tiers
                    ],
                })
            inconsistent_families: list[dict[str, object]] = []
            for family in connection.execute(
                "SELECT id,semantic_signature,source_modifier_family_id FROM affix_families ORDER BY id"
            ):
                tier_descriptions = connection.execute(
                    "SELECT id,source_modifier_id,description FROM affix_tiers WHERE family_id=? ORDER BY id",
                    (family["id"],),
                ).fetchall()
                signatures = {_semantic_signature(row["description"]) for row in tier_descriptions}
                wrong_modifier_rows = [
                    row["id"] for row in tier_descriptions
                    if row["source_modifier_id"]
                    and family["source_modifier_family_id"]
                    and not row["source_modifier_id"].startswith(family["source_modifier_family_id"])
                ]
                if signatures != {family["semantic_signature"]} or wrong_modifier_rows:
                    inconsistent_families.append({
                        "family_id": family["id"],
                        "stored_signature": family["semantic_signature"],
                        "observed_signatures": sorted(signatures),
                        "modifier_family_mismatches": wrong_modifier_rows,
                    })
            if inconsistent_families:
                issues.append({
                    "issue": "semantically_incompatible_or_misassociated_family_rows",
                    "families": inconsistent_families,
                })
            ids_that_are_labels = connection.execute(
                "SELECT id FROM affix_tiers WHERE id=tier_label ORDER BY id"
            ).fetchall()
            if ids_that_are_labels:
                issues.append({
                    "issue": "tier_record_id_is_only_visual_label",
                    "ids": [row[0] for row in ids_that_are_labels],
                })
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
                "legacy_family_ids_split": connection.execute(
                    """SELECT COUNT(*) FROM (
                         SELECT legacy_family_id FROM affix_families
                         WHERE legacy_family_id IS NOT NULL
                         GROUP BY legacy_family_id HAVING COUNT(DISTINCT id)>1
                       )"""
                ).fetchone()[0],
                "legacy_family_alias_rows": connection.execute(
                    """SELECT COUNT(*) FROM affix_families
                       WHERE legacy_family_id IS NOT NULL AND legacy_family_id<>id"""
                ).fetchone()[0],
            }
            manifest = connection.execute(
                "SELECT base_record_count,affix_tier_count,source_table_row_count FROM import_manifest WHERE id=1"
            ).fetchone()
            if manifest and (manifest[0], manifest[1], manifest[2]) != (
                counts["bases"], counts["tier_rows"], counts["source_table_rows"]
            ):
                issues.append({
                    "issue": "import_manifest_count_mismatch",
                    "manifest": list(manifest),
                    "database": [counts["bases"], counts["tier_rows"], counts["source_table_rows"]],
                })
            metadata_counts = {
                row["key"]: int(row["value"])
                for row in connection.execute("SELECT key,value FROM metadata")
                if row["key"] in {"bases", "affix_tiers", "source_table_rows"}
            }
            for key, expected in (
                ("bases", counts["bases"]),
                ("affix_tiers", counts["tier_rows"]),
                ("source_table_rows", counts["source_table_rows"]),
            ):
                if metadata_counts.get(key) != expected:
                    issues.append({
                        "issue": "metadata_count_mismatch",
                        "record_type": key,
                        "metadata": metadata_counts.get(key),
                        "database": expected,
                    })
    except (sqlite3.Error, OSError, json.JSONDecodeError) as exc:
        issues.append({"issue": "database_read_failed", "detail": str(exc)})
        counts = {}
    return {"valid": not issues, "schema_version": 3, "counts": counts, "issues": issues}


def write_validation_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
