# v0.3 Crafting Rules and Evidence

Reviewed on **2026-10-19** for **SS14 — Tartarus**. The bundled SQLite catalog is a community snapshot; its manifest timestamp is 2026-10-20 00:20 UTC. That timestamp is not proof that each row matches the live game.

## Evidence labels

- **verified**: supported by an official game source for a stated season or operation.
- **source-derived**: transcribed or inferred from TLIDB or the user-provided game screenshot, without complete official confirmation.
- **experimental**: a deliberately selected model policy used to make a single craft attempt executable.
- **unknown**: the available sources do not establish the rule.

| Rule | Status | Evidence and implementation |
|---|---|---|
| Standard craft selects from a chosen affix pool and can add or replace an affix in the selected Prefix/Suffix location. | verified for the cited SS14 operation; source-derived detail | The official [SS14 Tartarus announcement](https://torchlight.xd.com/us/news/single?id=nezvlurrIS2B) describes random selection from the selected pool and adding/replacing in the designated location. The exact current UI flow comes from the user screenshot and [TLIDB Craft](https://tlidb.com/en/Craft). |
| Basic, Advanced, and Ultimate are separate craft categories; Prefix and Suffix pools are separate. | source-derived | [TLIDB Craft](https://tlidb.com/en/Craft) and the normalized `affix_pools`/`affix_families` records. The engine requires one exact pool ID, group, and category per attempt. |
| Ultimate crafting requires a Priceless item; the documented caps are two Advanced and two Ultimate affixes per item. | source-derived | [TLIDB Craft](https://tlidb.com/en/Craft) and [TLIDB Priceless](https://tlidb.com/en/Priceless). The engine checks these before drawing. The item-level category flag comes from the editor; cap scope follows TLIDB's per-equipment wording. |
| Item Level excludes tiers whose listed requirement is higher than the item. | source-derived | Tier requirements are preserved from TLIDB rows. The engine rejects a missing requirement and filters higher requirements before summing weights. |
| A family already present is omitted from eligible results, except the selected replacement target is removed from that check. | source-derived + experimental | The screenshot marks an existing affix type as unavailable. TLIDB and the official source do not establish the exact duplicate rule or replacement-target behavior. The v0.3 experiment allows the selected target's family back into its replacement pool; this is an explicit model policy, not an official rule. |
| Replacing a slot from a different selected category is allowed, and category caps count the post-replacement item. | experimental | The engine applies the chosen Basic/Advanced/Ultimate pool to the selected Prefix/Suffix slot and excludes the old target from category counts. The game's cross-category replacement semantics remain unknown. |
| Published weights represent a flat distribution across every eligible family-tier row. | experimental | The engine uses `P(row) = row weight / total eligible weight`; family probability is the sum of its rows, and conditional tier probability is `row weight / family weight`. Official odds are not claimed. |
| Weight-zero rows remain visible but are never drawn. | source-derived data + engine invariant | Exact zero values are retained from the catalog. Positive-weight rows alone participate in the random draw. A pool with total weight zero is unavailable. |
| A numeric value inside the displayed tier range can be generated. | unknown | The engine stores the source range as the new affix value and explicitly reports that no numeric value roll was simulated. |
| A valid simulation attempt has a separate in-game failure chance or consumes materials. | unknown / out of scope | No failure chance or material cost is simulated. “Craft once” means the local model produced one outcome; it does not predict whether the game accepts a real action. |
| Slot limits for every imported base are known. | unknown | Empty slots are offered only when catalog data lists a capacity. The Cane's three slots are tagged `visual_example_only` from the supplied screenshot and are visibly marked unverified. Other bases with unknown limits permit replacement of an occupied slot but block additions. |
| The live game's exact pool filtering, blocked-family weight redistribution, category-crossing replacement behavior, and family-then-tier distribution are confirmed. | unknown | These details are not established by the cited official source. They are not described as official mechanics. |

## Model behavior

The only executable model is **Experimental — TLIDB Weighted**. It is off by default and requires an explicit opt-in each session. It applies the listed integer weights to all eligible family-tier rows in one exact pool. Probability arithmetic uses integer totals and Python `Fraction` values before display formatting.

The engine keeps `T0`/`T0+` and all other zero-weight tier rows in the pool breakdown, but excludes every zero-weight row from sampling. It rejects malformed, missing, negative, or all-zero eligible weights. It records the random seed used for the attempt so a draw can be repeated in a focused reproduction.

An inspected family row is only a probability breakdown. Selecting it does not target or guarantee that affix. A craft attempt draws once from the entire selected pool. Replacing an affix retains the selected slot and instance identity. The selected target is omitted from family and category cap checks as an experimental policy. Adding requires a catalog-listed empty slot with an accepted capacity status; a numeric limit with `unknown` status is still rejected. No capacity is inferred from a similarly named base.

Only bases classified as standard-craftable `base` records enter the engine. Graft, Corrosion, Gear Empowerment, Legendary variants, and unknown base classifications are unavailable. The engine uses the catalog's semantic family signatures; it does not equate rows solely because they share a broad TLIDB source ID. This preserves v0.2.1 splits such as Claw Multistrike versus Critical Strike Rating.

Craft history exists only in the open application session. Undo restores the full equipment snapshot while preserving the user's existing save baseline. A manual equipment edit or replacing the open item clears undo history. Equipment JSON remains `schema_version=1` and contains no craft model, probability, seed, or history metadata.

## Sources

- Official Torchlight: Infinite, [SS14 Tartarus season announcement](https://torchlight.xd.com/us/news/single?id=nezvlurrIS2B)
- Community reference, [TLIDB Craft](https://tlidb.com/en/Craft)
- Community reference, [TLIDB home/catalog](https://tlidb.com/en/)
- Community reference, [TLIDB Claw](https://tlidb.com/en/Claw)
- Community reference, [TLIDB Priceless](https://tlidb.com/en/Priceless)
- User-provided crafting screenshot, showing a selected replacement slot, Basic/Advanced/Ultimate categories, a highest-tier label, and a duplicate-family row disabled with “same type already exists.”
