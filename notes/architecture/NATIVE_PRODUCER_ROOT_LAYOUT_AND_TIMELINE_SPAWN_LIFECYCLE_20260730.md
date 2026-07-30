# Native Producer Root Layout And Timeline Spawn Lifecycle

Date: 2026-07-30 (Asia/Singapore)

Status: **allocation/initial-VM lifecycle connected offline; root inventory
partial; no future-body or live safety authority**

## Result

The stage-timeline producer now reaches the ordered generational lifetime
ledger. For every `TimelineSpawnRequest`, it repeats the shipped first-inactive
480-slot scan, emits an `allocate` event, calls an explicit initial-main-VM
executor once, and emits `retire` when that executor returns exactly `-1`.
Later timeline records in the same physical update can therefore reuse the
slot with the next generation.

This closes the allocation-order boundary only. The supplied initial-VM
executor is still an interface, not the complete shipped ECL VM. Child births,
later VM termination, offscreen retirement, defeat/phase cleanup, callbacks,
motion, flags, damage, resource coupling, and shared-RNG execution remain
open.

## Revalidated Native Layout

The connected IDA database and shipped dataflow establish:

| Root | Address/layout | Evidence | Coverage |
| --- | --- | --- | --- |
| enemy manager template | `0x0057D2F0`, `0x53D0` bytes | observed/revalidated at `0x0042A4F3..0x0042A55D` | complete template bytes |
| ordinary enemy pool | `0x005826C0`, 480 × `0x53D0` | observed/revalidated at `0x0042A515..0x0042A54E` and `0x0042C841..0x0042C86F` | complete fixed pool bytes |
| main ECL VM | enemy `+0x07F8` | observed/revalidated at `0x0042A5CE` and `0x0042C9A0` | fixed VM bytes are in the pool |
| auxiliary VM roots | four pointers at enemy `+0x3384` | previously revalidated at opcode `0x87` and the auxiliary scheduler | pointer roots only; `0x24B0` heap contexts are dynamic |
| timeline state table | `0x00F5A0C0`, 16 × 16-byte states; PC `+0x0C` | observed/revalidated at `0x0042C7C3..0x0042C82E` | fixed states only |
| timeline markers/suppression | `0x00F54E1C` four `s32` markers; `0x00F54E2C` suppression word | observed/revalidated in `stage_timeline_step` | fixed globals |
| indexed enemy registry | `0x00F54CC0`, eight pointers | observed/revalidated at timeline opcodes `0x08/0x0A` | pointer roots only |
| runtime ECL context | `0x004ECCB8`, two dwords | observed/revalidated in `ecl_load_file`/`ecl_start_subroutine` | pointer/table root only; relocated image bytes are dynamic |
| gameplay RNG | `0x0164D520`: `u16` state and call count at `+4` | observed/revalidated at `0x0043ECC0` and runtime sensing | complete fixed RNG root |
| input masks | raw/current/previous at `0x0164D528/0x0164D52C/0x0164D534` | previously revalidated from the player/input pipeline | fixed globals, not the whole player/shot state |
| player state | `0x017D5EF8` through predeath/lockout `+0xE2A6C` | revalidated consumers in the player update | fixed player bytes; external SHT/resource pointees remain |
| run-state resources | pointer cell `0x0160F510`; lives/Bombs/Power at pointee `+0x74/+0x80/+0x98` | runtime sensing and player/resource consumers | dynamic pointee not yet in the fixed root transaction |
| route/engine/stage | route `0x0164D0B1`, engine flags `0x0164D0B4`, stage route `0x0164D2CC` | runtime/menu/scene gates | multiple fixed regions |
| physical scheduler gates | FRScreen serial/pointer, scripted freeze, difficulty, enemy-manager frame | revalidated update order and CE-0120 boundary | multiple regions; manager frame is not a universal input clock |
| spell/time-scale transition | spell state `0x004EA670`; scale `0x017CE8E0` | revalidated spell/callback consumers | fixed roots; installed callback and auxiliary pointees remain |

`route2_revalidated_native_root_component_specs()` records these concrete
regions. A revalidated address with `complete_requirement_coverage=false`
does not satisfy its semantic root requirement. This prevents a pointer cell
from being mistaken for the bytes and identity of its pointee.

Current whole-requirement coverage is only:

- `ordinary_enemy_template_and_pool`;
- `motion_flag_and_lifecycle_state`; and
- `shared_gameplay_rng`.

The other seven minimum requirements remain explicitly missing from a
complete coherent producer root.

IDA comments were added at `0x0042C7F0`, `0x0042A5CE`, `0x00418473`, and
`0x0042C7C3`. They record the table root, main-VM initialization boundary,
runtime-image pointer boundary, and full producer-root dependency set.

## Native Allocation Recurrence

For each timeline spawn in ascending scheduler order:

```text
slot := first i in [0, 480) with active[i] == false
if no slot:
    publish pool_full; emit no lifecycle event; do not call initial VM
else:
    emit allocate(slot, next generation)
    copy template and apply spawn fields
    initialize main VM at enemy +0x07F8
    result := initial_enemy_ecl_vm_step_once()
    if result == -1:
        emit retire(slot, same generation)
```

The native pool-full function returns the end pointer and publishes an
exhaustion flag. The lifecycle model deliberately emits no false allocation.
The returned pointer's later opcode-`0x0B/0x0C` writes are not modeled and
remain an explicit exceptional native boundary.

`scripts/th08_simulator.py` now optionally owns a
`Route2SlotLifetimeLedger` and an `InitialEnemyVmExecutor`. Its
`stage_timeline_step` feeds every emitted spawn request into this recurrence
in the same event, so allocation/retirement is no longer a disconnected
postprocessor.

## Independent Differential

`scripts/analysis/th08_timeline_spawn_lifecycle_differential.py` compares the
product implementation to an independent list/dictionary oracle for:

1. ascending first-inactive allocation;
2. same-update allocate / initial-VM `-1` / reallocate;
3. post-root reuse advancing generation; and
4. a completely full 480-slot pool.

All four agree. The retained report is
`artifacts/runtime_reports/th08_timeline_spawn_lifecycle_differential_20260730.json`,
payload SHA-256
`d5db9e32cf029249b17f3e99cf8b7782856bbdb128acf52e5f7538f827c2ac17`.

## Formal Authority Check

1. **History equivalence:** two states merge only when the complete root,
   timeline clocks/PCs, shared RNG, ordered generational ledger, player/
   resource/input state, and every executed VM/callback state agree under the
   next observation. The current partial root does not meet that condition.
2. **Causality:** one spawn is selected before its initial-VM result is
   observed. Timeline order and same-update reuse are fixed by native order;
   no hidden branch is chosen after its result.
3. **Physical question:** exact execution of this slice answers allocation
   identity and immediate `-1` retirement only. It does not answer future
   body geometry or physical survival.
4. **Falsifier:** a non-first-inactive timeline allocation, a non-`-1`
   immediate retirement, a missing same-update reuse, product/oracle
   disagreement, or an unrecorded allocator invalidates the slice.
5. **Deadline/fallback:** no live controller consumes this executor. Missing
   root or event classes remain `UNKNOWN`; the current Boolean policy plus a
   fresh local hard certificate remains fallback.

## Next Native Slices

Proceed in native update order:

1. capture and execute the relocated runtime ECL image plus complete main VM;
2. lower child allocator opcodes `0x5A..0x5E` and all later active-bit clears;
3. connect auxiliary contexts, installed callbacks, conditional control flow,
   timers, and shared RNG;
4. execute internal motion, parent/world composition, clamp, mode flags, and
   final contact geometry;
5. execute player shots, HP/damage, Power/resources, defeat modes, and item
   effects; and
6. compare future body/flag schedules and safe-action masks against an
   independent scalar oracle before any predictive live promotion.

Offline/native replay remains a hypothesis-testing accelerator. It cannot
replace an original-game whole-stage physical survival gate.
