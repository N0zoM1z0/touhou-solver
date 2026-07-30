# Route-2 Loaded-SHT Provenance Contract

Date: 2026-07-31

Taskbook card: `COMBAT-FAST-01`

Status: offline exact loaded-content/provenance implementation; no retained
runtime sample, damage benefit, physical predictive, or live action authority

## Question

Can an active native player-shot slot be joined to an exact record in the
currently loaded pinned Route-2 SHTs, rather than inferred from matching
type/callback fields?

The prior normal-content closure proves what the pinned files contain.
Field compatibility alone does not prove that a runtime `source_record_pointer`
belongs to those files. This checkpoint closes that provenance representation
without launching TH08.

## Revalidated Loader And Ownership

The following are **observed** in shipped instructions and connected-IDB
dataflow:

- `player_sht_load` at `0x0044DD70` stores the loaded resource base through
  its destination pointer.
- Header `+0x02` is the unsigned level count. Level table entries begin at
  `+0x38` and contain one record-region offset plus signed Power threshold.
- The loader relocates each level offset by adding the loaded base.
- Each level consists of 56-byte records and one four-byte negative-period
  sentinel. The loader replaces callback indices at record
  `+0x28/+0x2C/+0x30/+0x34` through four executable callback tables.
- `player_emit_shot_level` reads the primary and secondary loaded bases from
  player `+0xE2A74/+0xE2A78`. After successful emission it stores the exact
  relocated source record pointer at shot slot `+0x480` and record
  callback-1/2/3 at slot `+0x474/+0x478/+0x47C`.
- The only nonzero callback relocation in the complete pinned Route-2
  primary/secondary corpus is secondary callback-0 index 7, which maps to
  `0x004501B0`. Every other callback field in these two files is zero.

IDA comments at `0x0044DE07` and `0x00450F83` retain the exact callback
relocation and player base-pointer/source-ownership boundaries. Existing
comments at `0x0044DD70`, `0x00451015`, and `0x004510EE` retain the broader
loader, selector, and slot mapping.

## Exact Normalization

`scripts/th08_runtime/route2_sht_provenance.py` reads:

- the adjacent primary/secondary base pointers;
- 1,584 bytes from the loaded primary SHT; and
- 3,568 bytes from the loaded secondary SHT.

For each loaded image it:

1. requires the exact level count and Power thresholds;
2. validates that relocated level pointers are distinct, ordered, aligned,
   and inside the image;
3. scans every 56-byte record to the exact terminal sentinel;
4. converts each level pointer back to its file-relative offset;
5. converts zero callbacks to index 0 and callback-0 pointer `0x004501B0` to
   index 7, rejecting every other pointer; and
6. SHA-256 hashes the normalized bytes and requires the pinned raw digest.

The resulting normalized digests are the shipped digests:

- primary:
  `4765744ab5bbf797746469d5a6afc6ec7d4b0371422b5aa5a2e54ae668c48885`;
- secondary:
  `f7554b3a32e16da01de9432e22609482a1c98a33212eb904ad47789079abebd3`.

The exact record map contains 87 source pointers: 53 normal-selector records
and 34 secondary Bomb-only special records. An active slot is normal only
when its exact `+0x480` pointer maps to one of the 53 normal records. Matching
type/callback fields without pointer ownership remains unknown.

## Snapshot And Report Integration

Combat projection schema `th08-native-combat-root-projection-v2` retains:

- both normalized loaded-SHT identities;
- exact profile, level, offset, and normal/special classification for each
  owned active source pointer; and
- counts of exact-normal versus non-normal-or-unknown active sources.

Because this changes immutable combat identity and acceptance, rolling native
snapshot schema is now `th08-native-snapshot-rolling-trial-v6` and causal
search schema is `th08-native-snapshot-causal-secondary-search-v4`.
No v5/v3 artifact is silently reinterpreted.

**Superseded later on 2026-07-31:** combat projection v4 adds the complete
damage-region pool, so the current immutable wrappers are rolling v7 and causal
v5. No v6/v4 artifact is silently reinterpreted as carrying damage regions.

`th08-native-combat-branch-comparison-v1` checks the root and every tick. Any
special or unknown active source keeps status
`survival_filtered_proxy_only_non_normal_or_unknown_shot_source`. This status
is independent of the existing hard player-phase-2 rejection and unresolved
overlap status. It cannot rank an action.

The loaded SHT pointers lie immediately beyond the earlier
`player_state_through_resource_transitions` semantic component, but the full
native snapshot already retains/restores their committed pages. V2 captures
and hashes them explicitly at each calculation seam rather than assuming
pointer stability.

## Formal Authority Questions

1. **Which histories merge?** Active shots merge into the normal content
   subset only when the complete loaded images normalize to both pinned
   digests and each exact source pointer maps to a normal record. Field-only
   matches, special records, nulls, and foreign pointers do not merge.
2. **Are hidden branches omitted?** No. Both normal profiles and both Bomb-
   only levels are scanned. Unknown pointers/callbacks fail closed. Callback-7
   RNG remains in each original-engine branch future.
3. **Does exact provenance answer the physical question?** It proves loaded
   byte identity and source-record ownership. It does not prove geometric hit,
   HP subtraction, kill, prevented emission, survival benefit, or Focus
   strategy.
4. **What falsifies it?** Any retained native loaded image that cannot be
   normalized to the pinned bytes despite verified Route-2 content, any
   native emission whose stored source pointer does not match its loaded
   record, or any expected normal source that maps to a special/unknown row.
5. **Can it be consumed before issue?** No. V2/v6/v4 are offline diagnostic
   schemas. The live Boolean policy and fresh local certificate are unchanged.

## Verification And Next Gate

Three dedicated tests cover exact relocation reversal/87-record ownership,
one scalar-byte digest corruption, and one foreign relocated callback.
Projection and branch tests cover exact normal and unknown source reporting.
Five projection tests and six branch-report tests pass. Ruff and diff checks
pass. Complete discovery passes 1,517 tests in 14.241 seconds on Linux and
31.181 seconds through the Windows UNC loader, with the three existing skips.

No TH08, replay, controller, native runner, or physical trial was launched.
The next authorized v6/v4 corpus must observe both normalized digests and
zero non-normal/unknown sources over every candidate root/tick before the
normal content closure is applied. Generation-safe damage still requires the
separate v4 lifecycle stream.
