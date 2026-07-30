# Route-2 Normal-Shot Content Closure Contract

Date: 2026-07-31

Taskbook card: `COMBAT-FAST-01`

Status: pinned shipped-content/native-selector checkpoint; no runtime damage,
combat-benefit, physical predictive, or live action authority

## Question

Do the type-4/5 collision predicate or nonzero update/hit callbacks occur in
any Route-2 normal shot that the no-Bomb Power selector can reach, or can
those unknowns be restricted to explicitly contaminated/non-normal roots?

This is a general WS-H damage-path question, not an individual hit-producer
investigation. The physical objective remains NMNB survival. Closing a static
content branch does not prove delivered damage, kill, prevented emission, or
safe Focus switching.

## Revalidated Native Selector

The following are **observed** in shipped instructions and connected-IDB
dataflow:

- `player_emit_shot_level` at `0x00450F60` selects the primary or secondary
  SHT using player Focus-logic byte `+0x03`.
- Normal selection starts at the chosen SHT level table and advances while
  truncated current Power is greater than or equal to the current signed
  threshold. Route-2 gameplay Power is bounded to 0..128.
- The special Route-2 override at `0x00450FDC..0x00451000` selects secondary
  level 6 or 7 only while a Bomb callback is active, its callback index is
  odd, and its local timer has reached 60. It is not a normal Power-selection
  edge.
- After one record emits, `0x004510D9..0x00451118` stores the relocated SHT
  record pointer at slot `+0x480`, record callback-1 at slot `+0x474`,
  callback-2 at `+0x478`, and callback-3 at `+0x47C`.
- `player_update_shots` at `0x00451150` calls nonzero slot `+0x474` before
  default motion. `player_compute_damage_to_enemy` at `0x00451670` applies
  the type-4/5 predicate and invokes nonzero slot `+0x47C` after geometric
  overlap.

These observations explain why normal content must be audited by reachable
level, shot type, callback-1, and callback-3. Callback-0 is the emission
callback; Route-2 callback 7 is already revalidated as the focused random-
spread birth calculation and does not become an update or hit callback.
IDA comments at `0x00451015` and `0x004510EE` retain the normal/special level
boundary and relocated callback-field mapping.

## Pinned Content Audit

`scripts/analysis/th08_route2_normal_shot_content_audit.py` parses the
locally recovered shipped resources and refuses any other byte identity:

- `ply02a.sht`:
  `4765744ab5bbf797746469d5a6afc6ec7d4b0371422b5aa5a2e54ae668c48885`;
- `ply02as.sht`:
  `f7554b3a32e16da01de9432e22609482a1c98a33212eb904ad47789079abebd3`.

Both normal selectors have exact thresholds
`8, 24, 48, 80, 128, 999`. The audit stops at the first terminal 999 level,
matching the native normal selector.

The normal reachable corpus contains:

| Profile | Records | Shot types | Callback-0 | Callback-1 | Callback-3 |
| --- | ---: | --- | --- | --- | --- |
| unfocused primary | 26 | `{0}` | `{0}` | `{0}` | `{0}` |
| focused secondary | 27 | `{0}` | `{0, 7}` | `{0}` | `{0}` |

Therefore all 53 normal records avoid type 4/5, nonzero update callbacks, and
nonzero hit callbacks. Secondary levels 6/7 contain 34 type-6 special records
with zero callbacks, but they are reachable only through the separate Bomb
override and are excluded from the normal no-Bomb content claim.

Retained report:
`artifacts/runtime_reports/th08_route2_normal_shot_content_audit_20260731.json`,
SHA-256
`4361ec2814a8885dd6c4dd17bd42039f5a9bb38bccbeebcb8c43b6816df6d4e1`.

## Runtime Compatibility Boundary

The static audit does not assume that every arbitrary snapshot root has a
clean no-Bomb history. A root is compatible with this closure only when:

1. replay/native route identity is Route 2;
2. retained replay history and all branch actions contain no Bomb input;
3. every active shot at the root and future seams has runtime
   `type == 0`, update-callback pointer zero, and hit-callback pointer zero;
4. neither the root nor any branch tick is native player phase 2.

`th08-native-combat-root-projection-v1` now marks every active slot against
those damage-path criteria and reports compatible/incompatible counts.
`th08-native-combat-branch-comparison-v1` carries the root plus tick counts.
An incompatible active slot keeps the branch explicitly
`survival_filtered_proxy_only_non_normal_shot_content`; it does not trigger a
broad assumption or a content-based damage claim.

The criteria do not prove exact SHT record provenance by themselves. They
only prove that the runtime slot lies inside the normal content's supported
type/update/hit damage-path subset. Source-record pointer identity remains
retained for later native corpus validation.

## Formal Authority Questions

1. **Which histories merge?** No histories merge on this report alone. Static
   records merge only by pinned SHT identity and native-reachable normal level.
   Runtime application additionally requires exact Route-2/no-Bomb history,
   compatible active slots, and no hit phase.
2. **Are hidden branches omitted?** The direct Bomb levels are separated, not
   silently treated as normal. Any incompatible runtime slot stays explicit.
   Callback-7 RNG remains branch-local in the existing native future.
3. **Does exact content closure answer the physical question?** It answers
   only whether normal Route-2 SHT content can reach type-4/5 or update/hit
   callbacks. It does not answer overlap, HP subtraction, kill, target
   selection, exposure, resources, or survival.
4. **What falsifies it?** A byte-identical pinned SHT parse with a reachable
   normal type-4/5, callback-1, or callback-3 record; native selector dataflow
   that reaches levels 6/7 without the Bomb override; or a compatible declared
   root that emits an incompatible slot before any Bomb/hit edge.
5. **Can it be consumed before issue?** No. The audit and branch report are
   offline. The live Boolean policy and fresh local certificate remain
   unchanged.

## Result And Next Gate

The normal Route-2 content branch is closed for its declared type/update/hit
boundary. This avoids spending reverse-engineering effort on unreachable
normal type-4/5 and hit-callback cases. It does not remove fail-closed handling
for arbitrary or contaminated roots.

Three focused content-audit tests, four projection tests, and five combat-
report tests pass. Ruff and diff checks pass. Complete discovery passes 1,512
tests in 13.868 seconds on Linux and 31.165 seconds through the Windows UNC
loader, with the three existing skips. No TH08, replay, controller, native
runner, or physical trial was launched.

The next explicitly authorized v5/v3 corpus must verify that every root/tick
used by `COMBAT-FAST-01` satisfies the runtime compatibility conditions, then
join v4 generation-safe damage before any damage or kill benefit is promoted.
Without runtime authorization, continue the next general WS-H semantic
dependency.
