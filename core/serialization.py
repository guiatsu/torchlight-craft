"""Versioned item JSON serialization."""

from __future__ import annotations

from typing import Any

from core.models import EquipmentItem, SCHEMA_VERSION


class SerializationError(ValueError):
    """Raised when an item document is malformed or from a newer schema."""


def serialize_item(item: EquipmentItem) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "item": item.to_dict()}


def deserialize_item(document: dict[str, Any]) -> EquipmentItem:
    if not isinstance(document, dict):
        raise SerializationError("The item document must be an object.")
    version = document.get("schema_version")
    if version != SCHEMA_VERSION:
        raise SerializationError(
            f"Unsupported item schema version {version!r}; this app reads version {SCHEMA_VERSION}."
        )
    try:
        item = EquipmentItem.from_dict(document["item"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SerializationError(f"The item document is incomplete: {exc}") from exc
    return item
