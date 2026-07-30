# TH08 Enemy, Damage, And Item Lifecycle Event-Ring Contract

Date: 2026-07-31
Status: implemented and synthetic-tested; default-off trace-only; no runtime,
planner, live-action, or physical authority

## Question

What is the smallest native observation boundary that can turn ordinary-enemy
slot reuse, end reason, forced-HP-zero ordering, resolved HP subtraction,
successful item allocation, and same-update item pickup into reviewable
evidence without repeating the rejected active-only observer or treating a
drop request as a pickup?

This is the first WS-H foundation needed before testing kill-before-saturation,
source-lifetime/emission causality, action-conditioned combat progress, or
route-wide resource benefit.

## Revalidated Native Boundaries

The following conclusions are **observed** in the shipped executable through
the connected IDA database, including instruction/dataflow review and exact
byte reads:

| Event | Address | Exact overwritten bytes | Enemy pointer |
|---|---:|---|---|
| timeline allocation after template copy | `0x0042A55F` | `8b55f8 8b45fc 89820c2e0000` | `[ebp-8]` |
| inherited-register allocation after template copy | `0x0042A6FF` | `8b55f8 8b45fc 89820c2e0000` | `[ebp-8]` |
| timeline initial-VM `-1` retirement | `0x0042A5F5` | `898124330000` | `ecx` |
| inherited initial-VM `-1` retirement | `0x0042A787` | `899024330000` | `eax` |
| manager main-VM `-1` retirement | `0x0042C9B1` | `899024330000` | `eax` |
| manager offscreen-cull retirement | `0x0042CDFE` | `899024330000` | `eax` |
| defeat-mode-0 retirement | `0x0042D899` | `898a24330000` | `edx` |
| eligible-enemy forced HP zero | `0x0042F039` | `c781fc2d000000000000` | `ecx` |
| enemy-damage begin | `0x0042D06D` | `8b4dc8 c7815433000000000000` | `[ebp-0x38]` |
| enemy-damage HP commit | `0x0042D343` | `2b45e8 8b4dc8 8981fc2d0000` | `[ebp-0x38]` |
| successful item allocation | `0x0044044D` | `8b4df8894df0` | `[ebp-8]` |
| non-pickup item cull | `0x00440991` | `8b4ddce8d70d0000` | `[ebp-0x24]` |
| pickup begin | `0x00440A39` | `668990da000000` | `[ebp-0x24]` |
| pickup commit | `0x00440C1E` | `8b4ddce84a0b0000` | `[ebp-0x24]` |

At both allocation hooks, signed word `[ebp+8]` is the exact root ECL
subroutine argument passed unchanged to `ecl_start_subroutine` later in the
same allocator. Native `g_stage_route_index` at `0x0164D2CC` selects the
loaded normal-stage ECL table (`0..8` for Stage 1 through Extra). The pair
`(stage_route_index, root_subroutine)` therefore identifies the concrete
allocation's loaded ECL program under the pinned normal-route content
boundary.

The five retirement sites clear active flag bit `0x01`. The forced-zero site
writes current HP `+0x2DFC = 0` and does **not** clear active. Its caller return
address distinguishes the four shipped call edges:

- spell finish: `0x0041622A`;
- ECL opcode `0x5F`: `0x0041DA8E`;
- boss-defeat cleanup: `0x0042D941`;
- message start: `0x00433DA4`.

The exact five-byte calls at the corresponding predecessor addresses were
also re-read from the IDB. Inherited names and earlier prose are not used as
authority for these boundaries.

The damage begin is after the current enemy is selected and immediately
before native `+0x3354` frame-damage reset. The commit is after shot
collision, flags, spell-card, Bomb, and Boss scaling have produced positive
resolved damage at `[ebp-0x18]`; it subtracts that value from pre-HP `eax`,
reloads the same current enemy, and writes current HP `+0x2DFC`. The hook
therefore observes the exact resolved subtraction, not a requested shot
damage or later retirement inference.

The called player routine at `0x00451670` iterates all 128 player-shot slots
at player `+0xBE838`, stride `0x484`. Its eligibility predicate is
`state != 0 && (state == 1 || type == 3)`. The transaction retains occupied
and eligible counts, both player timers at `+0xE2AC4` and `+0xE2AF4`, active
input, Focus/player/Bomb/route context, Power, target position/hitbox, main-VM
PC/timer, and gameplay RNG before/after the call. Enemy `+0x2D4C` is not used
as velocity; CE-0096 already rejects that inherited interpretation.

External comparison was demand-driven because this is a critical routine.
Pinned `th08-decomp` commit
`84738749bdcf6cffabe8d0d76e17f19253a20d50` agrees only on address/extent:
`EnemyManager::OnUpdate` is mapped at `0x0042C660` but remains an empty stub,
and `0x00451670` is only an unnamed mapping with no source implementation.
`thtk` and `eclmap` contain ECL/content-format logic, not this central runtime
damage path. They provide no competing field, order, or calling-convention
semantics. The shipped instructions/dataflow and exact hook bytes therefore
remain the sole semantic authority here.

At the successful item-allocation hook, effective type, motion, position,
velocity, callback RNG consumption, active-list append, and allocation-cursor
update are complete. Exact caller return `[ebp+4]` distinguishes all 58
shipped direct callers. At the five defeat-helper returns `0x0042BF0B`,
`0x0042BF86`, `0x0042C087`, `0x0042C09B`, and `0x0042C166`, the saved caller
frame exposes the exact source enemy at `[caller_ebp-0x14]`.

At pickup begin, collection collision has returned true but reward dispatch
has not executed. At pickup commit, type-specific resource effects are
complete and the same item is about to be unlinked. The cull edge unlinks
without a pickup reward. IDA comments at all four item hooks retain these
boundaries.

## Event ABI And Publication

`scripts/th08_runtime/enemy_lifecycle_probe.py` defines schema
`th08-enemy-item-damage-lifecycle-probe-v4`:

- one 32-byte identity/header record;
- fourteen fixed, position-specific x86 stubs;
- a power-of-two ring of 256 128-byte typed events;
- separate fixed scratch records pairing pickup and damage begin/commit;
- a `0x10000` remote image whose ring ends at `0xA400`;
- one unsigned 32-bit serial shared by the single native producer;
- explicit site-set CRC, PID, version, capacity, event size, and hook count.

Every event retains serial, `enemy_manager_frame`, kind, exact pool pointer,
stage-route index, caller boundary where applicable, a typed 22-word payload,
and explicit pre/post RNG fields. Allocation/retirement/forced-zero enemy
events retain:

1. decoder-validated ordinary-pool pointer/slot;
2. flags and HP before/after the overwritten instruction;
3. already-resolved frame damage at enemy `+0x3354`;
4. forced-zero caller return, or zero for other enemy kinds; and
5. signed allocation root subroutine, or `-1` for non-allocation events.

Damage events retain one same-frame, same-pointer begin/commit transaction:

1. flags/flags2, HP before/after, and exact positive resolved damage;
2. target world position, the native-selected primary/alternate damage
   hitbox, main-VM PC, and current VM timer;
3. Focus logic, player state, Bomb activity, alternate-hitbox nonzero
   magnitude, damage-region overlap, route id, native active input, and Power;
4. shot-emission and damage timers as
   `(previous, fraction_bits, current)`;
5. occupied and native-loop-eligible player-shot counts; and
6. gameplay RNG state/call count before and after damage computation.

Item-allocation events retain exact item pointer/slot, effective item
type/motion/full-value state, position/velocity, player position/state/Focus/
active input, Power/lives/Bombs, post-RNG state/calls, next allocation cursor,
active-list predecessor, and exact source enemy only for the five
defeat-helper callers. The hook is post-RNG, so pre-RNG is deliberately null.

Pickup begin copies pre-reward item/player/resource/RNG state into scratch.
Pickup commit publishes one transaction only when pointer and manager-frame
identity agree, adding post-resource/RNG state. Cull publishes the terminal
item state and requires unchanged resources and no RNG evidence. Damage
commit likewise requires its exact begin marker, enemy pointer, and manager
frame before selecting a ring slot. A mismatch replays shipped damage bytes
without publishing. Both paths invalidate the begin marker; success does so
before publication.

Every stub preserves flags and all general registers, replays the exact
overwritten behavior, and returns to the first untouched instruction.
Single-site events invalidate the selected ring slot, fill the event, then
publish slot serial before header serial. Paired pickup/damage begin hooks
write unpublished scratch. Their commit hooks copy a validated scratch
transaction into the selected ring slot and publish only after post-state is
complete.

CE-0224 corrects the first v3 selector encoding. IA-32
`imul r32, r/m32, imm8` sign-extends event-size byte `0x80` to `-128`; the
stub now uses `imul r32, r/m32, imm32` with exact positive stride 128. A
byte-level regression test decodes the signed immediate and rejects the old
sequence. No v3 probe was installed before the correction.

CE-0225 corrects the paired-hook activation boundary. Site-span quiescence
does not prove that a thread is not already between pickup or damage begin
and commit. Both v4 commit guards prevent stale scratch from consuming a
serial while preserving the exact HP write or item-unlink call on their
replay-only paths.

The implementation assumes one producer thread. This is **inferred** from the
covered enemy/item-management call topology and must be checked in the first
runtime trace. It is not a general multi-producer ring.

## Reader And Overflow Semantics

The reader double-samples the identity/header serial and validates the serial
stored in every selected slot. It reads one contiguous span, or two spans
across ring wrap, instead of one process-memory read per event. It returns:

- `baseline`;
- `no_events`;
- `exact`;
- `overflow_or_trace_truncation`, with an exact dropped count;
- `race_unknown`; or
- `read_error`.

Overflow, unstable slots, invalid pool pointers, unknown event kinds, a
nonzero caller on a non-forced event, or a forced-zero caller outside the four
shipped call edges cannot become partial positive evidence.
An enemy allocation without a nonnegative signed-word root, an enemy
non-allocation with a root, or a stage-route index outside `0..8` is also
rejected. Damage validation rejects incomplete RNG identity, begin/commit
pointer or frame disagreement, nonpositive or inconsistent HP arithmetic,
inactive slots, malformed player context, impossible shot counts, and
nonfinite target/resource values. Item validation additionally rejects
unknown direct callers,
non-defeat allocations with invented owners, missing defeat owners,
unsupported type/motion, broken pickup pointer/frame identity, cull resource
changes, and absent or malformed declared RNG boundaries.

For defeat-mode-0 retirement, the event exposes
`post_damage_hp + resolved_frame_damage`, but that arithmetic alone is not
player-kill authority. Ordered evidence for the same slot generation must
also exclude an earlier forced-zero event. The existing fail-closed
end-semantics classifier remains the authority boundary.

## Activation And Cleanup Safety

The probe remains outside default sensing. The live controller, hotkey
contract, stage-practice supervisor, and full-route supervisor now expose one
explicit `--trace-enemy-lifecycle-events` opt-in.

Installation:

- verifies all fourteen complete shipped instruction spans before allocation;
- writes the complete remote image before any code patch;
- suspends and snapshots every target thread;
- waits until no target instruction pointer lies inside any to-be-replaced
  instruction span;
- re-verifies all sites while suspended;
- activates direct `rel32` detours one at a time; and
- treats every attempted write as live until exact rollback is observed.

Failure rolls attempted sites back in reverse order. Any remaining detour or
unresumed thread raises an unsafe-state error requiring target termination
before gameplay.

Cleanup waits until no suspended instruction pointer lies in any patched span
or remote stub, restores every site in reverse order, verifies exact shipped
bytes, frees the remote image only after all detours are absent, and resumes
all target threads. A failed restore is unsafe and deliberately leaves the
remote image allocated.

This behavior is **implemented and synthetic-tested**, not yet observed
against a TH08 process.

Controller transport preserves the following fail-closed boundary:

- installation occurs only after shipped-target identity verification;
- priority-17 and lifecycle instrumentation are rejected in the same trial;
- one baseline batch is flushed only after route, difficulty, stage, raw
  input, and foreground arming checks pass;
- every diagnostic decision reads one batch before physical issue and embeds
  it in the flushed decision row;
- the consumed serial advances only after that row flushes successfully;
- after key release, a final batch is flushed before detour cleanup; and
- an unsafe activation or cleanup result terminates the exact verified TH08
  image rather than leaving an instrumented process available for gameplay.

An unavailable ordinary installation is retained explicitly and grants no
generation or end-reason authority. The trace option forces per-decision
rows, but the ring is not an observation used by the planner or issue path.

## Formal Authority Questions

1. **Which physical histories map to one state?**
   The ring does not merge histories. It records ordered allocation,
   forced-zero, damage, retirement, successful item allocation, cull, and
   pickup edges. A downstream generation ledger may merge only after applying
   every exact event in serial order. Any overflow or unstable read is
   `UNKNOWN`.

2. **Are all uncertainty branches present and nonclairvoyant?**
   This is an observer, not a control recurrence. It exposes no future
   information and grants no action choice. Missed events are explicit rather
   than imputed.

3. **Does an exact result answer the physical question?**
   An exact batch answers which covered native lifecycle edges executed, in
   order, for covered ordinary-pool records. Allocation events additionally
   answer the loaded stage/root program identity. Damage events answer exact
   positive native HP subtraction and captured player/target context. Item
   events answer covered successful pool allocation and same-update
   pickup/resource commit; the five defeat-helper callers also answer exact
   source-enemy identity. It does not expose failed allocation attempts or by
   itself prove action causation, survival-feasible collection,
   future-emission suppression, target-motion history, or later benefit.

4. **What falsifies the claim?**
   A covered lifecycle transition without an event; an event from an
   uncovered thread/caller; a register/flag mismatch after replayed bytes;
   a slot pointer outside its pool; damage marker/pointer/frame/HP/RNG
   disagreement; pickup pointer/frame/resource/RNG disagreement; source-owner
   disagreement; multi-producer serial corruption; or disagreement between
   ordered ring events and a bracketed full-pool snapshot.

5. **Can it be consumed before issue time?**
   No issue-time consumer exists. The ring is trace-only and must remain
   outside live action authority. Any later consumer needs exact-version
   matching, bounded read cost, overflow fail-closed behavior, and a separate
   delivery gate.

## Tests And Current Authority

The focused probe suite now covers 21 tests:

- all IDA-revalidated addresses and byte spans;
- enemy and item stub replay/return layout and fixed-slot bounds;
- direct activation targets and full-instruction padding;
- cleanup quiescence over every patch and stub;
- event and forced-caller validation;
- exact allocation root/stage identity and invalid-identity rejection;
- exact shipped item-allocation caller and defeat-source validation;
- paired pickup resource/RNG/pointer/frame validation;
- paired damage pointer/frame/HP/RNG/context/shot-count validation;
- exact damage hook bytes, native shot-loop predicate, alternate-hitbox
  `-0.0` handling, guarded replay-only commit, and marker invalidation;
- cull-without-resource-change validation;
- exact, overflow, and unstable reads;
- one- or two-span bulk ring reads across wrap;
- positive imm32 event-stride selection at the 128-byte sign boundary;
- activation-last install plus reverse-order cleanup;
- activation quiescence before replacing any in-flight instruction span;
- full rollback after a synthetic mid-activation failure; and
- unsafe retention after a synthetic restore failure.

Additional controller/automation tests cover default-off CLI behavior,
separate-probe rejection, supervisor and hotkey forwarding, and verified
target termination on unsafe instrumentation state.

No game, native replay, runtime installation, or physical trial was run. The
ring and its transport currently have implementation/synthetic-test authority
only. Complete discovery passes 1,500 tests in 13.953 seconds on Linux and
31.615 seconds through the Windows UNC loader, with the three existing skips.

## Next Gate

Before any strategy claim:

1. on explicit runtime authorization, bracket one short native replay or
   diagnostic workload with full-pool snapshots;
2. prove exact ordered agreement for enemy allocation/damage/retirement/
   forced zero and item allocation/cull/pickup/resource/RNG edges;
3. run the fail-closed lifecycle lowerer with `--require-complete` and compare
   its enemy/item generation output to that independent bracket; and
4. join exact stage/root generations to the immutable combat/resource
   candidate board; then
5. compare only unchanged-survival-feasible same-root branches to test
   whether a verified kill prevents emissions, creates/collects the declared
   Power opportunity, or shortens exposure.

The exact route-resource boundary is
`../route_resources/ROUTE2_ITEM_ALLOCATION_PICKUP_TRACE_CONTRACT_20260731.md`.
