# Route-2 Item/Drop Opportunity Atlas Contract

Date: 2026-07-31

Taskbook cards: `POWER-ROUTE-01`, `COMBAT-KILL-01`

Status: shipped-native recurrence and static route opportunity checkpoint;
runtime execution/pickup join required

## Question

Across the full Sakuya/Remilia Lunatic Final-B route, which pinned enemy
programs configure or directly request items, and which ordinary allocation
programs retain the native template's default small-Power defeat request?

The physical objective remains NMNB survival. Power, damage, and item
collection are subordinate objectives inside the viable set. This checkpoint
does not infer that a static instruction executes, an enemy ends by player
damage, an item allocation succeeds, a pickup occurs, or later combat becomes
shorter or safer.

## Revalidated Native Semantics

The following are **observed** in shipped instructions, relevant callers, and
manager initialization dataflow:

- `enemy_manager_initialize_template_and_pool` at `0x00429E00` clears the
  manager and template before the template is copied by both allocation
  paths. The inherited enemy drop fields therefore start as:
  primary type `0` (small Power), extra point count `0`, and extra Power
  count `0` at enemy offsets `+0x3304`, `+0x3308`, and `+0x330C`.
- ECL `0x8F` overwrites the primary type at `+0x3304`.
- ECL `0x90` writes its first evaluated argument to extra point count
  `+0x3308` and its second to extra Power count `+0x330C`.
- `enemy_spawn_configured_defeat_items` at `0x0042BEA0` is invoked by defeat
  modes 0, 1, and 2. Mode 3 bypasses it.
- The helper requests, in order, the primary item, extra Power items, and
  extra point items. A nonnegative primary type is requested at enemy
  position. Type `-1` uses the global every-third-call 32-entry schedule;
  values below `-1` suppress the primary request.
- Under the physical no-Bomb scope, the primary request has free motion.
  Bomb-related damage selects homing only for that primary request. Extra
  count requests always use free motion and independently randomized
  `x/y +/-64` positions.
- Below Power 128, configured extra Power counts request small Power. At
  Power 128 they request point items instead. The two count fields are cleared
  after the helper returns.
- ECL `0x8D` requests one supplied type at enemy position with free motion.
- ECL `0x8E` requests a randomized bundle. Below Power 128 the first request
  is large Power and the remainder are small Power; at Power 128 all are
  point items.
- ECL `0xA8` requests the supplied count of randomized point items.
- Built-in enemy callback 31 requests type 5 when no Bomb is active and type 3
  during a Bomb. No route-reachable callback-31 site exists in the six pinned
  Route-2 ECL files.

The analyzer models item **requests** before item-manager allocation. Native
playfield rejection, rotating-pool allocation, active-list update order,
auto-homing, pickup collision, and Power application remain in the existing
item-pool recurrence and are not silently assumed successful here.

Boss phase helpers can replace the template primary with `-2` and clear the
counts. The default-small-Power classification is therefore limited to
allocation-origin programs with no reachable Boss-control opcode, no `0x8F`,
no dynamic defeat mode, and at least one helper-invoking possible mode. It is
a strong static ordinary-enemy candidate, not a concrete-generation fact.

## Executable Recurrence

`scripts/th08_enemy_item_drop_model.py` preserves:

- the three native enemy fields and defeat-mode gate;
- exact primary/count request order;
- the global uint16 every-third primary schedule;
- native Power-128 type conversion;
- native per-item RNG call order and square position support;
- primary-only Bomb-related homing;
- post-helper count clearing; and
- mode-3 bypass without count clearing.

Its result is an ordered tuple of `ItemSpawnRequest` values. Applying the
separate `step_item_pool` recurrence is required to decide which requests
allocate and how later items update. Nine deterministic tests cover template
defaults, Bomb-related primary motion, full-Power conversion, mode-3 bypass,
the `-1` schedule, `<-1` suppression, direct item requests, bundle
composition, callback types, RNG consumption, and invalid states.

## Static Program Ownership

The atlas uses the same shipped-content manifest, route ID 2, difficulty index
3, and difficulty mask `0x08` as the source/emission atlas. For every program
root it traverses only same-enemy:

- direct calls;
- interrupt slots; and
- auxiliary VMs.

Timeline and child-spawn targets are allocation origins. Cross-enemy calls,
enemy-end targets, and health/timeout phase successors remain separate
program roots. Each row carries a join key of ECL SHA-256 plus root
subroutine, so it can be joined to the source/emission atlas without merging
physical generations.

All known route/difficulty predicates are folded. Other CFG branches remain
conservative. Every route-reachable item site must map to at least one
program root or report generation fails closed.

## Reproduction

Analyzer:

`scripts/analysis/th08_route2_item_drop_opportunity_atlas.py`

Command:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_route2_item_drop_opportunity_atlas.py \
  --decoded-dir artifacts/decoded \
  --content-manifest \
    artifacts/runtime_reports/th08_immutable_content_manifest_20260731.json \
  --output \
    artifacts/runtime_reports/th08_route2_item_drop_opportunity_atlas_20260731.json
```

Retained artifact SHA-256:

`0692985c579a3040def4e635115a3399c0e4323a338d5f03427c4930821dc0b0`

Internal pre-digest:

`cf89e9fc670d972b67d12ef2148391d1bf99649d5f434ebbdddd99a845f64659`

Size: 929,115 bytes. Exact in-process regeneration is a required test.

## Result

The six pinned files contain 60 route-reachable item/drop configuration sites
under the conservative CFG. All 60 use literal operands; none is unreachable
and none is left outside a program root.

| Stage | Timeline spawns | Program roots | Allocation programs | Default-small-Power candidates | Item sites | Reachable item opcodes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Stage 1 | 177 | 28 | 21 | 7 | 3 | `0x90`: 3 |
| Stage 2 | 295 | 34 | 24 | 10 | 9 | `0x8E`: 1, `0x90`: 7, `0xA8`: 1 |
| Stage 3 | 121 | 38 | 27 | 11 | 14 | `0x8D`: 1, `0x8E`: 3, `0x90`: 7, `0xA8`: 3 |
| Stage 4A | 247 | 33 | 20 | 14 | 9 | `0x8E`: 2, `0x90`: 5, `0xA8`: 2 |
| Stage 5 | 130 | 48 | 37 | 12 | 13 | `0x8D`: 1, `0x8E`: 1, `0x90`: 10, `0xA8`: 1 |
| Final B | 21 | 37 | 22 | 2 | 12 | `0x8D`: 1, `0x8E`: 1, `0x90`: 9, `0xA8`: 1 |
| **Total** | **991** | **218** | **151** | **56** | **60** | `0x8D`: 3, `0x8E`: 8, `0x90`: 41, `0xA8`: 8 |

There is no route-reachable `0x8F`, so shipped Route-2 ECL never directly
overwrites the primary defeat item. This does not rule out native Boss helper
changes, non-HP retirement, pool failure, or an unexecuted program.

One concrete atlas row illustrates the joined opportunity rather than a
policy: Stage-2 root 7 is timeline-allocated, ordinary-compatible, retains
the default primary small-Power candidate, and has a literal configured extra
Power count of 2. Static availability alone cannot say that this generation
spawns, is killed, allocates three items, or that collecting them is safe.

The useful general strategy consequence is a single causal chain:

```text
survival-feasible target/action
-> ordered player-shot HP defeat
-> configured item requests
-> successful allocation
-> Focus/route-conditioned homing and safe pickup
-> Power threshold crossing
-> changed shot coverage/damage
-> later verified phase or exposure reduction
```

Kill timing, Focus, item collection, Power, and later combat must therefore be
measured together rather than ranked as independent scalar bonuses.

## Formal Problem Contract

One static index state is:

```text
(content digest,
 stage,
 root subroutine,
 conservative same-source component,
 allocation/program origins,
 literal item/drop sites,
 ordinary/Boss-compatible classification)
```

Two physical histories mapping to one row are not control-equivalent. They can
differ in enemy generation, current PC/call stack, defeat mode, live drop
fields, end reason, Bomb-related damage, enemy position, Power, RNG, item-pool
cursor/capacity, active-list order, player Focus/position, pickup safety, and
later target state.

There is no controller/nature recurrence in the atlas. The executable drop
recurrence is exact only after its declared concrete inputs are supplied.
Hidden runtime branches are not separately maximized, and static CFG
reachability deliberately overapproximates instruction execution.

If solved exactly, this finite problem answers which ordered item requests one
concrete native drop configuration produces and which pinned programs may
configure such requests. It does not answer whether a physical item is born,
collected, valuable before route end, or attainable without losing survival
viability.

The algorithm exactly preserves the revalidated handler order, literal
operands, native RNG order, immutable content identity, and declared
same-source ownership partition. Conservative CFG reachability is an
overapproximation. Execution, generation/end attribution, allocation, pickup,
and later benefit are omitted with unknown direction and remain outside hard
safety authority.

A native trace showing different request order/type/RNG consumption would
falsify the recurrence. A runtime PC outside the retained same-source
component after an exact generation/root join would falsify static ownership.
An ordinary allocation generation with untouched template fields but no
primary request on an eligible mode-0/1/2 HP defeat would falsify the default
candidate.

Both tools are offline and have no publication deadline. No issue-time
consumer reads their results. The unchanged Boolean policy plus fresh local
hard certificate remains the fallback.

## Authority And Next Gate

This checkpoint grants:

- shipped template/drop-handler semantic authority;
- an independently tested pre-item-manager request recurrence;
- shipped Route-2/Lunatic Final-B item/drop site inventory;
- literal operand and conservative program ownership authority; and
- a route-wide candidate index for causal Power/combat experiments.

It grants no:

- runtime instruction execution or concrete enemy generation/end reason;
- successful item allocation, item identity, pickup, or Power gain;
- survival-feasible collection or later damage/kill benefit;
- planner ranking, live action authority, or physical promotion.

The next gate must join:

```text
content digest
+ stage/gameplay epoch
+ enemy generation and root subroutine
+ main/aux VM PC and ordered HP-defeat event
+ live defeat mode and drop fields
+ item allocation identity and randomized position
+ pickup identity and Power threshold crossing
+ unchanged viable action certificate
+ later shot/HP/phase or prevented-birth consequence
```

Candidate selection should prefer immutable ordinary roots with configured
extra Power counts or dense source/emission value. A pure-survival branch and
the resource/combat branch must start from the same immutable root. Static
availability must never be reinterpreted as a pickup.

Focused model, atlas, opcode, and retained-regeneration tests pass. Complete
Linux discovery passes 1,484 tests in 14.807 seconds. Complete Windows UNC
discovery passes 1,484 tests in 30.415 seconds with the three existing skips.
No TH08, controller, replay, or physical trial was run.
