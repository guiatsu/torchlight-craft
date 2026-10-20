# Implementation Plan: Torchlight Craft Planner v0.3

## Overview

Add a session-only probabilistic crafting mode beside the existing manual editor. The domain engine will consume the current catalog and one immutable item snapshot, build a single standard-craft pool, calculate exact integer-weight probabilities, make one reproducible weighted draw, and return before/after equipment states. The UI will require an explicit opt-in to the experimental TLIDB-weighted model. Saved equipment remains `schema_version=1`.

## Architecture Decisions

- Preserve the imported catalog and stable tier-record IDs. Expose each family's exact SQLite pool ID on `AffixDefinition`; do not combine pools by display name or T-label.
- Treat official, source-derived, experimental, and unknown rules as separate metadata. Only standard-craftable catalog bases can enter this first engine. Graft, Corrosion, Gear Empowerment, and unknown classifications remain unavailable.
- Implement one experimental model: a flat weighted draw across positive-weight eligible family-tier records. The official sources confirm random selection from a chosen pool but do not confirm how TLIDB weights map to the game's distribution. Never call the computed values official odds.
- Keep T0/T0+ source records and exact zero weights visible in pool details, but exclude zero weights from selection. Tiers above Item Level are excluded.
- Treat duplicate-family blocking as screenshot-derived, but label the replacement-target exception experimental because its live rule is unknown. Preserve the selected slot position and replace only that instance.
- Keep craft history in memory and store full before/after snapshots outside the item JSON schema. A normal manual edit or library item replacement invalidates craft undo history; consecutive craft attempts remain undoable one at a time.
- Keep the present editor panel and switch only the right-side workspace between Edit Mode and Craft Mode.

## Task List

### Phase 1: Evidence and catalog contracts
- [x] Record current-season rules and source links in `docs/crafting-rules.md` with explicit confidence statuses.
- [x] Expose exact pool and semantic signature metadata in the domain model and SQLite loader without changing legacy JSON serialization.
- [x] Add immutable craft action/outcome/pool/result types and rule metadata.
- [x] Confirm representative pool boundaries for Cane, Claw, Ring, and a two-handed base.

### Checkpoint: Catalog contract
- [x] Existing catalog and schema-v1 equipment tests pass.
- [x] Standard-craft pools remain separated by base category, Prefix/Suffix, and Basic/Advanced/Ultimate.
- [x] Claw Multistrike is one semantic family and remains separate from Critical Strike Rating.

### Phase 2: Eligibility, probabilities, and engine
- [x] Build a pool from an item snapshot and selected slot, excluding incompatible bases, tiers, categories, systems, duplicate families, and Advanced/Ultimate cap violations.
- [x] Fail closed when required pool weights are missing, malformed, negative, or total zero; retain exact zero-weight rows without sampling them.
- [x] Calculate family, joint-tier, and conditional-tier probabilities with integer arithmetic/Fractions.
- [x] Add an injected seeded weighted randomizer and pure engine for one add/replace attempt.
- [x] Return immutable before/after snapshots and a precise reason on invalid operations; invalid attempts never mutate input.

### Checkpoint: Domain engine
- [x] Deterministic tests cover weights, probability sums, pool boundaries, eligibility, replacement identity/position, and no-mutation failures.
- [x] Statistical test checks a small known distribution with a non-flaky tolerance.
- [x] Real-catalog reference cases cover Cane, Claw, Ring, two-handed, Priceless, and the Claw Multistrike regression.

### Phase 3: Session integration and QML
- [x] Add a crafting service and view-model that share the existing editor session.
- [x] Require explicit opt-in to the experimental model; show the reliability status and source-derived caveats.
- [x] Add mode switching, operation preview, pool list, family/tier probabilities, one-click craft, result detail, and repeat-on-same-slot behavior.
- [x] Keep manual editing separate and unchanged; protect craft actions with session snapshots and undo.
- [x] Invalidate undo history after non-craft equipment edits or item replacement.

### Checkpoint: User flow
- [x] Integration tests cover selected occupied and empty slots, category changes, preview refresh, one craft, repeated craft, undo, and manual-edit/library compatibility.
- [x] QML startup and basic craft-flow smoke tests pass without warnings.
- [ ] Inspect the desktop layout and disabled/unavailable states in a Windows desktop session.

### Phase 4: Release documentation and validation
- [x] Update `AGENTS.md`, `README.md`, `PRODUCT.md`, `pyproject.toml`, and package file lists for v0.3.
- [x] Run the complete pytest suite and QML craft-flow smoke test after the final changes.
- [x] Check Windows interop before attempting a local build. `cmd.exe /c ver` failed with a WSL socket error, so Windows build/executable validation is unavailable in this environment.
- [x] Review `git diff --check`, changed-file list, and backward compatibility.

### Checkpoint: Complete
- [x] All feasible acceptance criteria are implemented and verified with evidence.
- [x] Unknown mechanics and executable-build limits are stated plainly.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| TLIDB weights may not match the in-game distribution | Misleading odds | The weighted model is opt-in and explicitly experimental; the UI shows exact model semantics and source provenance. |
| Catalog snapshot and live SS14 data can differ | Unsupported or stale pool | Limit execution to catalog-standard craft bases and label source-season status; reject unknown classifications. |
| Some slot limits and family-exclusion rules are incomplete | Invalid outcomes | Require a catalog-listed slot; record duplicate-family exclusion as source-derived; do not infer unknown capacities. |
| The app has manual edits and unsaved-change flows | Craft history could erase intervening changes | Store deep before/after snapshots, clear history on external mutations, and preserve the editor's existing save baseline. |
| Large UI/data changes can regress old saves | Lost equipment references | Do not alter schema-v1 JSON and run existing persistence/regression tests before and after. |

## Open Questions

- Official documentation does not describe a verified family-then-tier vs. flat weight distribution. Only the explicit experimental flat model will be executable.
- Numerical rolls inside a tier's published range are not generated because the sources do not establish the within-range distribution.
- The local Windows executable cannot be declared validated unless Windows execution is available in this environment.
