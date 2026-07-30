# Route-2 Ordinary-Enemy End-Semantics Contract

Date: 2026-07-31

Taskbook workstream: `WS-H`, shared by `COMBAT-FAST-01`,
`COMBAT-KILL-01`, and `POWER-ROUTE-01`

Status: native control edges revalidated and fail-closed offline lowering
implemented; ordered runtime event capture remains open

## Question

Which shipped native events begin and end one ordinary-enemy slot lifetime,
which end reasons can be stated from the control edge alone, and what extra
evidence is required before one end may be called a player-shot kill?

This is deliberately stage-neutral. It does not infer generation or end
reason from sampled endpoint active bits.

## Revalidated Native Semantics

The connected shipped IDA database establishes two first-inactive
480-slot allocators:

| allocator | native evidence | lifetime effect |
| --- | --- | --- |
| timeline allocator `0x0042A4E0` | scan `0x0042A515..0x0042A54E`; template copy; initial VM | allocate; immediate retire at `0x0042A5F5` only when the initial VM returns `-1` |
| inherited-register allocator `0x0042A680` | scan `0x0042A6B5..0x0042A6EE`; template and 0x78-byte VM-register copy | allocate; immediate retire at `0x0042A787` only when the initial VM returns `-1` |

**Observed shipped instructions:** later manager retirement has three
distinguishable control-edge classes:

- main VM return `-1` reaches active-bit clear `0x0042C9A2`;
- the out-of-bounds/cull edge at `0x0042CDED` reaches that same clear site but
  has a distinct causal predecessor; and
- HP `<= 0`, after its explicit deferral flags, dispatches defeat mode 0 and
  clears active bit 0 at `0x0042D899`.

The other shipped defeat modes do not clear the active bit at that dispatch
site and therefore are not ordinary slot retirement events there.

## Corrected Forced-Zero Boundary

CE-0219 corrects the inherited name
`enemy_manager_clear_active_with_score_items` at `0x0042EFB0`.

**Observed shipped instructions:** the function:

1. selects active, non-boss enemies not protected by the secondary flag;
2. writes current HP `+0x2DFC` to zero at `0x0042F039`;
3. optionally spawns type-6 scaled-score items;
4. unlinks the parent relation at `0x0042F1A3`; and
5. starts and clears a configured signed end-subroutine index.

It never clears primary active bit 0 in this function. Affected enemies
reach later manager HP/defeat processing in the same update or a later
update, depending on slot order.

The four observed callers distinguish the forced-zero cause:

- spell finish at `0x00416225`;
- ECL opcode `0x5F` at `0x0041DA89`;
- boss-defeat shared cleanup at `0x0042D93C`; and
- message/dialogue start at `0x00433D9F`.

Consequently opcode `0x5F` is now named
`zero_eligible_enemy_hp_with_score_items`. Its static event class is
`forced_enemy_hp_zero`, not `global_enemy_cleanup`. The corrected
mandatory-stage atlas has SHA-256
`6b2580ebffa7658ede7ca756fb3718f969b2c365fa43f32c24e83b2733f16139`
and internal pre-digest
`203693babf321706f96a26f5b024136f3f56c1e0dc9980b6930759d7600c78de`.

## Kill Authority

An observed mode-0 active clear proves an HP-defeat retirement. It does not
by itself prove that player damage crossed zero. A complete verified
player-shot kill requires one ordered same-manager-iteration record of:

```text
hp_before_damage > 0
resolved_player_shot_damage > 0
hp_after_damage = hp_before_damage - resolved_player_shot_damage
hp_after_damage <= 0
no earlier forced-zero event for this generation
defeat_mode = 0
active bit clear at 0x0042D899
```

The post-update `frame_damage` field alone is insufficient: it omits
pre-subtraction HP, the ordered forced-zero history, and hidden same-update
allocation/reuse.

## Offline Lowering

`scripts/th08_enemy_end_semantics.py` now:

- records forced HP zero as a non-retirement, non-kill effect;
- accepts only the five revalidated active-clear control edges as retirement
  sources;
- distinguishes initial/main-VM end, offscreen cull, forced-zero defeat,
  exact lethal player-shot damage, and unattributed HP defeat;
- promotes a player-shot kill only from exact subtraction arithmetic plus the
  mode-0 active clear; and
- lowers a verified retirement into the existing ordered
  `Route2SlotLifecycleEvent`, after which the lifetime ledger assigns the
  generation.

Contradictory arithmetic, unsupported sites, a missing active clear, wrong
defeat mode, or a forced-zero record that claims immediate retirement fails
closed.

Focused semantics, ECL-catalog, atlas, and generation-ledger tests pass.
Complete discovery passes 1,400 tests on Linux in 12.956 seconds and through
the exact Windows UNC loader in 27.9 seconds, with the three existing Windows
skips.

## Authority

- **Observed:** the named instruction/dataflow slices and caller set in the
  shipped IDA database.
- **Inferred:** none of the corrected active-bit or HP-write distinctions.
- **Hypothesized/open:** runtime completeness of a future hook/ring, event
  timing on a physical workload, and every kill/exposure benefit.
- No game, controller, or physical trial was run.
- The implementation has offline semantic-lowering authority only. It has no
  trace-generation, damage-policy, future-emission, planner, or action
  authority.

## Formal Authority Questions

1. **History equivalence:** a generation is identified only by ordered native
   allocations and retirements. Endpoint active bits cannot merge histories
   containing hidden reuse.
2. **Causality:** forced zero, damage subtraction, and retirement are ordered
   before classification. A later clear cannot retroactively turn scripted
   cleanup into player damage.
3. **Physical question:** exact lowering answers the reason supported by one
   supplied event batch. It does not prove that the batch is complete or that
   an earlier kill improves survival.
4. **Falsifier:** another ordinary allocator/active-clear site, a callee that
   clears active within `0x0042EFB0`, a non-first-inactive allocation, or a
   native ordered trace that the classifier cannot represent.
5. **Deadline/fallback:** no live consumer exists. Missing ordered evidence
   remains `hp_defeat_unattributed` or `UNKNOWN`; live survival policy is
   unchanged.

## Next Gate

Build one default-off, bounded, overflow-explicit native event ring that
records both allocators, all five active-clear edges, forced-zero caller
identity, and exact damage subtraction fields. First validate it in native
replay and synthetic ring tests. Only then request a named physical capture;
do not repeat the old active-only combat observer.
