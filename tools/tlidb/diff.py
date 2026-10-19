"""Compare two normalized TLIDB catalog snapshots by stable source IDs."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


_TABLES = {
    "categories": ("equipment_categories", "id", ("name", "source_url", "group_label")),
    "bases": ("equipment_bases", "source_record_id", ("name", "record_kind", "crafting_class", "character_level_requirement", "equipment_type", "hands")),
    "tiers": ("affix_tiers", "id", ("tier_label", "description", "requirement_level_raw", "weight_raw")),
    "source_table_rows": ("source_table_rows", "id", ("headers_json", "values_json")),
}


def _records(path: Path, table: str, key_column: str, fields: tuple[str, ...]) -> dict[str, tuple[Any, ...]]:
    columns = ",".join((key_column, *fields))
    with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as connection:
        return {str(row[0]): tuple(row[1:]) for row in connection.execute(f"SELECT {columns} FROM {table}")}


def compare_catalogs(before: Path, after: Path) -> dict[str, object]:
    result: dict[str, object] = {"before": str(before), "after": str(after), "tables": {}}
    tables: dict[str, object] = {}
    for name, (table, key, fields) in _TABLES.items():
        old = _records(before, table, key, fields)
        new = _records(after, table, key, fields)
        added = sorted(new.keys() - old.keys())
        removed = sorted(old.keys() - new.keys())
        changed = sorted(key_id for key_id in old.keys() & new.keys() if old[key_id] != new[key_id])
        tables[name] = {
            "before_count": len(old),
            "after_count": len(new),
            "added": added,
            "removed": removed,
            "changed": changed,
        }
    result["tables"] = tables
    return result
