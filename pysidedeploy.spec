[app]
title = Torchlight Craft Planner
project_dir = .
input_file = main.py
exec_directory = dist
project_file = pyproject.toml
icon = assets/icons/planner-mark.ico

[python]
python_path = .venv/Scripts/python.exe
packages = nuitka,ordered_set,zstandard

[qt]
qml_files = ui/Main.qml,ui/ItemEditor.qml,ui/components/AffixSelector.qml,ui/components/AffixRow.qml,ui/components/BaseSelector.qml,ui/components/TierBadge.qml
excluded_qml_plugins = QtCharts,QtQuick3D,QtSensors,QtTest,QtWebEngine

[nuitka]
mode = standalone
extra_args = --include-data-dir=ui=ui --include-data-dir=assets=assets --include-data-dir=data=data --include-package-data=data --windows-console-mode=disable --windows-icon-from-ico=assets/icons/planner-mark.ico
