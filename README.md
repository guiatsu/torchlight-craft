# Torchlight Craft Planner

Version 0.1 is an offline desktop item editor for Torchlight: Infinite. The UI follows the supplied crafting-screen reference while using original vector artwork. It does not perform crafts or calculate costs or probabilities.

## Features

- Pick a local equipment base, set Item Level, and toggle Priceless independently from rarity.
- Add, edit, replace, and remove catalog affixes in separate prefix and suffix groups.
- Search the local affix catalog and filter Basic, Advanced, and Ultimate entries.
- Save, open, duplicate, rename, and delete equipment in a versioned JSON library.
- Keep an atomic backup of the previous library file when saving.
- Keep uncertain catalog compatibility and slot limits visible in the interface.

## Catalog and verification

The initial catalog is intentionally small: two Cane entries and one generic Ring slot, with a handful of affixes. Its Cane and Ring records were transcribed from [TLIDB Cane](https://tlidb.com/en/Cane) and [TLIDB Ring](https://tlidb.com/en/Ring), consulted on 2026-10-19. TLIDB describes itself as a fan-made site based on beta testing data. These entries are community references and are **not verified for SS14 — Tartarus**. The three-prefix/three-suffix capacity shown for Sleeping Sage's Cane follows the supplied screenshot only and remains provisional. See `data/sources.json` for provenance.

The app filters entries by the selected base and validates tier/item-level requirements found in the local catalog. It does not infer conflicts or unknown slot rules. A value field is a free-form display value, not a roll simulator.

## Run from source

Python 3.12+ is recommended. On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe main.py
```

On Linux or WSL:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python main.py
```

The local equipment library is stored in Qt's application data location as `items.json`. The previous version is kept as `items.json.bak` after a later save.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

or:

```bash
.venv/bin/python -m pytest
```

## Windows standalone build

The [Windows standalone workflow](.github/workflows/windows-build.yml) runs on pushes to `main` and can also be started manually from GitHub Actions. It builds on a Windows x64 runner, checks for the executable, and uploads `TorchlightCraftPlanner-Windows-x64.zip` as a workflow artifact. Download it from the completed run's **Artifacts** section. The artifact contains a standalone folder, not a onefile executable.

PySide6's deployment configuration is in `pysidedeploy.spec` and the `[tool.pyside6.deploy]` section of `pyproject.toml`; both include the QML files, original vector assets, and local JSON catalog.

To build locally on Windows x64 with the same Python environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\pyside6-deploy.exe --dry-run
.\.venv\Scripts\pyside6-deploy.exe --mode standalone
```

The official workflow and spec format are documented in [Qt for Python's pyside6-deploy guide](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html).

## Known limits

- The small catalog is community data pending season verification.
- The current three-per-side limit is a screenshot-derived example for Sleeping Sage's Cane only. Other base limits are unknown and not enforced.
- The generic Ring entry has no named base selected.
- No Windows build can be produced from the current Linux/WSL environment.
