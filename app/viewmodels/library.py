"""QML-facing library actions and unsaved-change flow."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from core.models import EquipmentItem, new_equipment
from core.validation import validate_item
from services.item_library_service import ItemLibraryService
from services.item_repository import ItemRepository, RepositoryError
from app.viewmodels.affix_browser import AffixBrowserViewModel
from app.viewmodels.item_editor import ItemEditorViewModel


class ItemLibraryViewModel(QObject):
    savedItemsChanged = Signal()
    confirmUnsaved = Signal()
    closeConfirmed = Signal()
    noticeRequested = Signal(str, str)

    def __init__(
        self,
        library: ItemLibraryService,
        editor: ItemEditorViewModel,
        browser: AffixBrowserViewModel,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.library = library
        self.editor = editor
        self.browser = browser
        self._saved_items: list[EquipmentItem] = []
        self._pending_action: tuple[str, str | None] | None = None
        self._refresh_saved_items(silent=True)

    @Property("QVariantList", notify=savedItemsChanged)
    def savedItems(self) -> list[dict[str, object]]:
        return [self._saved_item_view(item) for item in self._saved_items]

    @Property(str, notify=savedItemsChanged)
    def savedCountText(self) -> str:
        count = len(self._saved_items)
        return f"{count} saved item" if count == 1 else f"{count} saved items"

    def _saved_item_view(self, item: EquipmentItem) -> dict[str, object]:
        base = self.editor.service.catalog.bases.get(item.base_id)
        return {
            "id": item.id,
            "name": item.name,
            "baseName": base.name if base else "Unknown base",
            "itemLevel": item.item_level,
            "priceless": item.priceless,
            "affixCount": len(item.affixes),
        }

    def _refresh_saved_items(self, silent: bool = False) -> None:
        try:
            self._saved_items = self.library.load_all()
        except RepositoryError as exc:
            self._saved_items = []
            if not silent:
                self.noticeRequested.emit(str(exc), "error")
        self.savedItemsChanged.emit()

    def _commit_current(self) -> bool:
        errors = self.editor.service.validation_errors()
        if errors:
            self.noticeRequested.emit(" ".join(errors), "error")
            return False
        try:
            self._saved_items = self.library.save(self.editor.service.item)
        except RepositoryError as exc:
            self.noticeRequested.emit(str(exc), "error")
            return False
        self.editor.service.mark_saved()
        self.savedItemsChanged.emit()
        self.editor.stateChanged.emit()
        self.noticeRequested.emit("Equipment saved locally.", "success")
        return True

    def _continue_pending_action(self) -> None:
        if self._pending_action is None:
            return
        action, identifier = self._pending_action
        self._pending_action = None
        if action == "new":
            self._start_new_item()
        elif action == "open" and identifier:
            item = next((saved for saved in self._saved_items if saved.id == identifier), None)
            if item is None:
                self._refresh_saved_items()
                self.noticeRequested.emit("That saved item could not be found.", "error")
                return
            self._load_item(item)
        elif action == "duplicate" and identifier:
            item = next((saved for saved in self._saved_items if saved.id == identifier), None)
            if item is None:
                self.noticeRequested.emit("That saved item could not be found.", "error")
                return
            self.editor.service.replace_item(self.library.duplicate(item), clean=False)
            self._notify_item_replaced()
            self.noticeRequested.emit("Duplicate created. Save it when ready.", "success")
        elif action == "close":
            self.closeConfirmed.emit()

    def _notify_item_replaced(self) -> None:
        self.editor.item_replaced()
        self.browser.item_replaced()

    def _load_item(self, item: EquipmentItem) -> None:
        self.editor.service.replace_item(EquipmentItem.from_dict(item.to_dict()))
        self._notify_item_replaced()
        issues = self.editor.service.validation_errors()
        if issues:
            self.noticeRequested.emit(f"Opened {item.name} with catalog issues: {' '.join(issues)}", "warning")
        else:
            self.noticeRequested.emit(f"Opened {item.name}.", "success")

    def _start_new_item(self) -> None:
        item = new_equipment()
        base = self.editor.service.catalog.bases.get(item.base_id)
        if base:
            item.name = base.name
        self.editor.service.replace_item(item)
        self._notify_item_replaced()
        self.noticeRequested.emit("New equipment ready.", "success")

    @Slot()
    def saveCurrent(self) -> bool:
        return self._commit_current()

    @Slot()
    def requestNewItem(self) -> None:
        if self.editor.service.is_dirty:
            self._pending_action = ("new", None)
            self.confirmUnsaved.emit()
            return
        self._start_new_item()

    @Slot(str)
    def requestOpenItem(self, item_id: str) -> None:
        if self.editor.service.is_dirty:
            self._pending_action = ("open", item_id)
            self.confirmUnsaved.emit()
            return
        self._open_by_id(item_id)

    def _open_by_id(self, item_id: str) -> None:
        item = next((saved for saved in self._saved_items if saved.id == item_id), None)
        if item is None:
            self._refresh_saved_items()
            self.noticeRequested.emit("That saved item could not be found.", "error")
            return
        self._load_item(item)

    @Slot(str)
    def requestDuplicateItem(self, item_id: str) -> None:
        if self.editor.service.is_dirty:
            self._pending_action = ("duplicate", item_id)
            self.confirmUnsaved.emit()
            return
        self._pending_action = ("duplicate", item_id)
        self._continue_pending_action()

    @Slot(str)
    def resolveUnsaved(self, choice: str) -> None:
        if choice not in {"cancel", "discard", "save"}:
            return
        if choice == "cancel":
            self._pending_action = None
            return
        if choice == "save" and not self._commit_current():
            self._pending_action = None
            return
        self._continue_pending_action()

    @Slot()
    def requestClose(self) -> None:
        if self.editor.service.is_dirty:
            self._pending_action = ("close", None)
            self.confirmUnsaved.emit()
        else:
            self.closeConfirmed.emit()

    @Slot(str, str)
    def renameSavedItem(self, item_id: str, name: str = "") -> None:
        item = next((saved for saved in self._saved_items if saved.id == item_id), None)
        if item is None:
            self.noticeRequested.emit("That saved item could not be found.", "error")
            return
        clean_name = name.strip()[:80]
        if not clean_name:
            self.noticeRequested.emit("Give this equipment a name.", "error")
            return
        item.name = clean_name
        try:
            self._saved_items = self.library.rename(item, clean_name)
        except RepositoryError as exc:
            self.noticeRequested.emit(str(exc), "error")
            self._refresh_saved_items(silent=True)
            return
        if self.editor.service.item.id == item.id:
            self.editor.service.set_name(clean_name)
            self.editor.service.rename_baseline(clean_name)
            self.editor.stateChanged.emit()
            self.editor.equipmentChanged.emit()
        self.savedItemsChanged.emit()
        self.noticeRequested.emit("Saved equipment renamed.", "success")

    @Slot(str)
    def deleteSavedItem(self, item_id: str) -> None:
        try:
            self._saved_items = self.library.delete(item_id)
        except RepositoryError as exc:
            self.noticeRequested.emit(str(exc), "error")
            self._refresh_saved_items(silent=True)
            return
        current_item = self.editor.service.item
        if current_item.id == item_id:
            self.editor.service.mark_deleted_from_library()
        self.savedItemsChanged.emit()
        if current_item.id == item_id:
            self.editor.stateChanged.emit()
            self.noticeRequested.emit(
                "Saved equipment deleted. The open copy remains in the editor as an unsaved item.",
                "warning",
            )
        else:
            self.noticeRequested.emit("Saved equipment deleted.", "success")

    @Slot()
    def refreshLibrary(self) -> None:
        self._refresh_saved_items()

