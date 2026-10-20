# Product

<!-- impeccable:product-schema 1 -->

## Platform

Windows desktop (native PySide6/Qt Quick; implemented in the current WSL environment).

## Stack

Python 3.12+, PySide6, Qt Quick/QML, dataclasses, a bundled SQLite game catalog, and a separate local JSON equipment library.

## Users

Torchlight: Infinite players who want to assemble and save equipment plans on a Windows desktop.

## Product Purpose

Torchlight Craft Planner is an offline item editor for finding equipment bases, setting an item's level and Priceless state, editing standard-craft affixes, and saving equipment for later use. Success means the saved item can be reopened with its configuration intact and catalog data can be traced to its source.

## Positioning

The product provides a persistent equipment workspace backed by a broad, auditable local reference catalog. Crafting probabilities, costs, and strategy simulation are explicitly outside this release.

## Operating Context

The app is designed for a desktop Windows workflow and should remain usable offline after installation. The initial reference season is SS14 — Tartarus; community data is not assumed to be verified for that season.

## Capabilities and Constraints

- v0.2.1 includes category/subcategory filters and name search over the imported catalog, integer Item Level, verified-only base suggestions, standard-craft prefix/suffix selection and editing, catalog-listed slots, and JSON save/load/duplicate/rename/delete.
- The user's equipment library remains `schema_version=1`; the normalized local catalog uses SQLite schema v3.
- The 2026-10-19 TLIDB snapshot contains 49 discovered categories, 2,194 base records, 2,233 semantic affix families, 13,303 tiers, 831 retained non-affix source rows, and 37 inspected item detail pages. The family count rose from 642 because 382 broad legacy source keys contained multiple semantic properties; legacy aliases preserve old equipment references. All 16,328 source records were retained, while overall classification coverage remains partial.
- Tier identity uses stable source record IDs, while T0/T1 labels remain presentation-only. Repeated legacy labels are resolved only when unique; ambiguous labels are surfaced for correction.
- Current classification counts: 637 standard craftable, 338 special craftable, 0 explicitly non-craftable, and 1,219 unknown. Fifty source fields remain absent after detail inspection.
- `tools/tlidb/` provides dynamic discovery, cached import, offline validation, reports, and snapshot diff. It never runs during app startup.
- Changing to a base that does not list an existing affix preserves that affix and blocks saving until it is replaced or explicitly removed.
- Affix catalog data stays separate from QML and includes source and verification status.
- Unknown compatibility and slot rules must remain visibly unverified rather than being presented as game rules.
- Special or unknown bases remain in the browser, but unsupported systems do not appear as standard-craft options.
- No crafting simulation, probabilities, material costs, OCR, game-process access, or automatic catalog updates.
- The requested distribution target is a standalone Windows x64 package. CI builds from a clean runtime staging directory and smoke-tests the packaged GUI executable.
- The catalog is a community-source snapshot and is pending SS14 verification. The source inventory contains all 48 control categories plus Ethereal Prism, discovered as an additional live category. The audit remains partial because 1,219 records have unknown crafting classifications and 50 fields remain absent from source pages.

## Brand Commitments

The supplied Torchlight: Infinite crafting screenshot is the visual reference. Interface labels use English, matching the screenshot.

## Evidence on Hand

The user supplied a crafting-screen screenshot and detailed v0.1/v0.2 specifications. TLIDB is a fan-made community reference and labels its data as beta testing data; no official SS14 item-data confirmation is on hand. The import reports are the evidence source for coverage claims.

## Product Principles

- Keep the item editor and catalog usable without a network connection.
- Preserve each saved item and its history-safe JSON representation.
- Make selection and editing changes visible immediately.
- Expose data uncertainty where it affects a choice.
- Keep v0.2 focused on catalog coverage, editing, and persistence.
- Keep imported game data, QML presentation, and user equipment storage separate.
