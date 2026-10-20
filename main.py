"""Application entry point."""

from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QTimer, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from app.controller import AppController
from core.version import APP_VERSION


DIAGNOSTIC_LOG = Path(tempfile.gettempdir()) / "TorchlightCraftPlanner-startup.log"


def _write_diagnostics(messages: list[str]) -> None:
    if not messages:
        messages = ["The application failed during startup without additional diagnostics."]
    DIAGNOSTIC_LOG.write_text("\n".join(messages) + "\n", encoding="utf-8")


def main() -> int:
    diagnostics: list[str] = []
    try:
        DIAGNOSTIC_LOG.unlink(missing_ok=True)
    except OSError:
        pass

    def qt_message_handler(message_type, context, message) -> None:
        where = f" ({context.file}:{context.line})" if context and context.file else ""
        diagnostics.append(f"Qt message{where}: {message}")

    old_excepthook = sys.excepthook

    def exception_hook(error_type, error, error_traceback) -> None:
        diagnostics.append("Unhandled Python exception:\n" + "".join(
            traceback.format_exception(error_type, error, error_traceback)
        ))
        _write_diagnostics(diagnostics)
        old_excepthook(error_type, error, error_traceback)

    sys.excepthook = exception_hook
    qInstallMessageHandler(qt_message_handler)
    try:
        return _run_application(diagnostics)
    except Exception:
        diagnostics.append("Unhandled startup exception:\n" + traceback.format_exc())
        _write_diagnostics(diagnostics)
        return 1
    finally:
        qInstallMessageHandler(None)
        sys.excepthook = old_excepthook


def _run_application(diagnostics: list[str]) -> int:
    QQuickStyle.setStyle("Basic")
    QCoreApplication.setOrganizationName("Torchlight Craft Planner")
    QCoreApplication.setOrganizationDomain("local.torchlight-craft-planner")
    QCoreApplication.setApplicationName("Torchlight Craft Planner")
    QCoreApplication.setApplicationVersion(APP_VERSION)

    app = QGuiApplication(sys.argv)
    root_dir = Path(__file__).resolve().parent
    app.setWindowIcon(QIcon(str(root_dir / "assets" / "icons" / "planner-mark.svg")))

    engine = QQmlApplicationEngine()
    qml_warnings: list[str] = []
    engine.warnings.connect(lambda errors: qml_warnings.extend(str(error) for error in errors))
    controller = AppController()
    engine.rootContext().setContextProperty("controller", controller)
    engine.load(QUrl.fromLocalFile(str(root_dir / "ui" / "Main.qml")))
    if not engine.rootObjects():
        diagnostics.append("QQmlApplicationEngine did not create any root object.")
        diagnostics.extend(qml_warnings)
        _write_diagnostics(diagnostics)
        return 1
    smoke_test = "--smoke-test" in sys.argv[1:]
    if smoke_test:
        QTimer.singleShot(1500, app.quit)
    exit_code = app.exec()
    if smoke_test and qml_warnings:
        diagnostics.append("QML startup warnings during smoke test:")
        diagnostics.extend(qml_warnings)
        _write_diagnostics(diagnostics)
        for warning in qml_warnings:
            print(warning, file=sys.stderr)
        return 1
    if exit_code != 0:
        diagnostics.append(f"Qt application event loop exited with code {exit_code}.")
        _write_diagnostics(diagnostics)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
