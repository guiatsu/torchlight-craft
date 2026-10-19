import json

import pytest

from core.models import EquipmentItem
from services.item_repository import ItemRepository, RepositoryError


def test_save_load_duplicate_rename_and_delete(tmp_path):
    repository = ItemRepository(tmp_path / "items.json")
    item = EquipmentItem(name="First cane")
    repository.save_item(item)
    loaded = repository.load_all()
    assert len(loaded) == 1
    assert loaded[0].name == "First cane"

    loaded[0].name = "Renamed cane"
    repository.save_item(loaded[0])
    assert (tmp_path / "items.json.bak").exists()
    assert repository.load_all()[0].name == "Renamed cane"

    repository.delete_item(item.id)
    assert repository.load_all() == []


def test_repository_version_is_present(tmp_path):
    repository = ItemRepository(tmp_path / "items.json")
    repository.save_item(EquipmentItem())
    document = json.loads((tmp_path / "items.json").read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert len(document["items"]) == 1


def test_corrupt_file_is_preserved_and_never_overwritten(tmp_path):
    path = tmp_path / "items.json"
    original = "{ this is recoverable"
    path.write_text(original, encoding="utf-8")
    repository = ItemRepository(path)

    with pytest.raises(RepositoryError, match="original file is preserved"):
        repository.load_all()
    with pytest.raises(RepositoryError):
        repository.save_item(EquipmentItem())
    assert path.read_text(encoding="utf-8") == original


def test_incompatible_schema_is_preserved(tmp_path):
    path = tmp_path / "items.json"
    document = {"schema_version": 77, "items": []}
    path.write_text(json.dumps(document), encoding="utf-8")
    repository = ItemRepository(path)
    with pytest.raises(RepositoryError):
        repository.load_all()
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 77
