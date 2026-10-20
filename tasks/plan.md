# Implementation Plan: Torchlight Craft Planner v0.2.1

## Overview

Repair TLIDB affix family grouping and give each imported tier a stable record identity. Keep older schema-v1 equipment readable, make large tier lists usable, simplify base selection without inferring a base from Item Level, then reimport and audit the complete cached catalog.

## Architecture Decisions

- Keep every source tier row. Build canonical affix families from the modifier record identity plus a normalized semantic description; retain TLIDB's raw family comment and the previous application family ID as provenance.
- Preserve an old family ID when it maps to one canonical family. When an old ID maps to several families, expose it only as a legacy alias and report ambiguous saved tier labels instead of selecting the first match.
- Keep `schema_version=1` equipment serialization. Store the stable source tier-record ID in its existing `tier_id` field and recognize old tier labels only when they resolve uniquely.
- Use Item Level to revalidate affix tiers and known `minimum_item_level` requirements. Do not compare it with `character_level_requirement`; where base Item Level data is absent, show candidate bases and ambiguity instead of claiming a match.
- Keep `pyproject.toml` as the single application-version source; pass that version from Python to QML.

## Task List

### Phase 1: Source integrity and identity
- [x] Inspect repository rules, current implementation, baseline tests, Claw database rows, and published TLIDB Claw table.
- [x] Correct family grouping and schema; add semantic, duplicate-tier, family-link, source-ID, and row-retention audits.
- [x] Use stable tier-record IDs in domain selection and migrate old labels only when unambiguous.
- [x] Reimport all cached pages to a temporary database, compare counts, validate, then replace the bundled catalog and refresh reports.

### Checkpoint: Catalog integrity
- [x] All source tier rows are retained and linked to one family.
- [x] Claw Multistrike and Attack Critical Strike Rating are separate, internally coherent families with exact levels and weights.
- [x] Existing equipment JSON schema v1 loads; ambiguous legacy labels are visibly unresolved.

### Phase 2: Catalog selection UX
- [x] Replace the unlimited tier row with a compact, independently scrollable tier list and technical tooltips.
- [x] Simplify base selection, keep manual selection available, default to standard-craftable bases, and surface special/unknown bases separately.
- [x] Add explicit base suggestions that respect verified minimum Item Level data, display ambiguity, and never change a base on Item Level edits or library loads.
- [x] Revalidate selected tiers on Item Level changes and show incompatibility warnings without deleting affixes.
- [x] Read the application version from `pyproject.toml` and pass it to the header.

### Phase 3: Regression and delivery
- [x] Add parser, catalog, service, UI-model, persistence, and QML regression coverage, including Claw reference rows.
- [x] Update catalog documentation and audit reports with before/after family counts and retained tier counts.
- [x] Run the full test suite and offscreen QML smoke test; verify the Windows workflow stages `pyproject.toml` and retains its packaged smoke test.
- [ ] Build and smoke-test the Windows standalone bundle locally. WSL interop returned `UtilBindVsockAnyPort:317: socket failed 1` for both `cmd.exe` and PowerShell, so Windows execution is unavailable in this session.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| TLIDB's comment ID groups several different modifier families | Wrong descriptions, levels, or weights shown together | Preserve the raw ID as provenance, split by source modifier identity and semantic signature, and validate against the published table |
| Old equipment stores only a tier label | A label may map to multiple corrected tier records | Keep the JSON contract and report ambiguity; never choose the first matching tier |
| Source catalog has no verified minimum Item Level for bases | A single correct base cannot be inferred | Show candidates and explicit ambiguity; do not use character-level requirement as Item Level |
| Catalog replacement is interrupted or invalid | The bundled app could lose its catalog | Import to a temporary file, validate counts and foreign keys, keep the old database until the new database passes |

## Open Questions

- None blocking. The current snapshot has no populated base `minimum_item_level` values, so the UI must state that candidate matches are unverified when it cannot rank by that field.
