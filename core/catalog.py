"""Local JSON catalog loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from core.models import AffixDefinition, BaseDefinition


class CatalogError(ValueError):
    """Raised when bundled catalog data is invalid."""


@dataclass(frozen=True, slots=True)
class Catalog:
    bases: dict[str, BaseDefinition]
    affixes: dict[str, AffixDefinition]
    sources: dict[str, dict[str, Any]]


def _load_json(name: str) -> dict[str, Any]:
    try:
        return json.loads(files("data").joinpath(name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Could not load local catalog file {name}: {exc}") from exc


def load_catalog() -> Catalog:
    bases_raw = _load_json("bases.json").get("bases", [])
    affixes_raw = _load_json("affixes.json").get("affixes", [])
    sources_raw = _load_json("sources.json").get("sources", [])

    bases = {entry.id: entry for entry in (BaseDefinition.from_dict(row) for row in bases_raw)}
    affixes = {entry.id: entry for entry in (AffixDefinition.from_dict(row) for row in affixes_raw)}
    sources = {str(source["id"]): source for source in sources_raw}

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
    return Catalog(bases=bases, affixes=affixes, sources=sources)
