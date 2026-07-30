# Power-0 Clean-Prefix Audit Contract

Date: 2026-07-31

Taskbook card: `POWER-ROUTE-01`

Status: retained route-faithful observation audit; no collection-policy or
action authority

## Task Card

Question: what usable natural Power-0 route evidence already exists before
requesting a new collection experiment?

Hypothesis: first-hit-bounded Stage-1 prefixes can establish route-faithful
Power acquisition and expose whether the current passive policy leaves
material resource variance, while remaining insufficient to establish a
causal collection policy.

Earliest decision effect: none. This audit compares retained observations; it
does not rank or issue actions.

Win condition:

- bind every result to an accepted natural Game Start Route-2/Lunatic
  full-route session and the complete raw-trace digest;
- exclude the first native-hit row and every later row;
- verify hard no-Bomb, unchanged lives/Bombs, passive item policy, disabled
  item objective, and initial resources `Power 0 / lives 2 / Bombs 3`;
- retain exact observed Power changes, item rows, decision gaps, and threshold
  crossings without inventing pickup or counterfactual action authority; and
- state the cheapest missing same-root gate.

Reject or defer: different-root Power variance, disappeared item rows, or
post-hit recovery must not be promoted into a collection-policy result. If no
clean prefix crosses a shot threshold, continue another high-ROI task rather
than treating practice-mode maximum Power as route evidence.

Out of scope: a new game trial, item-aware live ranking, post-death recovery,
causal enemy damage, kill timing, and strategy promotion.

## Revalidated Native Semantics

The relevant shipped-program boundaries were revalidated in the connected
IDA database before using the item model:

- `item_pool_spawn` at `0x004400A0` and `item_manager_update` at
  `0x00440500` own the 2,096-slot item pool;
- `player_test_item_collection` at `0x0044A5A0` performs the inclusive
  Route-2 pickup AABB with half-width 24 in player states 0, 3, and 4;
- small Power collection at `0x00440CF0` adds one Power and large Power
  collection at `0x00441170` adds eight;
- the normal-shot Power thresholds are the shipped bytes
  `8, 24, 48, 80, 128`; and
- the auto-homing exception at `0x00440843` reads
  `g_player_route_id` (`0x0164D0B1`). Route/team IDs 1 and 6 bypass the
  low-Power/unfocused restriction above the point line.

The last item corrects an inherited solver label: the model previously called
this input `stage_load_index`. That label was not supported by native
dataflow. The source and tests now carry `route_id`, and the IDA instruction
has a revalidated comment. For Sakuya/Remilia Route 2 the corrected value
still selects the ordinary branch, so this is a semantic correction rather
than evidence of a prior Route-2 physical regression.

## Evidence And Projection

The deterministic audit consumes two accepted natural full-route sessions:

| Run | Raw trace SHA-256 | Session SHA-256 |
| --- | --- | --- |
| `lunatic_route2_fullrun_unattended_20260730_002115` | `ffe52f97e959a92ec0adb06e418c17e2a97c8e2209f0978a1249f1b66e8a69d0` | `060c9b0042b33a0504a804b7edd7f2024e3bb45b6e8cc6ab13f314bc490fc976` |
| `lunatic_route2_fullrun_unattended_20260730_222529` | `a2ca77291996c4e390c8e403cd78e61edd43cbb1edb8fc27d8d8116ed8dcaada` | `74a32c28076fb439ef7ec982bfe298fe9755834e5c2033e60c9dee4bf5ee0f1a` |

Both sessions identify the expected executable, no-life-decrement patch,
Route 2, Lunatic, the full stage sequence, hard no-Bomb, trial acceptance, and
terminal unload. The second session's later replay-save error does not alter
its already accepted gameplay trace.

The audit projection ends immediately before the first decision with
`hit_started=true`. It accepts only Stage-1 route index 0 / gameplay epoch 0
decisions with hit count zero. Item rows are active observation rows, not
native generation identities. A Power increase between decisions is bounded
to that interval; a visible Power item that disappears in the same interval
is only a candidate because intervening native updates are not captured.

## Retained Result

| Run suffix | Clean decisions | Clean frame range | First-hit frame | Power | Next threshold |
| --- | ---: | --- | ---: | --- | ---: |
| `002115` | 789 | `1..2018` | 2,022 | `0 -> 5` | 3 |
| `222529` | 712 | `1..1690` | 1,692 | `0 -> 0` | 8 |

Observed:

- the first prefix records five separate `+1` Power intervals at or before
  frames 806, 827, 840, 1,975, and 1,978;
- each interval has one visible disappeared small-Power candidate in the
  preceding observation, but the item-specific source remains unverified;
- at or before the common clean horizon frame 1,692 the two observed Power
  values are 3 and 0;
- the first prefix contains 1,626 Power-item row observations and the second
  1,648; and
- item objectives were disabled, predicted collections were empty, and
  retained item utility was zero throughout both prefixes.

Inferred: passive movement can produce materially different early natural
Power histories.

Not established: the traces have different RNG/world roots, neither reaches
the first shot threshold 8 before its first hit, and no same-root
survival-feasible alternative action was executed. Therefore the audit has no
causal policy, shot-effect, later-damage, or survival-benefit authority.

The compact report is
`artifacts/runtime_reports/lunatic_route2_power0_clean_prefix_audit_20260731.json`,
SHA-256
`837244e9ca86bd70271cc4fa311bbeb67313e4d6c5281285de2872df5e791a6f`.
Independent regeneration is byte-identical.

Focused item-model/pool and audit tests plus Ruff pass. Complete Linux
discovery passes 1,385 tests in 13.048 seconds. Exact Windows UNC discovery
passes 1,385 tests in 27.239 seconds with the three existing skips.

## Formal Authority Answers

1. One audit state contains one retained decision observation: physical frame,
   stage/epoch, player position, resources, action, and active item rows. Two
   histories are not merged into a control state; identical Power does not
   imply identical items, RNG, enemies, or survival continuation.
2. There is no controller/nature recurrence and no hidden-branch
   maximization. The audit enumerates the retained prefix and explicitly
   refuses a different-root causal comparison.
3. Exact audit output answers only what these two physical clean prefixes
   observed. It does not answer whether an item-seeking action is safe or
   improves the later route.
4. The algorithm is exact for its schema-checked projection and complete
   input digest. A post-hit row, resource discontinuity, enabled item
   objective, non-passive item policy, identity mismatch, malformed item row,
   or claimed item-specific source falsifies acceptance.
5. There is no issue-time consumer. The report cannot change cadence, sensor
   state, problem version, or live fallback.

## Required Next Gate

The finite pickup/resource recurrence and complete 0..128 static SHT
capability ledger are now retained in
`POWER_PICKUP_CAPABILITY_LEDGER_CONTRACT_20260731.md`. They do not close the
missing physical pickup identity or route carry-forward below.

A valid `POWER-ROUTE-01` causal experiment needs:

- a natural, first-hit-bounded Route-2/Lunatic root at Power 0;
- same-root action branches restricted to the unchanged exact
  survival-feasible set;
- a same-update item pickup/end record before slot reuse, including item
  identity/value, motion, pickup geometry, resource delta, and RNG identity;
- carried-forward world and Power state through threshold crossing; and
- a later join measuring shot schedule, enemy damage/kill timing, exact
  viable reserve, and first-hit frontier.

Only held-out prefixes showing later combat or survival benefit without
reduced hard survival reserve can promote a collection preference. Until
then, `POWER-ROUTE-01` remains proposed and default-off.
