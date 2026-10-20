from __future__ import annotations

from copy import deepcopy

from app.controller import AppController


def _controller(tmp_path, monkeypatch) -> AppController:
    monkeypatch.setattr(
        "app.controller.QStandardPaths.writableLocation",
        lambda _location: str(tmp_path),
    )
    return AppController()


def _enable_craft(controller: AppController) -> None:
    controller.affixBrowser.beginAddAffixAtSlot("prefix", 0)
    controller.crafting.setExperimentalEnabled(True)


def test_one_craft_and_repeat_replace_same_slot_then_undo_back_to_save_baseline(
    tmp_path, monkeypatch
) -> None:
    controller = _controller(tmp_path, monkeypatch)
    before = deepcopy(controller.editor_service.item.to_dict())
    _enable_craft(controller)

    controller.crafting.craftOnce()
    first = controller.editor_service.item.affixes[0]
    assert len(controller.editor_service.item.affixes) == 1
    assert controller.crafting.historyCount == 1
    assert controller.editor.isDirty

    controller.crafting.craftOnce()
    second = controller.editor_service.item.affixes[0]
    assert len(controller.editor_service.item.affixes) == 1
    assert second.id == first.id
    assert controller.crafting.historyCount == 2

    controller.crafting.undoLast()
    assert controller.editor_service.item.affixes[0].id == first.id
    assert controller.crafting.historyCount == 1
    controller.crafting.undoLast()
    assert controller.editor_service.item.to_dict() == before
    assert controller.crafting.historyCount == 0
    assert not controller.editor.isDirty


def test_manual_edit_invalidates_undo_without_reverting_the_craft(tmp_path, monkeypatch) -> None:
    controller = _controller(tmp_path, monkeypatch)
    _enable_craft(controller)
    controller.crafting.craftOnce()
    assert controller.crafting.historyCount == 1
    crafted = deepcopy(controller.editor_service.item.to_dict())

    controller.editor.setPriceless(True)

    assert controller.crafting.historyCount == 0
    assert len(controller.editor_service.item.affixes) == 1
    assert controller.editor_service.item.to_dict() != crafted
    assert controller.editor_service.item.priceless


def test_discarding_to_new_item_invalidates_history_and_replaces_session(tmp_path, monkeypatch) -> None:
    controller = _controller(tmp_path, monkeypatch)
    _enable_craft(controller)
    controller.crafting.craftOnce()
    old_item_id = controller.editor_service.item.id
    assert controller.crafting.historyCount == 1

    controller.library.requestNewItem()
    controller.library.resolveUnsaved("discard")

    assert controller.editor_service.item.id != old_item_id
    assert controller.editor_service.item.affixes == []
    assert controller.crafting.historyCount == 0


def test_preview_updates_with_category_and_selected_slot_and_never_calls_family_a_target(
    tmp_path, monkeypatch
) -> None:
    controller = _controller(tmp_path, monkeypatch)
    _enable_craft(controller)
    basic_pool = controller.crafting.poolId
    basic_families = {row["familyId"] for row in controller.crafting.candidates}
    assert controller.crafting.poolAvailable
    assert controller.crafting.selectedCategory == "Basic"

    controller.crafting.setCategory("Advanced")
    assert controller.crafting.poolAvailable
    assert controller.crafting.poolId == basic_pool
    advanced_families = {row["familyId"] for row in controller.crafting.candidates}
    assert advanced_families != basic_families
    assert controller.crafting.selectedCategory == "Advanced"
    assert "random outcome" not in controller.crafting.operationLabel.lower()


def test_item_level_change_rebuilds_the_pool_and_tier_probabilities(tmp_path, monkeypatch) -> None:
    controller = _controller(tmp_path, monkeypatch)
    _enable_craft(controller)
    high_level_rows = sum(len(row["tiers"]) for row in controller.crafting.candidates)
    high_level_weight = controller.crafting.totalWeight

    controller.editor.setItemLevel(50)

    low_level_rows = sum(len(row["tiers"]) for row in controller.crafting.candidates)
    assert controller.crafting.itemLevel == 50
    assert low_level_rows < high_level_rows
    assert controller.crafting.totalWeight < high_level_weight


def test_opt_in_is_required_and_unknown_limit_add_is_blocked(tmp_path, monkeypatch) -> None:
    controller = _controller(tmp_path, monkeypatch)
    controller.affixBrowser.beginAddAffixAtSlot("prefix", 0)
    assert not controller.crafting.experimentalEnabled
    assert not controller.crafting.canCraft
    assert "Enable" in controller.crafting.poolMessage

    ring = next(
        base for base in controller.catalog.bases.values()
        if base.name == "Burning Flame Ring"
    )
    controller.editor_service.replace_item(
        type(controller.editor_service.item)(
            id="ring-session",
            name=ring.name,
            base_id=ring.id,
            item_level=86,
        )
    )
    controller.editor.item_replaced()
    controller.affixBrowser.item_replaced()
    controller.affixBrowser.beginAddAffixAtSlot("prefix", 0)
    controller.crafting.setExperimentalEnabled(True)
    assert not controller.crafting.poolAvailable
    assert "no verified empty slot limit" in controller.crafting.poolMessage
