"""Load the bundled offline catalog while preserving legacy item references."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Any

from core.models import AffixCategory, AffixDefinition, AffixGroup, BaseDefinition, TierOption


class CatalogError(ValueError):
    """Raised when bundled catalog data is invalid."""


@dataclass(frozen=True, slots=True)
class Catalog:
    bases: dict[str, BaseDefinition]
    affixes: dict[str, AffixDefinition]
    sources: dict[str, dict[str, Any]]
    categories: dict[str, dict[str, Any]] = field(default_factory=dict)
    crafting_systems: dict[str, dict[str, Any]] = field(default_factory=dict)


def _resource_path(name: str):
    return files("data").joinpath(name)


def _load_json(name: str) -> dict[str, Any]:
    try:
        return json.loads(_resource_path(name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Could not load local catalog file {name}: {exc}") from exc


def _legacy_catalog() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    bases = _load_json("bases.json").get("bases", [])
    affixes = _load_json("affixes.json").get("affixes", [])
    sources = {
        str(source["id"]): source
        for source in _load_json("sources.json").get("sources", [])
    }
    return bases, affixes, sources


def _load_json_catalog() -> Catalog:
    bases_raw, affixes_raw, sources = _legacy_catalog()
    bases = {entry.id: entry for entry in (BaseDefinition.from_dict(row) for row in bases_raw)}
    affixes = {entry.id: entry for entry in (AffixDefinition.from_dict(row) for row in affixes_raw)}
    categories: dict[str, dict[str, Any]] = {}
    crafting_systems: dict[str, dict[str, Any]] = {}
    _validate_catalog(bases, affixes, sources, bases_raw, affixes_raw)
    return Catalog(bases=bases, affixes=affixes, sources=sources, categories=categories, crafting_systems=crafting_systems)


def _json_value(raw: str, default: Any) -> Any:
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default


def _load_sqlite_catalog() -> Catalog:
    path = _resource_path("catalog.sqlite3")
    bases_legacy, affixes_legacy, sources = _legacy_catalog()
    try:
        connection = sqlite3.connect(str(path))
        connection.row_factory = sqlite3.Row
        with connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version != 3:
                raise CatalogError(f"Unsupported catalog database schema version: {version}")

            categories = {
                row["id"]: dict(row)
                for row in connection.execute("SELECT * FROM equipment_categories ORDER BY name")
            }
            category_bases: dict[str, list[str]] = {}
            bases: dict[str, BaseDefinition] = {}
            base_rows = connection.execute(
                """SELECT b.*, c.name AS category_name, c.group_label
                   FROM equipment_bases b
                   JOIN equipment_categories c ON c.id=b.category_id
                   ORDER BY c.group_label, c.name, b.name, b.id"""
            ).fetchall()
            properties_by_base: dict[str, list[str]] = {}
            for prop in connection.execute(
                "SELECT base_id,description FROM base_properties ORDER BY base_id,ordinal"
            ):
                properties_by_base.setdefault(prop["base_id"], []).append(prop["description"])

            for row in base_rows:
                base_id = row["id"]
                crafting_class = row["crafting_class"]
                record_kind = row["record_kind"]
                definition = BaseDefinition.from_dict({
                    "id": base_id,
                    "name": row["name"],
                    "category": row["group_label"] or "Other",
                    "subcategory": row["category_name"],
                    "equipment_type": row["equipment_type"] or row["category_name"],
                    "hands": row["hands"],
                    "character_level_requirement": row["character_level_requirement"],
                    "minimum_item_level": row["minimum_item_level"],
                    "prefix_limit": row["prefix_limit"],
                    "suffix_limit": row["suffix_limit"],
                    "limit_status": row["limit_status"],
                    "restrictions": _json_value(row["restrictions_json"], []),
                    "source_id": row["category_id"],
                    "verification_status": row["verification_status"],
                    "crafting_class": crafting_class,
                    "record_kind": record_kind,
                    "classification_evidence": row["classification_evidence"] or "",
                    "source_url": row["source_url"],
                    "source_section": row["source_section"],
                    "source_item_id": row["source_item_id"],
                    "base_properties": properties_by_base.get(base_id, []),
                    "fields_missing": _json_value(row["properties_missing_json"], []),
                    "editor_supported": crafting_class == "standard_craftable" and record_kind == "base",
                })
                bases[base_id] = definition
                category_bases.setdefault(row["category_id"], []).append(base_id)

            # A few v0.1 saves can refer to generic placeholder bases that do
            # not correspond to a TLIDB item. Keep these resolvable but hide
            # them from the new equipment browser.
            for legacy in bases_legacy:
                legacy_id = str(legacy["id"])
                if legacy_id not in bases:
                    bases[legacy_id] = BaseDefinition.from_dict({**legacy, "is_legacy_alias": True})

            systems = {
                row["id"]: dict(row)
                for row in connection.execute("SELECT * FROM crafting_systems ORDER BY id")
            }
            source_refs = {
                row["id"]: dict(row)
                for row in connection.execute("SELECT * FROM source_references ORDER BY id")
            }
            sources.update(source_refs)

            family_rows = connection.execute(
                """SELECT f.*, p.id AS exact_pool_id, p.category_id, p.group_name, p.crafting_system_id,
                          c.verification_status
                   FROM affix_families f
                   JOIN affix_pools p ON p.id=f.pool_id
                   JOIN equipment_categories c ON c.id=p.category_id
                   ORDER BY f.id"""
            ).fetchall()
            tier_rows: dict[str, list[sqlite3.Row]] = {}
            for row in connection.execute(
                """SELECT t.*, f.pool_id, f.library
                   FROM affix_tiers t JOIN affix_families f ON f.id=t.family_id
                   ORDER BY t.family_id, t.source_row_number, t.id"""
            ):
                tier_rows.setdefault(row["family_id"], []).append(row)

            affixes: dict[str, AffixDefinition] = {}
            for family in family_rows:
                source_system = family["crafting_system_id"]
                group = family["group_name"]
                if group not in {AffixGroup.PREFIX.value, AffixGroup.SUFFIX.value}:
                    # Keep malformed groups in the normalized database and
                    # audit; they cannot be represented as editable affixes.
                    continue
                category_name = family["library"]
                if category_name not in {item.value for item in AffixCategory}:
                    continue
                compatible_classes = {
                    "tlidb:standard-craft": {"standard_craftable"},
                    "tlidb:graft": {"special_craftable"},
                    "tlidb:corrosion": {"special_craftable"},
                    "tlidb:gear-empowerment": {"special_craftable"},
                }.get(source_system, set())
                compatible_kinds = {
                    base.id for base in bases.values()
                    if not base.is_legacy_alias
                    and base.source_id == family["category_id"]
                    and base.crafting_class in compatible_classes
                    and (
                        source_system != "tlidb:standard-craft"
                        or base.record_kind == "base"
                    )
                    and (
                        source_system != "tlidb:corrosion"
                        or base.record_kind == "legendary_corroded_variant"
                    )
                }
                tiers = tuple(
                    TierOption(
                        id=row["id"],
                        item_level_required=row["requirement_level"],
                        value_range=row["description"],
                        tier_label=row["tier_label"] or "Unknown",
                        verification_status=family["verification_status"],
                        requirement_level_raw=row["requirement_level_raw"],
                        weight_raw=row["weight_raw"],
                        weight_parse_status=row["weight_parse_status"],
                        library=row["library"] or "",
                        source_url=row["source_url"],
                        source_section=row["source_section"],
                        source_table=row["source_table"],
                        source_row_key=row["source_row_key"],
                    )
                    for row in tier_rows.get(family["id"], [])
                )
                affixes[family["id"]] = AffixDefinition(
                    id=family["id"],
                    name=family["display_name"],
                    group=AffixGroup(group),
                    category=AffixCategory(category_name),
                    base_ids=tuple(sorted(compatible_kinds)),
                    tiers=tiers,
                    value_editable=True,
                    source_id=family["category_id"],
                    verification_status=family["verification_status"],
                    compatibility_status=("provisional" if compatible_kinds else "unsupported_or_unmapped"),
                    source_url=family["source_url"],
                    source_section=family["source_section"],
                    source_family_id=family["family_source_id"] or "",
                    family_grouping_status=family["grouping_status"],
                    crafting_system_id=source_system,
                    pool_id=family["exact_pool_id"],
                    semantic_signature=family["semantic_signature"] or "",
                )

            # Older equipment files stored the broad TLIDB comment family ID.
            # If that source key now resolves to several canonical families,
            # keep an explicit read/edit alias containing all original rows.
            # Legacy tier labels are resolved only when they identify one row.
            legacy_groups: dict[str, list[sqlite3.Row]] = {}
            for family in family_rows:
                legacy_id = family["legacy_family_id"]
                if legacy_id and legacy_id != family["id"]:
                    legacy_groups.setdefault(legacy_id, []).append(family)
            for legacy_id, siblings in legacy_groups.items():
                valid_siblings = [row for row in siblings if row["id"] in affixes]
                child_definitions = [affixes[row["id"]] for row in valid_siblings]
                if not child_definitions or legacy_id in affixes:
                    continue
                first = child_definitions[0]
                tiers = tuple(
                    tier
                    for sibling in valid_siblings
                    for tier in affixes[sibling["id"]].tiers
                )
                descriptions = sorted({definition.name for definition in child_definitions})
                display_name = (
                    descriptions[0]
                    if len(descriptions) == 1
                    else "Ambiguous legacy family: " + " / ".join(descriptions[:3])
                )
                affixes[legacy_id] = AffixDefinition(
                    id=legacy_id,
                    name=display_name,
                    group=first.group,
                    category=first.category,
                    base_ids=tuple(sorted({
                        base_id for definition in child_definitions for base_id in definition.base_ids
                    })),
                    tiers=tiers,
                    value_editable=True,
                    source_id=first.source_id,
                    verification_status=first.verification_status,
                    compatibility_status="ambiguous_legacy_alias",
                    source_url=first.source_url,
                    source_section=first.source_section,
                    source_family_id=first.source_family_id,
                    family_grouping_status="ambiguous_legacy_alias",
                    crafting_system_id=first.crafting_system_id,
                    is_legacy_alias=True,
                    legacy_family_member_ids=tuple(sorted(row["id"] for row in valid_siblings)),
                    pool_id=first.pool_id,
                    semantic_signature=first.semantic_signature,
                )

            # Definitions from v0.1.1 remain addressable by saved items. They
            # are aliases for loading/editing, never fresh selection options.
            for legacy in affixes_legacy:
                legacy_id = str(legacy["id"])
                if legacy_id not in affixes:
                    affixes[legacy_id] = AffixDefinition.from_dict({**legacy, "is_legacy_alias": True})

            _validate_catalog(bases, affixes, sources, list(bases), list(affixes))
            return Catalog(
                bases=bases,
                affixes=affixes,
                sources=sources,
                categories=categories,
                crafting_systems=systems,
            )
    except sqlite3.Error as exc:
        raise CatalogError(f"Could not load local catalog database: {exc}") from exc
    finally:
        if "connection" in locals():
            connection.close()


def _validate_catalog(
    bases: dict[str, BaseDefinition],
    affixes: dict[str, AffixDefinition],
    sources: dict[str, dict[str, Any]],
    bases_raw: list[Any],
    affixes_raw: list[Any],
) -> None:
    if not bases:
        raise CatalogError("The local catalog has no equipment bases.")
    if len(bases) != len(bases_raw) or len(affixes) != len(affixes_raw):
        raise CatalogError("Catalog IDs must be unique.")
    for affix in affixes.values():
        if not affix.tiers:
            raise CatalogError(f"Catalog affix {affix.id} has no tier options.")
        if affix.source_id and affix.source_id not in sources:
            raise CatalogError(f"Catalog affix {affix.id} refers to an unknown source.")
    for base in bases.values():
        if base.source_id and base.source_id not in sources:
            raise CatalogError(f"Catalog base {base.id} refers to an unknown source.")


def load_catalog() -> Catalog:
    """Prefer the generated normalized database, with JSON v0.1 fallback."""
    if _resource_path("catalog.sqlite3").is_file():
        return _load_sqlite_catalog()
    return _load_json_catalog()
