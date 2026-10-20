# v0.2.1 Task Checklist

- [x] Read `AGENTS.md`, inspect the current catalog and UI, and run the baseline suite.
- [x] Compare Claw affix rows with the published TLIDB table and identify the family-ID collision.
- [x] Implement canonical family IDs, tier-record IDs, legacy ambiguity handling, and catalog validation.
- [x] Reimport cached catalog data and refresh/compare audit reports.
- [x] Implement compact affix/tier selection and base suggestion/manual selection behavior.
- [x] Add regression tests and update documentation/version.
- [x] Run full tests, QML smoke, and verify the Windows build workflow configuration.
- [ ] Run Windows standalone build/smoke locally; blocked by WSL interop error `UtilBindVsockAnyPort:317: socket failed 1`.
