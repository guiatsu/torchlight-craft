# Torchlight Craft Planner

Version 0.3.0 is an offline desktop equipment editor and experimental standard-crafting planner for Torchlight: Infinite. It keeps the v0.1 editing and library flows, bundles a normalized TLIDB catalog, and can simulate one opt-in weighted craft attempt in the open session.

## Features

- Browse equipment by category and subcategory, search by name, and select from a virtualized result list.
- See the listed character requirement, base properties, crafting classification, and source status.
- Add, edit, replace, and remove compatible standard-craft affixes in separate prefix and suffix groups.
- Filter Basic, Advanced, and Ultimate affixes; see all published tiers, requirements, exact source weights, and source links.
- See each imported tier with a stable record ID, separate from its T0/T1 display label; ambiguous v0.2 tier labels are called out.
- Get a base suggestion only when the catalog contains a verified minimum Item Level; category filters never replace the selected base.
- Keep special or unknown equipment in the catalog and label systems the current editor does not support.
- Switch between Edit and Craft modes while sharing the same equipment session.
- Preview an exact standard-craft pool and inspect family and tier probabilities under **Experimental — TLIDB Weighted**. The model is opt-in and does not claim official game odds.
- Make one random attempt in the selected slot, repeat on that slot, inspect the result and undo session crafts. The displayed tier range is preserved; a numeric value inside that range is not rolled.
- Save, open, duplicate, rename, and delete equipment in the existing `schema_version=1` JSON library.

Crafting rule classifications, source links, and known limitations are documented in [`docs/crafting-rules.md`](docs/crafting-rules.md).

## Catalog snapshot

The 2026-10-19 import discovered and processed all **49** category pages in TLIDB's Gear card. It reconciled all 48 control categories and included one additional live category, Ethereal Prism. The category cards and item pages yielded **2,194 equipment records**, **2,233 semantic affix families**, **13,303 tier rows**, and **831 non-affix source rows**. All **16,328** discovered records were retained in SQLite; no category page or table failed parsing. The import preserved **3,516 explicit zero weights**, and found no missing or unparsed tier weights.

The family count increased from 642 in v0.2.0 because its grouping key treated a broad TLIDB table comment as a complete affix family. The v0.2.1 importer also groups by modifier family and normalized property description, splitting **382** legacy family keys that contained multiple properties. Every old family key remains available as a hidden compatibility alias, and all 13,303 source tier rows are retained.

The audit is **partial**, not complete: 637 records are classified `standard_craftable`, 338 `special_craftable`, 0 `non_craftable`, and 1,219 remain `unknown`. Fifty base fields are still absent from the source pages after inspecting 37 distinct item detail pages; seven records gained confirmed fields from those pages. Ten self-named Vorax entries use their already-fetched category page as the item URL, so there is no separate detail page for those entries. The unresolved report distinguishes those cases from detail pages that were inspected but lacked the field. Unknown Legendary classifications are preserved without guessing. Ethereal Prism's 393 tabular records are retained as raw source rows rather than treated as conventional craft affixes.

The current snapshot has no verified `minimum_item_level` values on equipment bases. The suggestion control therefore explains that it cannot rank bases in this snapshot. It never compares equipment Item Level with a base's character level requirement.

The percentage in `reports/tlidb-coverage.json` measures record retention against the records discovered in fetched pages. It does not confirm gameplay rules or season accuracy. TLIDB is a community reference; records remain `community_reference_season_unverified` for SS14 — Tartarus.

Reports are checked in under `reports/`:

- `tlidb-discovery.json` — live categories and comparison with the 48-category control list.
- `tlidb-coverage.json` — counts, classification and per-category status.
- `tlidb-import-errors.json` — parsing, fetch, and source-count errors.
- `tlidb-unresolved.json` — unknown classifications and source fields that remain absent.
- `tlidb-import-summary.md` — human-readable snapshot.
- `tlidb-validation.json` — SQLite schema, foreign-key, and integrity checks.
- `tlidb-v021-migration.md` — v0.2.0/v0.2.1 count comparison and Claw regression audit.

The runtime catalog is `data/catalog.sqlite3` (catalog schema v3). Legacy JSON records and split v0.2 family IDs remain available as hidden aliases so saved equipment references still resolve. User items remain in their separate `schema_version=1` JSON library. The app never fetches TLIDB at startup and works offline. The UI version and Windows build both read the single version in `pyproject.toml`.

## Update and validate the catalog

The development importer uses Python's standard library, a checksum-verified cache, `robots.txt`, serial requests (one per second by default), and bounded retries. The cache lives in the ignored `.cache/tlidb/` directory.

```bash
.venv/bin/python tools/tlidb/import_catalog.py discover
.venv/bin/python tools/tlidb/import_catalog.py import
.venv/bin/python tools/tlidb/import_catalog.py import --offline
.venv/bin/python tools/tlidb/import_catalog.py validate
.venv/bin/python tools/tlidb/import_catalog.py diff old.sqlite3 new.sqlite3
```

`import` uses cached pages when available and fetches missing pages. `--refresh` refetches source pages. Import returns a nonzero status when coverage remains partial; the generated database and reports are still available for inspection. A category-only pilot cannot overwrite the bundled full catalog.

## Architecture

The Qt/QML facade in `app/controller.py` composes focused view-models for the editor, affix browser, crafting panel, and library. Python-only services own equipment edits, affix browsing, bounded craft-pool caching, probabilistic crafting, and library operations. The pure engine in `core/crafting.py` uses immutable action/outcome/result records and keeps the user's active equipment as the single session state. Models live under `core/models/`; `from core.models import ...` remains supported. The equipment service keeps the craft undo snapshots separate from the save baseline.

`core/catalog.py` reads the bundled SQLite catalog and adds hidden compatibility aliases from the original JSON files. `tools/tlidb/` is a development-only importer and audit tool; it is not imported during application startup.

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

The local equipment library is stored in Qt's application data location as `items.json`. Saving keeps the previous version as `items.json.bak`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

or:

```bash
.venv/bin/python -m pytest
QT_QPA_PLATFORM=offscreen .venv/bin/python main.py --smoke-test-craft
```

The craft smoke test also loads Craft Mode, makes one eligible test attempt, and undoes it in the temporary process.

## Windows standalone build

The [Windows standalone workflow](.github/workflows/windows-build.yml) runs on pushes to `main` and can also be started manually from GitHub Actions. It stages the runtime Python packages, UI, assets, JSON compatibility data, and SQLite catalog before compiling on a Windows x64 runner. It checks the GUI executable's actual process exit code and uploads `TorchlightCraftPlanner-Windows-x64.zip` only after the packaged QML smoke test passes.

To build locally on Windows x64 with the same Python environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\pyside6-deploy.exe --dry-run
.\.venv\Scripts\pyside6-deploy.exe --mode standalone
```

## Known limits

- Gameplay and SS14 accuracy are not verified by this community-source import.
- The 1,219 `unknown` classifications remain visible and are not offered as standard-craft affixes. No items are called non-craftable without explicit evidence.
- Only standard crafting is simulated. Graft, Corrosion, Gear Empowerment, cost consumption, in-game failure chances, and automatic crafting are not implemented.
- TLIDB weights are not verified game odds. The single flat weighted-row model is explicitly experimental, off by default, and described in `docs/crafting-rules.md`.
- Numerical value rolls within a tier's displayed range are not simulated. The result stores the catalog range and says so.
- Craft undo is session-only. Manual equipment edits and replacing the open item clear its history; no craft history is written into equipment JSON.
- Fifty base fields remain absent from the linked category/detail pages: 41 character requirements and 9 property sets. See the unresolved report for each record and link.
- The three-prefix/three-suffix display for Sleeping Sage's Cane is screenshot-derived and remains provisional; other slot limits are unknown unless listed.
- The offscreen QML smoke test checks startup and QML loading; it does not replace visual review in a Windows desktop session.
