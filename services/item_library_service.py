"""Use cases for saved equipment, separate from editor-session state."""

from __future__ import annotations

from uuid import uuid4

from core.models import EquipmentItem
from services.item_repository import ItemRepository


class ItemLibraryService:
    def __init__(self, repository: ItemRepository) -> None:
        self.repository = repository

    def load_all(self) -> list[EquipmentItem]:
        return self.repository.load_all()

    def save(self, item: EquipmentItem) -> list[EquipmentItem]:
        return self.repository.save_item(item)

    def duplicate(self, item: EquipmentItem) -> EquipmentItem:
        duplicate = EquipmentItem.from_dict(item.to_dict())
        duplicate.id = f"item-{uuid4().hex}"
        duplicate.name = f"{item.name} Copy"
        return duplicate

    def rename(self, item: EquipmentItem, name: str) -> list[EquipmentItem]:
        item.name = name
        return self.repository.save_item(item)

    def delete(self, item_id: str) -> list[EquipmentItem]:
        return self.repository.delete_item(item_id)
