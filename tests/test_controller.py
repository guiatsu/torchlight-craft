from dataclasses import asdict

from core.controller import AppController


def test_rename_open_saved_item_preserves_other_unsaved_edits(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()
    assert controller.library.saveCurrent()
    saved_id = controller.library.savedItems[0]["id"]

    controller.editor.setPriceless(True)
    assert controller.editor.isDirty

    controller.library.renameSavedItem(saved_id, "Renamed cane")

    assert controller.editor.itemName == "Renamed cane"
    assert controller.editor.isDirty
    assert controller.library.saveCurrent()

    saved = controller.library_service.load_all()[0]
    assert saved.id == saved_id
    assert saved.name == "Renamed cane"
    assert saved.priceless is True


def test_controller_does_not_add_the_same_affix_twice(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()
    definition_id = "cane-physical-damage-prefix"

    controller.affixBrowser.selectDefinition(definition_id)
    controller.affixBrowser.addOrUpdateAffix()
    controller.affixBrowser.beginAddAffix("prefix")
    controller.affixBrowser.selectDefinition(definition_id)
    controller.affixBrowser.addOrUpdateAffix()

    assert len(controller.editor.prefixAffixes) == 1
    assert "already on this equipment" in controller.noticeText


def test_discarding_unsaved_changes_completes_the_close_request(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()
    close_events = []
    controller.library.closeConfirmed.connect(lambda: close_events.append(True))
    controller.editor.setPriceless(True)

    controller.library.requestClose()
    controller.library.resolveUnsaved("discard")

    assert close_events == [True]


def test_updating_one_selected_instance_leaves_other_affixes_unchanged(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()

    controller.affixBrowser.selectDefinition("cane-fire-damage-prefix")
    controller.affixBrowser.addOrUpdateAffix()
    controller.affixBrowser.beginAddAffix("suffix")
    controller.affixBrowser.selectDefinition("cane-attack-speed-suffix")
    controller.affixBrowser.addOrUpdateAffix()
    untouched = asdict(controller.editor_service.item.affixes[1])
    edited_id = controller.editor_service.item.affixes[0].id

    controller.affixBrowser.selectAffixInstance(edited_id)
    controller.affixBrowser.selectDefinition("cane-critical-damage-suffix")
    controller.affixBrowser.setAffixValue("custom critical value")
    controller.affixBrowser.addOrUpdateAffix()

    assert controller.editor_service.item.affixes[0].id == edited_id
    assert controller.editor_service.item.affixes[0].definition_id == "cane-critical-damage-suffix"
    assert asdict(controller.editor_service.item.affixes[1]) == untouched


def test_base_change_preserves_incompatible_affix_and_blocks_save(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()
    controller.affixBrowser.selectDefinition("cane-fire-damage-prefix")
    controller.affixBrowser.addOrUpdateAffix()
    original = asdict(controller.editor_service.item.affixes[0])

    controller.editor.setBase("ring")

    assert len(controller.editor_service.item.affixes) == 1
    assert asdict(controller.editor_service.item.affixes[0]) == original
    assert not controller.library.saveCurrent()


def test_library_open_duplicate_rename_and_delete_flows(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    controller = AppController()
    assert controller.library.saveCurrent()
    saved_id = controller.library.savedItems[0]["id"]

    controller.library.requestOpenItem(saved_id)
    assert controller.editor_service.item.id == saved_id
    assert not controller.editor.isDirty

    controller.library.requestDuplicateItem(saved_id)
    assert controller.editor_service.item.id != saved_id
    assert controller.editor.itemName.endswith(" Copy")
    assert controller.editor.isDirty
    assert controller.library.saveCurrent()

    duplicate_id = controller.editor_service.item.id
    controller.library.renameSavedItem(duplicate_id, "Renamed copy")
    assert controller.editor.itemName == "Renamed copy"
    controller.library.deleteSavedItem(duplicate_id)

    assert all(item["id"] != duplicate_id for item in controller.library.savedItems)
    assert controller.editor.isDirty
