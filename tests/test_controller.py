from core.controller import AppController


def test_rename_open_saved_item_preserves_other_unsaved_edits(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()
    assert controller.saveCurrent()
    saved_id = controller.savedItems[0]["id"]

    controller.setPriceless(True)
    assert controller.isDirty

    controller.renameSavedItem(saved_id, "Renamed cane")

    assert controller.itemName == "Renamed cane"
    assert controller.isDirty
    assert controller.saveCurrent()

    saved = controller.repository.load_all()[0]
    assert saved.id == saved_id
    assert saved.name == "Renamed cane"
    assert saved.priceless is True
