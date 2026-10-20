# Product

<!-- impeccable:product-schema 1 -->

## Platform

Windows desktop (native PySide6/Qt Quick; implemented in the current WSL environment).

## Stack

Python 3.12+, PySide6, Qt Quick/QML, dataclasses, a bundled SQLite game catalog, and a separate local JSON equipment library.

## Users

Torchlight: Infinite players who want to assemble and save equipment plans on a Windows desktop.

## Product Purpose

Torchlight Craft Planner is an offline equipment editor and experimental standard-crafting planner. Users can find a base, set its Item Level and Priceless state, edit affixes, inspect a weighted pool, make one craft attempt, undo session crafts, and save the equipment. Success means existing items remain compatible, each craft uses a valid traceable pool, and the chosen probability model is clearly labeled.

## Positioning

The product provides a persistent equipment workspace backed by a broad, auditable local reference catalog, with a separate opt-in experimental model for one craft attempt at a time. Official odds, material costs, numeric value rolls, and strategy simulation remain outside this release.

## Operating Context

The app is designed for a desktop Windows workflow and should remain usable offline after installation. The initial reference season is SS14 — Tartarus; community data is not assumed to be verified for that season.

## Capabilities and Constraints

- v0.3.0 includes the v0.2.1 editor and library workflows plus Edit/Craft mode switching, source-pool preview, exact experimental family/tier probabilities, one weighted craft attempt, result detail, and session-only undo.
- The user's equipment library remains `schema_version=1`; the normalized local catalog uses SQLite schema v3.
- The 2026-10-19 TLIDB snapshot contains 49 discovered categories, 2,194 base records, 2,233 semantic affix families, 13,303 tiers, 831 retained non-affix source rows, and 37 inspected item detail pages. The family count rose from 642 because 382 broad legacy source keys contained multiple semantic properties; legacy aliases preserve old equipment references. All 16,328 source records were retained, while overall classification coverage remains partial.
- Tier identity uses stable source record IDs, while T0/T1 labels remain presentation-only. Repeated legacy labels are resolved only when unique; ambiguous labels are surfaced for correction.
- Current classification counts: 637 standard craftable, 338 special craftable, 0 explicitly non-craftable, and 1,219 unknown. Fifty source fields remain absent after detail inspection.
- `tools/tlidb/` provides dynamic discovery, cached import, offline validation, reports, and snapshot diff. It never runs during app startup.
- Changing to a base that does not list an existing affix preserves that affix and blocks saving until it is replaced or explicitly removed.
- Affix catalog data stays separate from QML and includes source and verification status.
- The pure Python craft engine preserves source weights, stable tier IDs, exact pool identity, and semantic family signatures. It blocks unavailable rules rather than filling gaps with uniform odds.
- **Experimental — TLIDB Weighted** is disabled until the user opts in. Its flat weighted-row assumption is not an official probability model; TLIDB is a community source.
- Zero-weight tiers remain inspectable and are never drawn. Higher Item Level requirements are filtered. Family and category caps follow the documented evidence classifications in `docs/crafting-rules.md`.
- Crafting modifies the same open item as manual editing. Undo stores only in-memory snapshots and is cleared by a manual equipment edit or item replacement. Item JSON remains `schema_version=1`.
- Tier value ranges are displayed as catalog text; the engine does not invent a numeric roll or material cost.
- Unknown compatibility and slot rules must remain visibly unverified rather than being presented as game rules.
- Special or unknown bases remain in the browser, but unsupported systems do not appear as standard-craft options.
- No Graft, Corrosion, Gear Empowerment, OCR, game-process access, automatic catalog updates, or automatic/batch craft loop.
- The requested distribution target is a standalone Windows x64 package. CI builds from a clean runtime staging directory and smoke-tests the packaged GUI executable.
- The catalog is a community-source snapshot and is pending SS14 verification. The source inventory contains all 48 control categories plus Ethereal Prism, discovered as an additional live category. The audit remains partial because 1,219 records have unknown crafting classifications and 50 fields remain absent from source pages.

## Brand Commitments

The supplied Torchlight: Infinite crafting screenshot is the visual reference. Interface labels use English, matching the screenshot.

## Evidence on Hand

The user supplied a crafting-screen screenshot and detailed v0.1-v0.3 specifications. TLIDB is a community reference; no official SS14 confirmation of its imported item data or weights is claimed. The import reports and `docs/crafting-rules.md` record coverage and the specific rule status.

## Product Principles

- Keep the item editor and catalog usable without a network connection.
- Preserve each saved item and its history-safe JSON representation.
- Make selection and editing changes visible immediately.
- Expose data uncertainty where it affects a choice.
- Keep crafting one attempt at a time, session-only, and visibly experimental where the distribution is unverified.
- Keep imported game data, QML presentation, and user equipment storage separate.
