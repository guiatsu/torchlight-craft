[app]
title = Torchlight Craft Planner
project_dir = .
input_file = main.py
exec_directory = dist
project_file = pyproject.toml
icon = assets/icons/planner-mark.ico

[python]
packages = nuitka,ordered_set,zstandard

[qt]
qml_files = ui/Main.qml,ui/ItemEditor.qml
excluded_qml_plugins = QtCharts,QtQuick3D,QtSensors,QtTest,QtWebEngine

[nuitka]
mode = standalone
extra_args = --windows-console-mode=disable --assume-yes-for-downloads --windows-icon-from-ico=assets/icons/planner-mark.ico --include-data-files=pyproject.toml=pyproject.toml
