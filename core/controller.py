"""Compatibility import for the QML facade, moved to :mod:`app.controller`."""

from PySide6.QtCore import QStandardPaths

from app.controller import AppController

__all__ = ["AppController", "QStandardPaths"]
