# Stage-5 Enemy Combat-Progress Offline Gate

Date: 2026-07-28
Status: accepted for default-off physical integration; not physically accepted

## Question And Authority

Can the first 64 ordinary-enemy records expose raw HP, current-update damage,
local damage flags, and defeat mode from the already-paid coherent pool blob
without changing sensing RPM, body geometry, or the live action path?

This checkpoint answers only the offline implementation and performance
question in
`STAGE5_ENEMY_COMBAT_PROGRESS_OBSERVATION_CONTRACT_20260728.md`.
It grants no generation identity, kill/end-reason, complete damageability,
targeting, future-hazard, planner, or action authority. The controller and
supervisor do not yet enable the observer, and no physical result is claimed.

## Implemented Boundary

- `th08_live.enemy_combat_progress` decodes the six revalidated raw fields
  from one existing contiguous pool blob.
- Active rows retain slot and capture-time pointer, signed current/maximum/
  phase-start HP, signed current-update damage, raw flags, the explicitly
  local damage-flags gate, and the three-bit defeat mode.
- The decoder performs no process-memory reads. The opt-in
  `capture_enemy_pool_prefix_contiguous(..., include_combat_progress=True)`
  uses the same `u32/read/u32` bracket and preserves ordinary body output.
- `EnemyCombatProgressStageRequest` provides a narrow post-issue,
  action-neutral trace boundary carrying route, difficulty, stage, epoch,
  decision, capture bracket, and attempt identity.
- Malformed pool geometry, truncated blobs, non-finite timing, and reversed
  clocks fail loudly.

The observation rows use an immutable `NamedTuple`. This retains named access
and a compact canonical list representation without the dense per-frame
allocation cost of 64 frozen dataclass instances.

## Correctness Evidence

**Observed in deterministic tests:**

- inactive and active filtering, signed negative HP/damage, all four local
  blocking cases, defeat modes, truncation, and timing failures behave as
  contracted;
- a dense 64-slot adversarial fixture matches an independent scalar oracle
  that reads every field separately and uses literal gate/defeat masks;
- slot 63 and every intermediate record boundary are exercised;
- enabling the inventory produces byte-for-byte equal body tuples and the
  exact same `u32/read/u32` reader call sequence as the disabled capture;
- the post-issue stage preserves capture identity, emits with timing
  measurement, does not force a flush, and has no action consumer.

Focused Ruff and eight focused tests pass.

The complete Linux quick suite passes 965 tests after the final oracle test.
The complete Windows discovery over the same test pattern exits zero. The
Windows interop process emitted no retained console summary on the final
invocation; its exit status, the focused Windows result, and the shared
discovery set are the retained evidence rather than an invented duration.

## Performance Failure And Repair

The first implementation used four `struct.unpack_from` calls per active
record. On the dense 64-slot Linux fixture its decode p95 was `0.138854 ms`,
above the fixed `0.10 ms` gate.

Packing all six fields into one precompiled `Struct` reduced p95 only to
`0.122955 ms`; the gate still failed. Profiling by representation then
localized the remaining cost to constructing 64 frozen dataclass objects.
Replacing only that representation with an immutable named tuple preserved
the canonical record SHA-256 while reducing repeated Linux decode p95 values
to `0.071152`, `0.065151`, and `0.059225 ms`. The performance contract was
not weakened.

The final retained 10,000-iteration dense results are:

| Platform | Phase | median ms | p95 ms | p99 ms | max ms |
| --- | --- | ---: | ---: | ---: | ---: |
| Linux Python 3.13.5 | decode | 0.048112 | 0.059839 | 0.079025 | 0.340649 |
| Linux Python 3.13.5 | record | 0.010631 | 0.012975 | 0.018512 | 0.097177 |
| Windows Python 3.12.10 | decode | 0.057000 | 0.078700 | 0.097900 | 0.207600 |
| Windows Python 3.12.10 | record | 0.012200 | 0.016900 | 0.021400 | 0.066900 |

Both reports pass p95 `<= 0.10 ms`, p99 `<= 0.20 ms`, and maximum
`<= 2.00 ms` independently for decode and record construction. Both produce
canonical record SHA-256
`f00ced83950978bffc354742bd01c04bba74ea1e301310efcdb97f9cf4b1bf23`.

Retained reports:

- `artifacts/benchmarks/enemy_combat_progress_linux_20260728.json`
  (file SHA-256
  `574dd967b8f92b11283c342a4f73721c1538b7b9ec4dd756ca64ab991fa68d39`);
- `artifacts/benchmarks/enemy_combat_progress_windows_20260728.json`
  (file SHA-256
  `75b2c56f7069dd0d113c4646464981b7ba0e58d8ccb26e91a16dfd831ead4e38`).

## Interpretation

**Observed:** the bounded decoder is cross-platform deterministic, stays
inside the fixed offline timing gate, and can reuse the existing capture
without added enemy-pool RPM.

**Inferred:** the original miss was a Python object-allocation problem, not a
need to reduce field coverage or weaken the deadline.

**Not established:** one stable snapshot does not identify an enemy
generation or distinguish kill, timeout, scripted despawn, transition
cleanup, and unknown. A lethal update may disappear before the next stable
capture. `local_damage_flags_open` is not complete physical damageability.

## Next Gate

Wire the option through CLI, hotkey supervisor, and controller as explicit
default-off trace-only telemetry. Retain a focused Stage-5 physical run and a
strict streaming audit that checks:

1. zero added enemy-pool RPM;
2. stable capture identity and bounded cadence;
3. exact row/schema validity and no non-finite timings;
4. observer p95/p99/max against the fixed gate;
5. hard no-Bomb, route/session acceptance, and exact cleanup.

Only after that physical gate may a separate generation/end tracker and
deterministic exposure audit begin. No target preference may enter live
guidance at this checkpoint.
