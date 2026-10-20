"""Structural parsing for TLIDB equipment and crafting category pages."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from typing import Any
from urllib.parse import urlparse

from tools.tlidb.discovery import EquipmentCategoryLink
from tools.tlidb.dom import Node, parse_html


_COUNT_RE = re.compile(r"/\s*(\d+)\s*$")
_LEVEL_RE = re.compile(r"\b(?:Require|Required)\s+(?:Character\s+)?lv\.?\s*(\d+)\b", re.I)
_FAMILY_COMMENT_RE = re.compile(r"<\s*td\s*>\s*(\d+)", re.I)
_MODIFIER_ID_RE = re.compile(r"\d+")
_UNKNOWN_TOKENS = {"-", "—", "–", "?", "n/a", "unknown", ""}


@dataclass(frozen=True, slots=True)
class EquipmentBaseRecord:
    id: str
    category_id: str
    category_name: str
    source_item_id: str
    name: str
    section_id: str
    section_name: str
    record_kind: str
    crafting_class: str
    crafting_system_id: str | None
    character_level_requirement: int | None
    character_level_requirement_raw: str | None
    equipment_type: str | None
    hands: int | None
    properties: tuple[dict[str, str | None], ...]
    fields_missing: tuple[str, ...]
    source_url: str
    source_section: str
    source_row_key: str
    verification_status: str
    classification_evidence: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AffixTierRecord:
    id: str
    pool_id: str
    crafting_system_id: str
    family_id: str
    family_source_id: str | None
    source_modifier_family_id: str | None
    semantic_signature: str
    legacy_family_id: str | None
    family_grouping_status: str
    display_name: str
    group: str
    library: str | None
    library_category: str | None
    tier: str | None
    description: str
    requirement_level: int | None
    requirement_level_raw: str | None
    weight_raw: str | None
    weight_parse_status: str
    source_modifier_id: str | None
    source_url: str
    source_section: str
    source_table: str
    source_row_key: str
    source_row_number: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CategorySection:
    id: str
    category_id: str
    title: str
    section_type: str
    announced_count: int | None
    discovered_record_count: int
    source_tab_id: str
    source_url: str
    source_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SourceTableRow:
    id: str
    category_id: str
    section_id: str
    source_table_id: str
    source_table_name: str
    row_number: int
    headers: tuple[str, ...]
    values: tuple[str, ...]
    values_html: tuple[str, ...]
    source_url: str
    source_section: str
    source_row_key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParsedCategoryPage:
    category: EquipmentCategoryLink
    source_hash: str
    retrieved_at: str
    sections: list[CategorySection] = field(default_factory=list)
    bases: list[EquipmentBaseRecord] = field(default_factory=list)
    tiers: list[AffixTierRecord] = field(default_factory=list)
    source_rows: list[SourceTableRow] = field(default_factory=list)
    errors: list[dict[str, str | int | None]] = field(default_factory=list)
    unresolved: list[dict[str, str | int | None]] = field(default_factory=list)
    craft_tables_discovered: int = 0
    craft_tables_parsed: int = 0
    source_tables_discovered: int = 0


@dataclass(frozen=True, slots=True)
class ParsedItemDetailPage:
    title: str
    requirement_levels: tuple[int, ...]
    properties: tuple[dict[str, str | None], ...]


def _find_by_id(root: Node, node_id: str) -> Node | None:
    return next((node for node in root.elements() if node.attrs.get("id") == node_id), None)


def _section_kind(title: str, index: int, category: EquipmentCategoryLink) -> str:
    clean = " ".join(title.casefold().split())
    title_without_count = re.sub(r"\s*/\s*\d+\s*$", "", title).strip()
    if "legendary" in clean and "corroded" in clean:
        return "legendary_corroded"
    if "legendary" in clean:
        return "legendary"
    if "graft" in clean:
        return "special_craft"
    if "craft" in clean:
        return "craft"
    if "gear empowerment" in clean or "empowerment" in clean:
        return "gear_empowerment"
    if title_without_count.casefold() == category.name.casefold():
        return "base_list"
    # The dynamically discovered Ethereal Prism page calls its equipment
    # section simply "Item". Other tabs with item links are not bases unless
    # their section title identifies them as such.
    if title_without_count.casefold() == "item":
        return "base_list"
    return "other"


def _section_tabs(root: Node) -> list[tuple[str, str, Node]]:
    nav = next((node for node in root.elements("ul") if "nav-tabs" in node.classes), None)
    result: list[tuple[str, str, Node]] = []
    if nav:
        for anchor in nav.elements("a"):
            target = anchor.attrs.get("href", "")
            if not target.startswith("#"):
                continue
            node_id = target[1:]
            pane = _find_by_id(root, node_id)
            if pane:
                result.append((node_id, anchor.text(), pane))
    if result:
        return result
    panes = [node for node in root.elements("div") if "tab-pane" in node.classes]
    return [(node.attrs.get("id", f"section-{i}"), node.attrs.get("id", ""), node) for i, node in enumerate(panes)]


def _count_from_title(title: str) -> int | None:
    match = _COUNT_RE.search(title)
    return int(match.group(1)) if match else None


def _record_id(
    category: EquipmentCategoryLink,
    source_item_id: str,
    kind: str,
    identity_suffix: str | None = None,
) -> str:
    base = f"{category.id}:{kind}:{source_item_id}"
    return f"{base}:variant:{identity_suffix}" if identity_suffix else base


def _card_identity_text(anchor: Node) -> str:
    card = anchor.closest("div", "col") or anchor.parent
    return " ".join((card.text() if card else anchor.text()).split())


def _base_from_anchor(
    anchor: Node,
    category: EquipmentCategoryLink,
    section_id: str,
    section_name: str,
    record_kind: str,
    *,
    group_label: str,
    crafting_class: str,
    crafting_system_id: str | None,
    evidence: str | None,
    identity_suffix: str | None,
) -> EquipmentBaseRecord:
    source_item_id = anchor.attrs.get("href", "").split("?", 1)[0].rsplit("/", 1)[-1]
    card = anchor.closest("div", "col") or anchor.parent
    card_text = card.text() if card else anchor.text()
    level_match = _LEVEL_RE.search(card_text)
    level_raw = level_match.group(1) if level_match else None
    props = []
    if card:
        for node in card.elements("span"):
            modifier_id = node.attrs.get("data-modifier-id")
            if not modifier_id:
                continue
            props.append(
                {
                    "source_modifier_id": modifier_id,
                    "description": node.text(),
                    "description_html": node.inner_html(),
                }
            )
    equipment_type = group_label or category.name
    card_lower = card_text.casefold()
    if "two-handed" in card_lower:
        equipment_type = "Two-Handed"
    elif "one-handed" in card_lower:
        equipment_type = "One-Handed"
    hands = (
        2 if equipment_type and "two-handed" in equipment_type.casefold()
        else 1 if equipment_type and "one-handed" in equipment_type.casefold()
        else None
    )
    missing = []
    if level_raw is None:
        missing.append("character_level_requirement")
    if not props:
        missing.append("properties")
    source_row_key = source_item_id or f"{section_id}:row:{anchor.text()}"
    return EquipmentBaseRecord(
        id=_record_id(category, source_item_id or source_row_key, record_kind, identity_suffix),
        category_id=category.id,
        category_name=category.name,
        source_item_id=source_item_id,
        name=anchor.text(),
        section_id=section_id,
        section_name=section_name,
        record_kind=record_kind,
        crafting_class=crafting_class,
        crafting_system_id=crafting_system_id,
        character_level_requirement=int(level_raw) if level_raw else None,
        character_level_requirement_raw=level_raw,
        equipment_type=equipment_type,
        hands=hands,
        properties=tuple(props),
        fields_missing=tuple(missing),
        source_url=category.url,
        source_section=section_name,
        source_row_key=source_row_key,
        verification_status="community_reference_season_unverified",
        classification_evidence=evidence,
    )


def _base_anchors(pane: Node) -> list[Node]:
    anchors: list[Node] = []
    seen: set[tuple[str, str]] = set()
    for anchor in pane.elements("a"):
        href = anchor.attrs.get("href", "").split("?", 1)[0]
        # Modifier and component links inside data tables are not equipment
        # cards. Several TLIDB cards also render the same item link more than
        # once, so use the source href as the page-local identity.
        if not anchor.attrs.get("data-hover") or not anchor.text() or anchor.closest("td"):
            continue
        identity = (href, _card_identity_text(anchor))
        if identity in seen:
            continue
        seen.add(identity)
        anchors.append(anchor)
    return anchors


def _family_source_id(row: Node) -> str | None:
    for node in row.elements():
        if node.tag != "#comment":
            continue
        match = _FAMILY_COMMENT_RE.search(node.attrs.get("text", ""))
        if match:
            return match.group(1)
    return None


def _modifier_source_id(row: Node) -> str | None:
    for node in row.elements():
        if node.tag == "span" and node.attrs.get("data-modifier-id"):
            value = node.attrs["data-modifier-id"]
            if _MODIFIER_ID_RE.fullmatch(value):
                return value
    return None


def _parse_weight(raw: str | None) -> tuple[str | None, str]:
    if raw is None or raw.strip().casefold() in _UNKNOWN_TOKENS:
        return None, "missing"
    value = raw.strip()
    # Store the source exactly; this status only records whether it is a plain
    # non-negative integer, not whether a craft mechanic uses it as a chance.
    if re.fullmatch(r"\d+", value):
        return value, "parsed_integer"
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+", value):
        return value, "parsed_integer_grouped"
    return value, "unparsed"


def _parse_requirement(raw: str | None) -> tuple[int | None, str | None]:
    if raw is None or raw.strip().casefold() in _UNKNOWN_TOKENS:
        return None, raw
    value = raw.strip()
    if re.fullmatch(r"\d+", value):
        return int(value), value
    return None, value


def _caption(table: Node) -> str:
    caption = next((node for node in table.elements("caption")), None)
    return caption.text() if caption else ""


def _group_from_caption(caption: str) -> str | None:
    clean = caption.casefold().replace("-", "").strip()
    if clean in {"prefix", "prefixes", "pre fix"}:
        return "prefix"
    if clean in {"suffix", "suffixes"}:
        return "suffix"
    return None


def _library_category(value: str) -> tuple[str | None, str | None]:
    raw = value.strip()
    folded = raw.casefold()
    for category in ("Basic", "Advanced", "Ultimate"):
        if category.casefold() in folded:
            return category, raw or None
    return None, raw or None


def _family_display_name(description: str) -> str:
    name = re.sub(r"\([^)]*\)", "…", description)
    name = re.sub(r"(?<![A-Za-z])\+?\d+(?:[.,]\d+)?%?", "…", name)
    name = re.sub(r"\s+", " ", name).strip(" …")
    return name or description


_NUMERIC_RANGE_RE = re.compile(
    r"\(\s*([+-]?)\s*\d+(?:[.,]\d+)?\s*(?:[–—-]\s*[+-]?\s*\d+(?:[.,]\d+)?)?\s*\)(%?)"
)
_STANDALONE_RANGE_RE = re.compile(
    r"(?<![A-Za-z])([+-]?)\s*\d+(?:[.,]\d+)?\s*[–—-]\s*[+-]?\s*\d+(?:[.,]\d+)?(%?)"
)
_NUMBER_RE = re.compile(r"(?<![A-Za-z])([+-]?)\s*\d+(?:[.,]\d+)?(%?)")


def _semantic_signature(description: str) -> str:
    """Normalize values while retaining the affix property and its sign."""
    normalized = _NUMERIC_RANGE_RE.sub(
        lambda match: f"{match.group(1)}#{match.group(2)}", description.casefold()
    )
    normalized = _STANDALONE_RANGE_RE.sub(
        lambda match: f"{match.group(1)}#-#{match.group(2)}", normalized
    )
    normalized = _NUMBER_RE.sub(lambda match: f"{match.group(1)}#{match.group(2)}", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\s*([,;])\s*", r"\1 ", normalized)
    return normalized.strip()


def _modifier_family_id(source_modifier_id: str | None) -> str | None:
    if source_modifier_id and len(source_modifier_id) > 2:
        return source_modifier_id[:-2]
    return source_modifier_id


def _reconcile_family_ids(records: list[AffixTierRecord]) -> list[AffixTierRecord]:
    """Split source comments that contain multiple modifier families.

    TLIDB's row comment is useful provenance, but it is broader than a semantic
    affix family for some tables. Keep that old key as an explicit alias target
    and derive canonical IDs from the table, modifier family and property text.
    """
    identities_by_legacy: dict[str, set[tuple[str, str, str, str]]] = {}
    for record in records:
        if not record.legacy_family_id:
            continue
        identity = (
            record.pool_id,
            record.group,
            record.source_modifier_family_id or "missing-modifier-family",
            record.semantic_signature,
        )
        identities_by_legacy.setdefault(record.legacy_family_id, set()).add(identity)

    result: list[AffixTierRecord] = []
    for record in records:
        legacy_id = record.legacy_family_id
        if legacy_id is None:
            result.append(record)
            continue
        identities = identities_by_legacy[legacy_id]
        identity = (
            record.pool_id,
            record.group,
            record.source_modifier_family_id or "missing-modifier-family",
            record.semantic_signature,
        )
        if len(identities) == 1:
            canonical_id = legacy_id
        else:
            digest = hashlib.sha256("\x1f".join(identity).encode("utf-8")).hexdigest()[:16]
            canonical_id = f"{legacy_id}:split:{digest}"
        result.append(replace(record, family_id=canonical_id))
    return result


def _craft_rows(
    pane: Node,
    category: EquipmentCategoryLink,
    section_id: str,
    section_name: str,
    page_hash: str,
    crafting_system_id: str,
    errors: list[dict[str, str | int | None]],
    unresolved: list[dict[str, str | int | None]],
) -> tuple[list[AffixTierRecord], int, int]:
    records: list[AffixTierRecord] = []
    tables = list(pane.elements("table"))
    parsed_tables = 0
    for table_index, table in enumerate(tables):
        caption = _caption(table)
        group = _group_from_caption(caption)
        rows = [row for row in table.elements("tr") if "data-tier" in row.attrs]
        if not rows:
            continue
        if group is None:
            errors.append({
                "category": category.name,
                "url": category.url,
                "section": section_name,
                "issue": "craft_table_group_unrecognized",
                "source_table": caption or f"table-{table_index + 1}",
                "row_count": len(rows),
            })
        parsed_tables += 1
        pool_name = caption or f"table-{table_index + 1}"
        pool_id = f"{category.id}:pool:{section_id}:{table_index + 1}"
        fallback_family_ids: dict[str, str] = {}
        for row_number, row in enumerate(rows, 1):
            cells = [child for child in row.children if isinstance(child, Node) and child.tag in {"td", "th"}]
            # Some tables omit cells with no value. Preserve whatever source row
            # exists and report it instead of silently skipping it.
            cell_texts = [cell.text() for cell in cells]
            tier = row.attrs.get("data-tier") or (cell_texts[0] if cell_texts else None)
            description_cell = cells[1] if len(cells) > 1 else None
            description = description_cell.text() if description_cell else ""
            level_raw = cell_texts[2] if len(cell_texts) > 2 else None
            weight_raw, weight_status = _parse_weight(cell_texts[3] if len(cell_texts) > 3 else None)
            library_raw = cell_texts[4] if len(cell_texts) > 4 else None
            library, library_category = _library_category(library_raw or "")
            requirement_level, requirement_raw = _parse_requirement(level_raw)
            source_modifier_id = _modifier_source_id(row)
            source_family_id = _family_source_id(row)
            legacy_family_id = None
            if source_family_id:
                family_id = f"{category.id}:family:{section_id}:{group or 'unknown'}:{library or 'unknown'}:{source_family_id}"
                legacy_family_id = family_id
                grouping_status = "source_family_id"
            else:
                stable_row = source_modifier_id or f"{section_id}:{pool_name}:{group or 'unknown'}:{row_number}"
                family_id = fallback_family_ids.setdefault(stable_row, f"{pool_id}:unresolved-family:{stable_row}")
                grouping_status = "pending_source_family_id"
                unresolved.append({
                    "category": category.name,
                    "url": category.url,
                    "section": section_name,
                    "source_row_key": source_modifier_id or stable_row,
                    "issue": "affix_family_id_missing",
                })
            if not description.strip():
                errors.append({
                    "category": category.name,
                    "url": category.url,
                    "section": section_name,
                    "source_table": pool_name,
                    "row": row_number,
                    "issue": "empty_affix_description",
                })
            if weight_status in {"missing", "unparsed"}:
                unresolved.append({
                    "category": category.name,
                    "url": category.url,
                    "section": section_name,
                    "source_row_key": source_modifier_id or f"{pool_name}:{row_number}",
                    "issue": f"weight_{weight_status}",
                    "weight_raw": weight_raw,
                })
            if library is None:
                unresolved.append({
                    "category": category.name,
                    "url": category.url,
                    "section": section_name,
                    "source_row_key": source_modifier_id or f"{pool_name}:{row_number}",
                    "issue": "affix_library_unrecognized",
                    "library_raw": library_raw,
                })
            if requirement_level is None:
                unresolved.append({
                    "category": category.name,
                    "url": category.url,
                    "section": section_name,
                    "source_row_key": source_modifier_id or f"{pool_name}:{row_number}",
                    "issue": "requirement_level_missing_or_unparsed",
                    "requirement_raw": requirement_raw,
                })
            if not source_modifier_id:
                unresolved.append({
                    "category": category.name,
                    "url": category.url,
                    "section": section_name,
                    "source_row_key": f"{pool_name}:{row_number}",
                    "issue": "modifier_source_id_missing",
                })
            if group is None:
                unresolved.append({
                    "category": category.name,
                    "url": category.url,
                    "source_row_key": source_modifier_id or f"{pool_name}:{row_number}",
                    "issue": "affix_group_unrecognized",
                    "source_table": pool_name,
                })
            family_name = _family_display_name(description)
            row_key = source_modifier_id or f"{section_id}:{pool_name}:{row_number}"
            record_id = f"{category.id}:tier:{section_id}:{source_modifier_id or row_key}"
            records.append(
                AffixTierRecord(
                    id=record_id,
                    pool_id=pool_id,
                    crafting_system_id=crafting_system_id,
                    family_id=family_id,
                    family_source_id=source_family_id,
                    source_modifier_family_id=_modifier_family_id(source_modifier_id),
                    semantic_signature=_semantic_signature(description),
                    legacy_family_id=legacy_family_id,
                    family_grouping_status=grouping_status,
                    display_name=family_name,
                    group=group or "unknown",
                    library=library,
                    library_category=library_category,
                    tier=f"T{tier}" if tier and not tier.upper().startswith("T") else tier,
                    description=description,
                    requirement_level=requirement_level,
                    requirement_level_raw=requirement_raw,
                    weight_raw=weight_raw,
                    weight_parse_status=weight_status,
                    source_modifier_id=source_modifier_id,
                    source_url=category.url,
                    source_section=section_name,
                    source_table=pool_name,
                    source_row_key=row_key,
                    source_row_number=row_number,
                )
            )
    return records, len(tables), parsed_tables


def _source_table_rows(
    pane: Node,
    category: EquipmentCategoryLink,
    section_id: str,
    section_name: str,
    *,
    include_tier_rows: bool = False,
) -> tuple[list[SourceTableRow], int]:
    output: list[SourceTableRow] = []
    tables = list(pane.elements("table"))
    for table_index, table in enumerate(tables, 1):
        header_rows = [row for row in table.elements("tr") if any(
            isinstance(child, Node) and child.tag == "th" for child in row.children
        )]
        headers = tuple(
            cell.text()
            for row in header_rows
            for cell in row.children
            if isinstance(cell, Node) and cell.tag == "th"
        )
        table_id = table.attrs.get("data-table-id") or f"table-{table_index}"
        rows = [
            row for row in table.elements("tr")
            if (include_tier_rows or "data-tier" not in row.attrs)
            and any(isinstance(child, Node) and child.tag == "td" for child in row.children)
        ]
        for row_number, row in enumerate(rows, 1):
            cells = [child for child in row.children if isinstance(child, Node) and child.tag == "td"]
            values = tuple(cell.text() for cell in cells)
            values_html = tuple(cell.inner_html() for cell in cells)
            row_key = f"{table_id}:{row_number}"
            output.append(
                SourceTableRow(
                    id=f"{category.id}:source-row:{section_id}:{row_key}",
                    category_id=category.id,
                    section_id=section_id,
                    source_table_id=table_id,
                    source_table_name=_caption(table) or section_name,
                    row_number=row_number,
                    headers=headers,
                    values=values,
                    values_html=values_html,
                    source_url=category.url,
                    source_section=section_name,
                    source_row_key=row_key,
                )
            )
    return output, len(tables)


def _source_card_rows(
    pane: Node,
    category: EquipmentCategoryLink,
    section_id: str,
    section_name: str,
) -> list[SourceTableRow]:
    """Preserve non-table source records such as the 97 Blending Rituals."""
    output: list[SourceTableRow] = []
    cards = [
        node for node in pane.elements("div")
        if {"d-flex", "border-top", "rounded"}.issubset(node.classes)
        and any(anchor.attrs.get("data-hover") for anchor in node.elements("a"))
    ]
    for row_number, card in enumerate(cards, 1):
        value = card.text()
        row_key = f"card:{row_number}"
        output.append(
            SourceTableRow(
                id=f"{category.id}:source-row:{section_id}:{row_key}",
                category_id=category.id,
                section_id=section_id,
                source_table_id="source-cards",
                source_table_name=section_name,
                row_number=row_number,
                headers=(),
                values=(value,),
                values_html=(card.inner_html(),),
                source_url=category.url,
                source_section=section_name,
                source_row_key=row_key,
            )
        )
    return output


def parse_category_page(
    category: EquipmentCategoryLink,
    html: str,
    *,
    retrieved_at: str,
    source_hash: str,
) -> ParsedCategoryPage:
    root = parse_html(html)
    parsed = ParsedCategoryPage(category=category, source_hash=source_hash, retrieved_at=retrieved_at)
    tabs = _section_tabs(root)
    if not tabs:
        parsed.errors.append({"category": category.name, "url": category.url, "issue": "no_page_sections_found"})
        return parsed

    parsed_section_data: list[tuple[CategorySection, Node, int]] = []
    for index, (tab_id, title, pane) in enumerate(tabs):
        display_title = title or pane.attrs.get("id", tab_id)
        section_kind = _section_kind(display_title, index, category)
        announced = _count_from_title(display_title)
        section_id = f"{category.id}:section:{tab_id}"
        anchors = _base_anchors(pane) if section_kind in {
            "base_list", "legendary", "legendary_corroded", "special_craft"
        } else []
        raw_table_rows, raw_table_count = _source_table_rows(
            pane,
            category,
            section_id,
            display_title,
            include_tier_rows=section_kind not in {"craft", "special_craft"},
        )
        card_rows = _source_card_rows(pane, category, section_id, display_title) if section_kind == "other" else []
        if section_kind in {"base_list", "legendary", "legendary_corroded", "special_craft"}:
            discovered_count = len(anchors)
        else:
            discovered_count = len(raw_table_rows) + len(card_rows)
        section = CategorySection(
            id=section_id,
            category_id=category.id,
            title=display_title,
            section_type=section_kind,
            announced_count=announced,
            discovered_record_count=discovered_count,
            source_tab_id=tab_id,
            source_url=category.url,
            source_hash=source_hash,
        )
        parsed.sections.append(section)
        parsed_section_data.append((section, pane, index))
        parsed.source_rows.extend(raw_table_rows)
        parsed.source_rows.extend(card_rows)
        parsed.source_tables_discovered += raw_table_count

    standard_tables = [
        (section, pane)
        for section, pane, _ in parsed_section_data
        if section.section_type == "craft"
    ]
    has_standard_rows = any(
        row for _, pane in standard_tables for row in pane.elements("tr") if "data-tier" in row.attrs
    )
    has_graft_section = any(section.section_type == "special_craft" for section, _, _ in parsed_section_data)

    for section, pane, _ in parsed_section_data:
        if section.section_type in {"base_list", "legendary", "legendary_corroded", "special_craft"}:
            if section.section_type == "base_list":
                record_kind = "base"
                if has_standard_rows:
                    craft_class = "standard_craftable"
                    system_id = "tlidb:standard-craft"
                    evidence = "A category-level Craft tab contains tiered Prefix/Suffix tables."
                elif has_graft_section:
                    craft_class = "special_craftable"
                    system_id = "tlidb:graft"
                    evidence = "A category-level Graft tab is present."
                else:
                    craft_class = "unknown"
                    system_id = None
                    evidence = None
            elif section.section_type == "legendary_corroded":
                record_kind = "legendary_corroded_variant"
                craft_class = "special_craftable"
                system_id = "tlidb:corrosion"
                evidence = "The source lists a Corroded legendary variant."
            elif section.section_type == "legendary":
                record_kind = "legendary"
                craft_class = "unknown"
                system_id = None
                evidence = "Listed in a Legendary Gear section; no conventional crafting classification inferred."
            else:
                record_kind = "special_equipment"
                craft_class = "special_craftable" if has_graft_section else "unknown"
                system_id = "tlidb:graft" if has_graft_section else None
                evidence = "A category-level Graft tab is present." if has_graft_section else None
            anchors = _base_anchors(pane)
            href_counts = Counter(
                anchor.attrs.get("href", "").split("?", 1)[0].rsplit("/", 1)[-1]
                for anchor in anchors
            )
            for anchor in anchors:
                source_item_id = anchor.attrs.get("href", "").split("?", 1)[0].rsplit("/", 1)[-1]
                identity_suffix = None
                if href_counts[source_item_id] > 1:
                    identity_suffix = hashlib.sha256(_card_identity_text(anchor).encode("utf-8")).hexdigest()[:16]
                parsed.bases.append(
                    _base_from_anchor(
                        anchor,
                        category,
                        section.id,
                        section.title,
                        record_kind,
                    group_label=category.group_label,
                        crafting_class=craft_class,
                        crafting_system_id=system_id,
                        evidence=evidence,
                        identity_suffix=identity_suffix,
                    )
                )

        if section.section_type == "legendary" and not _base_anchors(pane):
            parsed.unresolved.append({
                "category": category.name,
                "url": category.url,
                "section": section.title,
                "issue": "legendary_section_has_no_recognized_item_cards",
            })
        if section.section_type == "legendary_corroded" and not _base_anchors(pane):
            parsed.unresolved.append({
                "category": category.name,
                "url": category.url,
                "section": section.title,
                "issue": "corroded_section_has_no_recognized_item_cards",
            })

    for section, pane, _ in parsed_section_data:
        if section.section_type in {"craft", "special_craft"}:
            tiers, discovered_tables, parsed_tables = _craft_rows(
                pane,
                category,
                section.id,
                section.title,
                source_hash,
                "tlidb:graft" if section.section_type == "special_craft" else "tlidb:standard-craft",
                parsed.errors,
                parsed.unresolved,
            )
            parsed.tiers.extend(tiers)
            parsed.craft_tables_discovered += discovered_tables
            parsed.craft_tables_parsed += parsed_tables
        else:
            # Some special systems embed tier tables under another tab title.
            rows = [row for row in pane.elements("tr") if "data-tier" in row.attrs]
            if rows:
                parsed.unresolved.append({
                    "category": category.name,
                    "url": category.url,
                    "section": section.title,
                    "issue": "tier_rows_in_non_craft_section",
                    "row_count": len(rows),
                })

    parsed.tiers = _reconcile_family_ids(parsed.tiers)

    for section in parsed.sections:
        if section.announced_count is not None and section.discovered_record_count != section.announced_count:
            parsed.errors.append({
                "category": category.name,
                "url": category.url,
                "section": section.title,
                "issue": "announced_record_count_mismatch",
                "announced": section.announced_count,
                "discovered": section.discovered_record_count,
            })
    if not parsed.bases:
        parsed.errors.append({"category": category.name, "url": category.url, "issue": "no_equipment_records_found"})
    return parsed


def parse_item_detail_page(html: str) -> ParsedItemDetailPage:
    """Extract only explicit item requirements and modifier properties."""
    root = parse_html(html)
    title = next((node.text() for node in root.elements("h1") if node.text()), "")
    if not title:
        title = next((node.text() for node in root.elements("title") if node.text()), "")
        title = re.sub(r"\s*-\s*Torchlight: Infinite Wiki\s*$", "", title, flags=re.I).replace("_", " ")

    requirements = tuple(sorted({int(value) for value in _LEVEL_RE.findall(root.text())}))
    properties: list[dict[str, str | None]] = []
    seen: set[tuple[str, str]] = set()
    for node in root.elements("span"):
        modifier_id = node.attrs.get("data-modifier-id")
        description = node.text()
        key = (modifier_id or "", description)
        if not modifier_id or not description or key in seen:
            continue
        seen.add(key)
        properties.append({
            "source_modifier_id": modifier_id,
            "description": description,
            "description_html": node.inner_html(),
        })
    return ParsedItemDetailPage(
        title=title,
        requirement_levels=requirements,
        properties=tuple(properties),
    )
