"""Discover equipment categories from TLIDB's live Gear navigation."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

from tools.tlidb.dom import Node, parse_html


TLIDB_HOME = "https://tlidb.com/en/"
TLIDB_HOST = "tlidb.com"
REFERENCE_FILE = Path(__file__).with_name("reference_categories.json")


@dataclass(frozen=True, slots=True)
class EquipmentCategoryLink:
    id: str
    name: str
    url: str
    source_href: str
    source_category_id: str | None
    group_label: str
    source_section: str = "Gear"

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


def _normalize_url(href: str, base_url: str) -> str:
    url = urljoin(base_url, href)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != TLIDB_HOST:
        raise ValueError(f"Unexpected category URL: {url}")
    if not parsed.path.startswith("/en/"):
        raise ValueError(f"Category URL is outside the English catalog: {url}")
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), "", "", ""))


def _gear_card(root: Node) -> Node:
    headers = [
        node for node in root.elements("div")
        if "card-header" in node.classes and node.text().casefold() == "gear"
    ]
    if len(headers) != 1:
        raise ValueError(f"Expected one Gear navigation header, found {len(headers)}.")
    card = headers[0].closest("div", "card")
    if card is None:
        raise ValueError("The Gear navigation header has no containing card.")
    return card


def discover_categories(html: str, base_url: str = TLIDB_HOME) -> list[EquipmentCategoryLink]:
    root = parse_html(html)
    card = _gear_card(root)
    body = next((node for node in card.elements("div") if "card-body" in node.classes), None)
    if body is None:
        raise ValueError("The Gear navigation card has no body.")

    categories: list[EquipmentCategoryLink] = []
    seen_urls: set[str] = set()
    for row in body.elements("div"):
        if "py-1" not in row.classes:
            continue
        group_label = next(
            (child.text() for child in row.elements("span") if child.text()), ""
        )
        for anchor in row.elements("a"):
            if not anchor.attrs.get("data-i18n", "").startswith("item_type_list|name|"):
                continue
            href = anchor.attrs.get("href", "").strip()
            if not href or href.startswith(("#", "http:", "https:", "//")):
                continue
            url = _normalize_url(href, base_url)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            source_id = anchor.attrs.get("data-i18n", "").rsplit("|", 1)[-1]
            source_id = source_id if source_id.isdigit() else None
            slug = urlparse(url).path.rsplit("/", 1)[-1]
            stable = re.sub(r"[^a-z0-9]+", "-", slug.casefold()).strip("-")
            categories.append(
                EquipmentCategoryLink(
                    id=f"tlidb-category-{stable}",
                    name=anchor.text(),
                    url=url,
                    source_href=href,
                    source_category_id=source_id,
                    group_label=group_label,
                )
            )
    if not categories:
        raise ValueError("No equipment categories were found under Gear.")
    return categories


def compare_reference_categories(
    categories: list[EquipmentCategoryLink], reference_file: Path = REFERENCE_FILE
) -> dict[str, list[str]]:
    control = json.loads(reference_file.read_text(encoding="utf-8"))["categories"]
    discovered = [entry.name for entry in categories]
    expected_map = {name.casefold(): name for name in control}
    discovered_map = {name.casefold(): name for name in discovered}
    return {
        "missing_from_site": [
            expected_map[key] for key in expected_map if key not in discovered_map
        ],
        "additional_on_site": [
            name for name in discovered
            if name.casefold() not in expected_map
        ],
        "duplicate_reference_names": [
            name for index, name in enumerate(discovered) if name in discovered[:index]
        ],
    }


def discovery_report(
    categories: list[EquipmentCategoryLink],
    *,
    retrieved_at: str,
    source_hash: str,
) -> dict[str, object]:
    comparison = compare_reference_categories(categories)
    return {
        "schema_version": 1,
        "source_url": TLIDB_HOME,
        "source_site": "TLIDB",
        "retrieved_at": retrieved_at,
        "source_sha256": source_hash,
        "category_count": len(categories),
        "reference_category_count": len(
            json.loads(REFERENCE_FILE.read_text(encoding="utf-8"))["categories"]
        ),
        "reference_comparison": comparison,
        "categories": [entry.to_dict() for entry in categories],
    }
