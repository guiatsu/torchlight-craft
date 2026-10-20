"""Small QML composition facade for the editor, browser and library view-models."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, QStandardPaths, Signal, Slot

from app.viewmodels.affix_browser import AffixBrowserViewModel
from app.viewmodels.crafting import CraftingViewModel
from app.viewmodels.item_editor import ItemEditorViewModel
from app.viewmodels.library import ItemLibraryViewModel
from core.catalog import Catalog, load_catalog
from core.models import new_equipment
from core.version import APP_VERSION
from services.affix_browser import AffixBrowser
from services.crafting_service import CraftingService
from services.item_editor_service import ItemEditorService
from services.item_library_service import ItemLibraryService
from services.item_repository import ItemRepository


class AppController(QObject):
    """Compose Qt adapters and expose only shared app-level state to QML."""

    noticeChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.catalog: Catalog = load_catalog()
        initial_item = new_equipment()
        initial_base = self.catalog.bases.get(initial_item.base_id)
        if initial_base:
            initial_item.name = initial_base.name

        self.editor_service = ItemEditorService(self.catalog, initial_item)
        self.browser_service = AffixBrowser(self.catalog)
        self.crafting_service = CraftingService(self.catalog)
        self.library_service = ItemLibraryService(
            ItemRepository(
                Path(
                    QStandardPaths.writableLocation(
                        QStandardPaths.StandardLocation.AppDataLocation
                    )
                )
                / "items.json"
            )
        )
        self._editor = ItemEditorViewModel(self.editor_service, self)
        self._affix_browser = AffixBrowserViewModel(
            self.browser_service, self.editor_service, self
        )
        self._crafting = CraftingViewModel(
            self.crafting_service, self.editor_service, self._affix_browser, self
        )
        self._library = ItemLibraryViewModel(
            self.library_service, self._editor, self._affix_browser, self
        )
        self._editor.baseChanged.connect(self._affix_browser.item_replaced)
        self._editor.itemLevelChanged.connect(self._affix_browser.item_level_changed)
        self._editor.affixesChanged.connect(self._affix_browser.selectionChanged.emit)
        self._affix_browser.itemChanged.connect(self._notify_item_mutated)
        self._editor.equipmentChanged.connect(self._crafting.invalidateHistory)
        self._editor.equipmentChanged.connect(self._crafting.refreshPreview)
        self._affix_browser.selectionChanged.connect(self._crafting.refreshPreview)
        self._affix_browser.itemChanged.connect(self._crafting.invalidateHistory)
        self._crafting.itemChanged.connect(self._notify_item_mutated)
        for view_model in (self._editor, self._affix_browser, self._crafting, self._library):
            view_model.noticeRequested.connect(self._set_notice)
        self._notice_text = ""
        self._notice_kind = "info"

    @Property(QObject, constant=True)
    def editor(self) -> ItemEditorViewModel:
        return self._editor

    @Property(str, constant=True)
    def appVersion(self) -> str:
        return APP_VERSION

    @Property(QObject, constant=True)
    def affixBrowser(self) -> AffixBrowserViewModel:
        return self._affix_browser

    @Property(QObject, constant=True)
    def crafting(self) -> CraftingViewModel:
        return self._crafting

    @Property(QObject, constant=True)
    def library(self) -> ItemLibraryViewModel:
        return self._library

    @Property(str, notify=noticeChanged)
    def noticeText(self) -> str:
        return self._notice_text

    @Property(str, notify=noticeChanged)
    def noticeKind(self) -> str:
        return self._notice_kind

    @Slot(str, str)
    def _set_notice(self, message: str, kind: str = "info") -> None:
        self._notice_text = message
        self._notice_kind = kind
        self.noticeChanged.emit()

    def _notify_item_mutated(self) -> None:
        self._editor.affixesChanged.emit()
        self._editor.stateChanged.emit()

    @Slot()
    def dismissNotice(self) -> None:
        if self._notice_text:
            self._notice_text = ""
            self.noticeChanged.emit()
