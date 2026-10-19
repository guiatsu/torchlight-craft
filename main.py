"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from core.controller import AppController


def main() -> int:
    QQuickStyle.setStyle("Basic")
    QCoreApplication.setOrganizationName("Torchlight Craft Planner")
    QCoreApplication.setOrganizationDomain("local.torchlight-craft-planner")
    QCoreApplication.setApplicationName("Torchlight Craft Planner")
    QCoreApplication.setApplicationVersion("0.1.0")

    app = QGuiApplication(sys.argv)
    root_dir = Path(__file__).resolve().parent
    app.setWindowIcon(QIcon(str(root_dir / "assets" / "icons" / "planner-mark.svg")))

    engine = QQmlApplicationEngine()
    qml_warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: qml_warnings.extend(str(error) for error in errors)
    )
    controller = AppController()
    engine.rootContext().setContextProperty("controller", controller)
    engine.load(QUrl.fromLocalFile(str(root_dir / "ui" / "Main.qml")))
    if not engine.rootObjects():
        return 1
    smoke_test = "--smoke-test" in sys.argv[1:]
    if smoke_test:
        QTimer.singleShot(1500, app.quit)
    exit_code = app.exec()
    if smoke_test and qml_warnings:
        for warning in qml_warnings:
            print(warning, file=sys.stderr)
        return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
