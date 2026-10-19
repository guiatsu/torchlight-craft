"""Atomic JSON repository for saved equipment."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from core.models import EquipmentItem, SCHEMA_VERSION


class RepositoryError(RuntimeError):
    """Raised without modifying data when the repository cannot be trusted."""


class ItemRepository:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._blocked_error: str | None = None

    @property
    def backup_path(self) -> Path:
        return self.path.with_suffix(self.path.suffix + ".bak")

    def load_all(self) -> list[EquipmentItem]:
        if not self.path.exists():
            self._blocked_error = None
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or raw.get("schema_version") != SCHEMA_VERSION:
                raise RepositoryError("Saved data uses an unsupported schema. The original file is preserved.")
            rows = raw.get("items")
            if not isinstance(rows, list):
                raise RepositoryError("Saved data is missing its item list. The original file is preserved.")
            items = [EquipmentItem.from_dict(row) for row in rows]
            if len({item.id for item in items}) != len(items):
                raise RepositoryError("Saved data contains duplicate item IDs. The original file is preserved.")
        except RepositoryError as exc:
            self._blocked_error = str(exc)
            raise
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            self._blocked_error = f"Saved data could not be read: {exc}. The original file is preserved."
            raise RepositoryError(self._blocked_error) from exc
        self._blocked_error = None
        return items

    def save_item(self, item: EquipmentItem) -> list[EquipmentItem]:
        items = self.load_all()
        replaced = False
        for index, saved in enumerate(items):
            if saved.id == item.id:
                items[index] = item
                replaced = True
                break
        if not replaced:
            items.append(item)
        self._write(items)
        return items

    def delete_item(self, item_id: str) -> list[EquipmentItem]:
        items = self.load_all()
        remaining = [item for item in items if item.id != item_id]
        if len(remaining) == len(items):
            raise RepositoryError("That saved item no longer exists.")
        self._write(remaining)
        return remaining

    def _write(self, items: list[EquipmentItem]) -> None:
        if self._blocked_error:
            raise RepositoryError(self._blocked_error)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        document: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "items": [item.to_dict() for item in items],
        }
        if self.path.exists():
            try:
                shutil.copy2(self.path, self.backup_path)
            except OSError as exc:
                raise RepositoryError(f"Could not create a recovery copy: {exc}") from exc

        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.path.parent, delete=False, suffix=".tmp"
            ) as handle:
                temp_name = handle.name
                json.dump(document, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
            temp_name = None
        except OSError as exc:
            raise RepositoryError(f"Could not save equipment: {exc}") from exc
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)
