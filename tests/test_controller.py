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


def test_controller_does_not_add_the_same_affix_twice(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()
    definition_id = "cane-physical-damage-prefix"

    controller.selectDefinition(definition_id)
    controller.addOrUpdateAffix()
    controller.beginAddAffix("prefix")
    controller.selectDefinition(definition_id)
    controller.addOrUpdateAffix()

    assert len(controller.prefixAffixes) == 1
    assert "already on this equipment" in controller.noticeText


def test_discarding_unsaved_changes_completes_the_close_request(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()
    close_events = []
    controller.closeConfirmed.connect(lambda: close_events.append(True))
    controller.setPriceless(True)

    controller.requestClose()
    controller.resolveUnsaved("discard")

    assert close_events == [True]
