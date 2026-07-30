# Route-2 Combat/Resource Candidate Board Contract

Date: 2026-07-31

Taskbook cards: `COMBAT-KILL-01`, `POWER-ROUTE-01`, `ROUTE-OPT-01`

Status: immutable cross-atlas candidate checkpoint; runtime causal join
required

## Question

Which pinned Route-2 enemy program roots simultaneously have:

- ordinary-compatible future hostile emission value; and
- a static Power opportunity through the native default defeat request or an
  explicit configured Power count?

The purpose is to select reusable fixed-root causal experiments across event
families, not to assign a fictional combat/resource utility score. The
physical objective remains NMNB survival. Damage and collection remain
subordinate to exact viability.

## Inputs And Exact Join

The board consumes two retained reports:

- source/emission program atlas SHA-256
  `6ae9494a40ff5a08143564c653b3c2007e1125063a16b1108854db84f74531b5`;
- item/drop opportunity atlas SHA-256
  `0692985c579a3040def4e635115a3399c0e4323a338d5f03427c4930821dc0b0`.

Both inputs must preserve their accepted schemas, immutable content manifest,
route profile, stage order, and per-stage ECL identity. The join key is:

```text
(route ECL SHA-256, root subroutine)
```

Every one of the 70 timeline-rooted source programs must have exactly one
matching item-atlas program. A duplicate, missing root, changed input hash,
schema mismatch, manifest mismatch, route mismatch, or ECL mismatch fails
report generation.

The item atlas has 148 additional child, cross-enemy, enemy-end, and phase
successor program roots. They remain explicit `item_only_program_count` and
are not silently merged into a timeline source generation.

## Candidate Cohorts

A program enters `ordinary_emitter_power_intersection` only when:

1. the source atlas classifies it as an ordinary-compatible static emitter
   candidate; and
2. the item atlas gives it at least one Power signal:
   default small-Power on an eligible HP defeat, a positive configured extra
   Power count, or a positive direct Power-bundle count.

The board then emits independent named cohorts for:

- default primary small Power;
- configured extra Power;
- direct Power bundles;
- source-owned direct emission;
- child-emitter births; and
- staged periodic control.

These labels overlap deliberately. They are categorical experiment families,
not additive weights. The board performs no scalar ranking, treats a local VM
timer as no kill deadline, treats an item signal as no pickup, and treats an
emission site as no prevented birth.

## Reproduction

Analyzer:

`scripts/analysis/th08_route2_combat_resource_candidate_board.py`

Command:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_route2_combat_resource_candidate_board.py \
  --source-atlas \
    artifacts/runtime_reports/th08_source_emission_program_atlas_20260731.json \
  --item-atlas \
    artifacts/runtime_reports/th08_route2_item_drop_opportunity_atlas_20260731.json \
  --output \
    artifacts/runtime_reports/th08_route2_combat_resource_candidate_board_20260731.json
```

Retained artifact SHA-256:

`34e70a50e6c38c8241df0425be83367e6bf9e369106d600956d5a052dfa8cfea`

Internal pre-digest:

`aae2ca5e332fb0ebeb886076884034ebd9e5f3dff9888b86dadccdd44c2c8da9`

Size: 145,956 bytes. Exact regeneration is test-enforced.

## Result

All 39 ordinary static emitter candidates also retain the native default
small-Power opportunity on an eligible HP defeat. They cover 909 timeline
spawn instances. Sixteen of those programs additionally configure a positive
extra Power count and cover 97 timeline spawn instances.

| Stage | Joined source programs | Ordinary emitter/Power intersections | Intersection spawns | Configured-extra-Power intersections |
| --- | ---: | ---: | ---: | ---: |
| Stage 1 | 10 | 6 | 173 | 0 |
| Stage 2 | 12 | 9 | 292 | 4 |
| Stage 3 | 14 | 9 | 81 | 4 |
| Stage 4A | 10 | 5 | 241 | 1 |
| Stage 5 | 15 | 8 | 108 | 5 |
| Final B | 9 | 2 | 14 | 2 |
| **Total** | **70** | **39** | **909** | **16** |

The intersection spans three overlapping hostile-source mechanisms:

| Mechanism cohort | Programs | Timeline spawns |
| --- | ---: | ---: |
| Direct source-owned emission | 32 | 878 |
| Child-emitter birth | 14 | 74 |
| Staged periodic control | 13 | 479 |

Nine ordinary-compatible resource programs covering 60 spawns have no static
emitter-candidate classification. They remain a resource-only comparison
cohort rather than being discarded.

Representative configured-extra-Power rows expose distinct experiment
families:

- Stage-2 root 11: eight spawns, three direct sites, three periodic controls,
  configured extra Power count 2;
- Stage-3 root 0: twenty spawns, seven direct sites, configured extra Power
  count 2;
- Stage-4A root 7: seventeen spawns, eight child-emitter sites, configured
  extra Power count 4;
- Stage-5 roots 2/9/15/22: child-emitter-heavy programs with configured extra
  Power count 4; and
- Final-B root 7: twelve spawns, one direct and one child-emitter site,
  configured extra Power count 2.

These are diversity examples, not a utility ordering. Every row still carries
`partial_with_semantic_residuals` source coverage and a complete runtime-join
debt.

## Formal Problem Contract

One board state is:

```text
(content manifest,
 route profile,
 stage and ECL identity,
 timeline root subroutine,
 static source-emission metrics,
 static item/drop signals,
 named mechanism cohorts)
```

Two physical histories mapping to one row are not control-equivalent. They can
differ in enemy generation, current VM state, damageability, HP, end reason,
emission timing, existing projectile persistence, drop fields, RNG, item-pool
capacity/order, player position/Focus/Power, pickup safety, and later phase
state.

There is no controller/nature recurrence and no option-graph edge in this
checkpoint. Hidden runtime branches are not separately maximized. The static
CFG inputs remain conservative overapproximations.

If solved exactly, the finite board answers only which immutable source roots
are members of declared static emission/resource cohorts. It does not answer
whether one action kills the source, prevents a birth, allocates or collects
an item, crosses a useful threshold, or preserves a later continuation.

The algorithm exactly preserves input hashes, schema/profile identity, ECL
identity, root keys, and categorical cohort predicates. Runtime execution,
generation/end reason, absolute deadline, prevented birth, allocation,
pickup, and downstream benefit are omitted with unknown direction. They
remain outside hard safety authority.

A source root absent from the item atlas, a duplicate root, or a mismatched
ECL identity falsifies the join and fails closed. A runtime generation whose
exact root executes outside the input atlas component falsifies source
coverage. An eligible ordinary HP defeat with untouched default fields but no
small-Power request falsifies the resource predicate.

The analyzer is offline and has no publication deadline. No issue-time
consumer reads the board. The unchanged Boolean policy plus a fresh local
hard certificate remains the fallback.

## Authority And Next Gate

This checkpoint grants:

- an exact immutable-key join across the two accepted static atlases;
- route-wide named combat/resource candidate cohorts; and
- a mechanism-diverse selection board for fixed-root causal experiments.

It grants no:

- runtime generation or instruction execution;
- kill/end reason, deadline, prevented birth, or exposure reduction;
- item allocation, pickup, Power gain, or safe collection;
- causal later combat/survival benefit;
- phase option edge, planner ranking, action authority, or physical promotion.

The next experiment must select more than one immutable root from more than
one mechanism/event family. From each identical native root it must compare:

```text
pure survival
versus survival-feasible damage/resource policy
```

Each branch must regenerate its own causal future and join:

```text
enemy generation/root/VM PC
+ damageability and ordered HP/end event
+ hostile births and persistence
+ item request/allocation/pickup
+ Power threshold and shot-state change
+ exact viable-action reserve and terminal continuation
```

Only an exact terminal continuation can become a later `ROUTE-OPT-01` edge.
This board itself is not an option graph and cannot promote one.

Three focused board tests and Ruff pass. Complete Linux discovery passes
1,487 tests in 15.671 seconds. Complete Windows UNC discovery passes 1,487
tests in 30.206 seconds with the three existing skips. No TH08, controller,
replay, or physical trial was run.
