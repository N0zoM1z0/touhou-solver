# Route-2 Damageability And Static Shot-Coverage Contract

Date: 2026-07-31

Taskbook card: `COMBAT-FAST-01`

Status: offline semantic/static checkpoint; no live action authority

## Question

Which native gates must open before an ordinary player shot can subtract enemy
HP, and does the shipped Route-2 SHT corpus support a general rule that
releasing Focus gives wider or stronger normal-shot coverage?

The physical objective remains NMNB survival. Damage, earlier removal, and
phase shortening are secondary objectives only among actions already proved
viable and issue-safe.

## Revalidated Native Semantics

The following are **observed** in shipped instructions and relevant
callers/dataflow:

- `enemy_manager_update` (`0x0042C660`) enters the full update only when the
  enemy is active, `flags2 & 0x80` is clear, and `flags & 0x40000000` does not
  coincide with either an active Bomb or nonzero player transition byte
  `g_player_state` at `0x017D5EF8`.
- The player-damage block requires flags `0x10`, `0x20`, and `0x800` clear.
  Flag `0x80000000` blocks that block only while Bomb is active.
- Flag `0x40` admits player-shot collision work. It is not the HP-write gate.
- `player_compute_damage_to_enemy` (`0x00451670`) returns zero when the
  integer player-damage timer did not advance. Eligible shots require active
  state and either shot state 1 or shot type 3.
- Shot types 4 and 5 have an additional mode-2 collision suppression
  predicate. A nonzero hit callback runs after geometric overlap and may veto
  the hit.
- Collision uses the inclusive center/size AABB at `0x00451740`.
- During Bomb, each ordinary-shot contribution is divided by five with a
  minimum of one. The ordinary-shot subtotal remains uncapped in the return
  accumulator used by the separate damage-region pass and later HP path.
  `0x0045199F..0x004519BF` caps only the increment added to caller-owned enemy
  `+0x2E10`, a hit-feedback accumulator initialized at `0x0042A1FA`.
- Shot types 4, 5, and 6 pierce. Other hits enter state 2; their velocity is
  divided by eight except for shot type 3.
- An active spell owned by the target plus an active Bomb forces this
  player-shot result to zero.
- Flag `0x08` is the later, distinct HP-subtraction gate at `0x0042D275`.
  Therefore a true HP-damage candidate needs both `0x40` and `0x08`, plus all
  preceding gates, overlap, and positive post-scaling damage.

The optional alternate enemy hitbox is still part of native damage
arithmetic. Its result is normally divided by 1.7, or by 6.5 for Routes 3 and
11, unless the second call reports Bomb-region overlap. Later spell/phase
scaling and timeout/transition arithmetic remain outside the pure gate model.

The later arithmetic is now separately executable in
`resolve_enemy_hp_damage`:

- each primary/alternate `player_compute_damage_to_enemy` return first applies
  optional signed integer `106 * damage / 100`;
- absent a Bomb-region overlap signal, alternate damage is combined through
  truncating division by 6.5 for route byte 3/11 or 1.7 otherwise;
- combined positive damage is capped at 70;
- opaque special-enemy state can reduce no-overlap damage to
  `max(1, damage / 7)`, or on Bomb-region overlap either block it or use
  `max(1, trunc(damage / 2.5))`; and
- an active enemy `+0x5354` timer finally divides by 9 when flags bit 1 is set,
  otherwise it blocks damage, before HP `+0x2DFC` subtraction and frame-damage
  `+0x3354` publication.

The arithmetic is **observed**; the physical meanings and current values of
the `sub_406D70`, `sub_4178A0`, `sub_42DFF0`, `sub_41FD20`, and timer
predicates remain explicit inputs rather than guessed labels.

Fourteen durable IDA comments were added at `0x0042A1FA`, `0x0042C936`,
`0x0042C95D`, `0x0042CF47`, `0x0042D08B`, `0x0042D275`, `0x004516A9`,
`0x004518DC`, `0x004519A3`, `0x00451CB5`, `0x0042D135`, `0x0042D23E`,
`0x0042D289`, and `0x0042D33A`.

## Executable Boundary

`scripts/th08_enemy_damage_model.py` now exposes the native-ordered gates as:

1. manager update open;
2. damage block open;
3. player-shot collision open;
4. HP subtraction open.

Every closed result records explicit reasons. The model intentionally does not
claim geometric overlap, damage magnitude, a lethal crossing, or an end
reason.

`BossPhaseSnapshot.as_progress_state()` now consumes the observed player
transition state, Bomb state, spell-active state, and active spell owner. The
old projection was both incomplete and over-coarse: it omitted the separate
HP flag and rejected all Bomb-active damage even where native gates allow
reduced ordinary-shot damage.

`scripts/th08_player_shot_model.py` now also preserves SHT update/hit callback
indices, fails closed on unsupported callbacks, implements the state/type
collision gates, and retains the type-3 velocity exception. These changes
remain model semantics; they are not a live targeting policy.

## Static Atlas

`scripts/th08_route2_shot_coverage.py` and
`scripts/analysis/th08_route2_shot_coverage_atlas.py` enumerate every normal
Power partition in shipped `ply02a.sht` and `ply02as.sht`.

For each profile and Power interval, the atlas retains:

- exact native 0..19 shot-timer due rows under an empty-pool assumption;
- nominal emitted record count and raw base-damage sum;
- callback-7 RNG u16 consumption;
- merged enemy-point center-x support at 64, 128, and 192 units above the
  player, including the native center/size AABB footprint.

The unfocused callback-0 paths are revalidated scalar projections but have not
received a native-bit trigonometric differential. Focused callback-7 option
paths use a continuous outer envelope over:

- the revalidated angle support around `-pi/2`;
- the observed steady Route-2 option target offsets;
- the eight-unit option orbit;
- the shot's vertical and horizontal collision extents.

That envelope contains possible support. It does not prove that every enclosed
x is attainable at one immutable state or that multiple record envelopes can
be realized simultaneously. Treating it as damage coverage is therefore
**optimistic**, with unknown-direction numerical error from the remaining
x87/trigonometric differential.

## Result

The retained atlas has SHA-256
`2d62726829fd18a3f0df94f1f37862cdbd5a4e02eb7d3834269548bea97f73f4`.

Across six Power partitions and three target heights:

- the focused option outer envelope is wider in 14/18 comparisons;
- the unfocused primary scalar support is wider in 4/18 comparisons;
- no comparison is equal.

The only unfocused-wider rows are Power 80..127 and Power 128+, at target
rises 128 and 192. Even there, the focused side is an optimistic outer
envelope, so the comparison is useful for rejecting a coarse rule, not
promoting an inverse rule.

Nominal empty-pool 20-tick base-damage sums are:

| Power | Unfocused | Focused |
| --- | ---: | ---: |
| 0..7 | 192 | 248 |
| 8..23 | 232 | 352 |
| 24..47 | 312 | 395 |
| 48..79 | 400 | 427 |
| 80..127 | 492 | 431 |
| 128+ | 572 | 616 |

These sums are **not delivered damage**. They omit pool occupancy, target
motion, target dimensions, collision timing, hit-feedback accumulator
behavior, damage-region overlap, native scaling, and enemy lifetime.

The general statement “release Focus for wider coverage” is rejected. Focus,
Power, height, option/RNG state, and the target set must be modeled together.
The narrower retained hypothesis is that an exactly viable action schedule may
gain target-specific progress at a particular Power/state; that requires an
immutable causal root.

## Formal Problem Contract

Physical histories map to one static row when they share profile, Power
partition, shot-timer phase, and target height. The focused envelope then
deliberately merges distinct RNG and option phases that are not
control-equivalent. Therefore the row is not a controller state and cannot
authorize an action.

There is no controller/nature recurrence in this checkpoint. It does not
maximize hidden RNG branches separately and makes no causal policy choice.
The exact cadence enumeration answers only the declared empty-pool SHT
question. The geometry answers a proxy question about static horizontal
support, not whether a physical enemy is hit or killed.

The algorithm:

- exactly enumerates declared 0..19 due predicates and raw SHT damage values;
- uses a scalar trigonometric projection for fixed callback-0 paths;
- outer-bounds focused callback-7/orbit support.

The callback-7 outer bound is conservative for *possible position support* but
optimistic for *guaranteed damage*. A native root outside the reported
envelope would falsify the geometric bound. A root inside the envelope that
does not hit is expected and does not falsify it.

This report is offline and has no publication deadline. No issue-time consumer
reads it. The unchanged live Boolean policy and fresh local hard certificate
remain the fallback.

## Authority And Next Gate

This checkpoint grants:

- observed native gate semantics;
- tested implementation parity with those declared gates;
- shipped-data cadence and nominal base-damage accounting;
- static scalar/outer-envelope coverage evidence.

It grants no:

- target-selection or Focus-switch authority;
- actual HP-delta, kill, prevented-emission, or phase-shortening claim;
- survival equivalence;
- physical predictive authority.

Focused Ruff and 28 targeted tests pass. Complete Linux discovery passes
1,430 tests in 13.398 seconds. Complete Windows UNC discovery passes 1,430
tests in 28.178 seconds with the three existing skips.

The next causal gate must join one immutable native root to enemy generation,
flags/flags2, HP before/after, frame damage, shot timer and pool, option state,
RNG, target motion/hitboxes, and the exact action. Focused, unfocused, and
refocus schedules may then be compared only inside the unchanged exact viable
action set. Source-lifetime-to-emission linkage and item/drop/Power causality
remain separate open WS-H work.
