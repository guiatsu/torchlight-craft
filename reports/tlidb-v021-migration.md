# v0.2.1 catalog migration audit

The full import used the existing checksum-verified TLIDB cache. The new database was generated at a temporary path, validated, compared with the bundled v0.2.0 database, and only then installed.

| Record type | v0.2.0 | v0.2.1 | Change |
|---|---:|---:|---:|
| Categories | 49 | 49 | 0 |
| Equipment bases | 2,194 | 2,194 | 0 |
| Canonical affix families | 642 | 2,233 | +1,591 |
| Tier source rows | 13,303 | 13,303 | 0 |
| Other source table rows | 831 | 831 | 0 |
| Total retained source records | 16,328 | 16,328 | 0 |

The 642 old family IDs came from a broad TLIDB table comment. The v0.2.1 importer also checks the source modifier family and normalized property text. This split 382 broad IDs that contained multiple semantic families. Canonical tier rows still use the same 13,303 source row IDs, descriptions, tier labels, requirements and raw weights. No source tier was added, removed or changed during reimport.

The old family ID is stored as `legacy_family_id`. The runtime catalog exposes hidden aliases for saved equipment that still refers to a split family. A saved tier label resolves only when it identifies one source tier; duplicate matches are reported as ambiguous.

## Claw reference check

In the Claw `Suffix / Advanced` source group (`200010`), the previous import mixed several properties into one family. The new catalog keeps Attack Critical Strike Rating and chance to Multistrike in separate families. Both have their own T0+ through T7 descriptions, requirements and weights. Their rows match the published [TLIDB Claw craft table](https://tlidb.com/en/Claw).

## Validation

- SQLite schema: v3; integrity and foreign-key checks pass.
- Canonical families with incompatible semantic signatures: 0.
- Duplicate tier labels within canonical families: 0.
- Tier rows linked to the wrong modifier family: 0.
- Source tier records retained: 13,303 / 13,303.
- Base minimum Item Level values populated in this snapshot: 0. Suggestions therefore do not infer an Item Level requirement from character-level requirements.
- The source audit remains partial because some TLIDB classifications and base fields are still unresolved; see `tlidb-coverage.json` and `tlidb-unresolved.json`.
