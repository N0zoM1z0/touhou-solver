# Current Route-2 Combat And Resource Model

Last updated: 2026-07-31.

This consolidates the active WS-H boundary. It is an offline/native diagnostic
model and has no live ranking authority yet.

## Goal

Determine whether survival-feasible control can improve the whole solver by:

- killing ordinary enemies before their patterns saturate;
- choosing Focus dynamically for movement and shot coverage;
- collecting early Power when it causally improves later combat/survival;
- shortening supported boss/nonspell exposure without weakening survival.

The decision metric is later native survival/hits, not static shot width,
damage proxy, pickup count, or report completeness.

## Observed Native Semantics

### Player shots

- Route-2 normal SHT selection is indexed by Focus and six Power partitions.
- All 53 selector-reachable normal records are type 0 with zero update and hit
  callbacks. Bomb-only or unowned source records fail closed.
- Focused option emission callback 7 consumes two u16 RNG calls per due
  option shot when a free slot exists. Primary normal shots consume no
  callback RNG.
- The 128-slot player-shot pool retains exact source-record ownership,
  position/hitbox, velocity/angle, timers, damage/state/type, Focus-at-birth,
  ANM index, and callbacks.
- Spawn and per-frame motion preserve binary32 storage boundaries. Static CRT
  `sin/cos` low-bit parity is still unknown-direction.
- Static spread does not justify “always unfocus”: focused outer coverage is
  wider in 14 of 18 audited rows; unfocused is wider in four. Nominal
  empty-pool base damage favors unfocused only at Power 80..127.

### Enemy damage and lifecycle

- Enemy manager processing is slot ordered; nonpiercing shot and
  damage-region mutation carry across targets.
- Supported ordinary damage retains primary/alternate hitboxes, frame damage,
  HP/max HP, blockers/timers/mode predicates, resolved HP writes, and exact
  active-clear ordering.
- Returned ordinary-shot damage is not capped by the separate 50-point
  hit-feedback clamp.
- The later damage path includes native predicates for 106/100 scaling,
  route-specific divisors, a resolved-damage cap of 70, special/Bomb-region
  divisors, timer/block branches, and final HP/frame-damage writes. Predicate
  labels remain opaque where not revalidated.
- Forced HP zero, boss/spell cleanup, and message-start cleanup are not
  player-shot kills. A kill requires exact pre-HP/damage/post-HP arithmetic,
  no preceding forced zero, defeat mode 0, and the ordered active clear.
- Boss transition ordering and the selected successor registry are part of
  phase identity; threshold overshoot does not itself identify the next
  phase.

### Lifecycle trace

The default-off diagnostic ring is one 256-entry, 128-byte, total-order event
stream covering:

- two enemy allocations;
- exact active-clear retirements and forced-HP-zero;
- paired damage begin/commit;
- successful item allocation, non-pickup cull, and pickup begin/commit.

Paired commits publish only when marker, pointer, and manager frame agree.
Overflow, malformed serial advancement, pointer/slot disagreement, or unsafe
rollback cuts authority. No runtime ring corpus has yet promoted this
implementation beyond synthetic/offline authority.

The lowerer accepts only continuous zero-drop prefixes. It constructs explicit
enemy/item generations and joins:

`static candidate -> enemy generation -> damage -> defeat -> item generation -> pickup -> resource delta`

Baseline-active objects remain partial starts. Non-timeline child/phase roots
remain explicit unmatched programs.

### Items and Power

- Power additions cap immediately at 128.
- Full-Power conversion changes eligible active Power items according to
  native order.
- Defeat drops, item allocation, pre-update movement, cull, pickup, and
  resource writes are separate events.
- Effective item type 7 uses its one native cursor probe; scanning farther is
  incorrect.
- Message cleanup can move all active items into homing state. Homing is not
  evidence of pickup or Power gain.
- Exact Power, lives, and Bomb values must agree at root and every tick.
  Lives decrease is a hard survival failure. Bomb selection/active state or
  Bomb-stock decrease rejects an NMNB branch.

## Static Coverage

The pinned shipped-content manifest covers the mandatory Route-2 ECL/SHT
inputs. Static atlases currently index:

- mandatory timeline events;
- source/emission program candidates;
- boss phase configurations and successor identities;
- normal-shot content/coverage;
- defeat-drop opportunities;
- the route-wide combat/resource candidate intersection;
- message-cleanup seams.

These atlases select roots; they do not prove runtime execution, a kill
deadline, allocation/pickup, prevented hostile fire, or survival benefit.

Compact retained reports:

- `artifacts/runtime_reports/th08_immutable_content_manifest_20260731.json`
- `artifacts/runtime_reports/th08_mandatory_event_atlas_20260731.json`
- `artifacts/runtime_reports/th08_route2_focus_shot_emission_root2129_20260731.json`
- `artifacts/runtime_reports/th08_route2_normal_shot_content_audit_20260731.json`
- `artifacts/runtime_reports/th08_route2_normal_shot_coverage_atlas_20260731.json`
- `artifacts/runtime_reports/th08_route2_boss_phase_configuration_atlas_20260731.json`
- `artifacts/runtime_reports/th08_source_emission_program_atlas_20260731.json`
- `artifacts/runtime_reports/th08_route2_item_drop_opportunity_atlas_20260731.json`
- `artifacts/runtime_reports/th08_route2_power_capability_ledger_20260731.json`
- `artifacts/runtime_reports/th08_route2_combat_resource_candidate_board_20260731.json`
- `artifacts/runtime_reports/th08_route2_message_cleanup_seam_atlas_20260731.json`

## Current Physical Evidence

At the generation-safe Stage-5 root 4300, an eight-tick unfocus then refocus
schedule **observably** defeated the 20-HP slot-16 enemy and suppressed three
hostile births per nine-frame cadence; the endpoint hostile count was 539
instead of 548. Applying the current live global viability model independently
to both exact native branches produced identical layer-0 viable masks and
safe-action masks at frames 4314, 4323, and 4332. This says the current metric
did not change on that root; it was not used alone to falsify the idea.

The 2026-07-31 Stage 3/4A/5 ring ran with every WS-H ranking feature disabled.
It observed 5/13/12 hits, first hits at 2150/2555/2124, zero Bombs, and valid
replays. Different-root comparisons were 15→5, 10→13, and 19→12. These are
workload baselines only and give no causal authority to this model.

A later default-off Stage-5 physical gate exercised the narrow
kill-before-saturation delivery rule. It observed 109 matching target
decisions, requested 37 same-direction unfocused peers, and applied 27 after
fresh issue certification; four unsafe peers and six decisions without a
fresh transaction preserved baseline control. The run was accepted no-Bomb
with first hit 6981 and 13 total hits. Relative to the different-RNG 2124/12
baseline, that is a later first hit but one worse total hit. Global allowed
actions and viability-constrained decisions were both zero, so this gate did
not show that early killing rescues the global kernel. It also does not
falsify the separate same-root native hostile-birth suppression.

Post-run gate reconstruction found that no rolling solve was submitted: all
13,306 player projections were exact (12,594 zero-lag and 712 one-step), but
the 120-frame diagnostic scale schedule was shorter than the 161–162 frames
required by sensor age + initial asynchronous lead + the kernel. The repaired
269-frame diagnostic schedule can publish/query shadow policies but cannot
constrain live actions because its future scale remains unknown-direction.

The rotated Stage-4A gate confirmed the repair physically: 1,926 submissions,
1,925 completions, 1,915 unique policies, and 12,156 available queries. The
kernel was losing/empty for 6,635 queries, and every one of 16 hits followed
kernel exhaustion. Early kill made 39 actual fresh-safe selections, but 26
were already in a losing shadow-global state and only nine were also members
of a winning shadow-global action set. This rejects short local safety as the
global survival filter; it does not reject killing enemies earlier.

The latest full-route game-start baseline is 68 hits, zero Bombs, with
per-stage counts 2/3/5/20/15/23.

## Next Decisive Experiment

Do not add more atlas/schema work unless it blocks this experiment:

1. Establish exact ordinary-stage global action authority or an equivalent
   causal pre-exhaustion viability filter.
2. Test the combat objective before kernel loss and only inside the exact
   winning action set.
3. Repeat the native kill/prevented-birth result on a second ordinary enemy
   and root.
3. Keep the live HP/alignment rule default-off and unchanged until the second
   root and a rotated Stage 3/4A physical workload agree.
4. Return `UNKNOWN` at the first unsupported event; do not infer a causal A/B
   from the different-RNG physical totals.

After that, test survival-feasible early Power collection on a clean prefix
that crosses a Power threshold and has a later combat/survival join. Do not
model post-death recovery for an NMNB policy.

## Active Counterexamples

- CE-0220: item ledger must cap Power and preserve native order.
- CE-0221–0223: boss phase identity includes ordered transition and successor
  registry state.
- CE-0224–0225: ring stride encoding and paired publication must fail closed.
- CE-0226: damage and hit-feedback accumulators are distinct.
- CE-0227: unconsumed timeline engine events invalidate integrated simulation.
- CE-0228: effective type 7 performs only one cursor probe.
- CE-0230: a physically exercised early-kill preference delayed the first hit
  but did not improve total hits or make global guidance available.
- CE-0229: different-root physical totals are not causal A/B evidence.
