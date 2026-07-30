# Route-2 Boss Phase Configuration Atlas Contract

Date: 2026-07-31

Taskbook workstream: `WS-H`

Status: shipped-content/native-static checkpoint; runtime join required

## Question

Across the complete Sakuya/Remilia Lunatic Final-B route, which literal ECL
instructions configure Boss HP, the phase timer, HP-threshold successors, and
timeout successors, and how do those operands join the revalidated native
transition recurrence?

The physical objective remains NMNB survival. Damage or earlier phase
completion is secondary and may be considered only among actions already
proved viable and issue-safe. This atlas does not rank actions.

## Revalidated Native Configuration Writes

The following are **observed** in shipped `th08.exe` instructions and were
freshly revalidated against the connected IDA database:

- ECL opcode `0x83`, handler `0x0041C941`, evaluates argument 0 and writes the
  same integer to maximum HP `+0x2E00`, current HP `+0x2DFC`, and phase-start
  HP `+0x2E04`. The handler also has conditional side effects outside this
  atlas.
- ECL opcode `0x84`, handler `0x0041CB26`, evaluates argument 0 and calls
  `timer_set_elapsed` on the phase timer at `+0x2E14`. This corrects its opcode
  catalog confidence from **inferred** to **observed**.
- ECL opcode `0x85`, handler `0x0041CB70`, evaluates:
  - argument 0 as threshold slot;
  - argument 1 as HP threshold; and
  - argument 2 as successor subroutine.
- Opcode `0x85` always writes the threshold to `+0x3358[slot]`. It writes the
  successor to `+0x3368[slot]` only when:

  ```text
  (engine_flags & 0x4000) == 0
  or ((engine_flags >> 7) & 3) == 0
  ```

- ECL opcode `0x86`, handler `0x0041CCFC`, evaluates argument 0 as timeout
  frame and argument 1 as successor subroutine. It always writes the timeout
  at `+0x3378` and resets the phase timer at `+0x2E14`. Its successor write to
  `+0x337C` uses the same engine-mode gate.
- When bit `0x4000` is set and mode bits `7..8` are nonzero, opcodes `0x85`
  and `0x86` retain the prior successor register. A literal successor operand
  is therefore not unconditional runtime successor state.

Retained normal-route gameplay rows observe the full-configuration side of
this gate, but no retained row brackets one of these ECL writes. That
corroboration is not an instruction-execution join.

Four durable IDA comments retain the corrected handler semantics at
`0x0041C941`, `0x0041CB26`, `0x0041CB70`, and `0x0041CCFC`.

The manager-side recurrence remains the **observed** model documented by
`BOSS_PHASE_TRANSITION_MODEL_CONTRACT_20260731.md`:

- health slots scan in order `0..3`;
- health fires only for strict `current_hp < threshold`;
- multiple already-crossed slots may be consumed by the manager loop;
- health wins over timeout;
- timeout compares integer elapsed time with `>=`;
- timeout restores the greatest positive retained threshold; and
- transition checks precede later same-update player-shot HP subtraction.

## Static Content Method

The analyzer pins the immutable shipped-content manifest and parses:

- `ecldata1.ecl`;
- `ecldata2.ecl`;
- `ecldata3.ecl`;
- `ecldata4a.ecl`;
- `ecldata5.ecl`; and
- `ecldata7.ecl`.

Route ID 2, difficulty index 3, and difficulty mask `0x08` are fixed. The
conservative CFG folds those known selectors and retains other branch
alternatives. All six files have no unresolved dynamic subroutine edge for
this configuration.

The same-enemy Boss program closure traverses direct calls, interrupts,
auxiliary VMs, enemy-end exits, HP-phase exits, and timeout exits. It does not
merge child-spawn or `call_with_enemy` targets, which own different enemy
generations.

Every eligible `0x83..0x86` operand in the six files has parameter mask zero.
The literal operands are therefore exact shipped content. Static CFG
reachability and grouping are **inferred** conservative structure, not
runtime execution.

Transition edges in the report mean:

```text
this literal successor is installed if this instruction executes
on the full-configuration engine-mode branch
```

They do not mean that the instruction executes, that its prior register is
known, or that the successor starts in a retained run.

## Reproduction

Analyzer:

`scripts/analysis/th08_route2_boss_phase_configuration_atlas.py`

Command:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_route2_boss_phase_configuration_atlas.py \
  --decoded-dir artifacts/decoded \
  --content-manifest \
    artifacts/runtime_reports/th08_immutable_content_manifest_20260731.json \
  --output \
    artifacts/runtime_reports/th08_route2_boss_phase_configuration_atlas_20260731.json
```

Retained artifact SHA-256:

`95e872a31085b64e9660d9e488ffba16983a3cdb3d26e76a051a174e983bc837`

Internal pre-digest:

`6854c77f54d67869bcd74bd794f4eb86d9baf25c7303e1a1bb389e4c3dbf1ae7`

Size: 300,561 bytes. A second generation is byte-identical.

## Result

| Stage | Eligible sites | CFG-reachable | Unreachable | Phase subroutines | Literal transition edges | Boss roots |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Stage 1 | 19 | 19 | 0 | 9 | 11 | 3 |
| Stage 2 | 27 | 24 | 3 | 12 | 13 | 2 |
| Stage 3 | 34 | 28 | 6 | 14 | 17 | 3 |
| Stage 4A | 31 | 31 | 0 | 15 | 18 | 3 |
| Stage 5 | 28 | 28 | 0 | 14 | 17 | 4 |
| Final B | 50 | 50 | 0 | 24 | 27 | 7 |
| **Total** | **189** | **180** | **9** | **88** | **103** | **22** |

The 180 reachable sites contain:

- 40 HP assignments;
- 37 phase-timer assignments;
- 25 HP-threshold registrations; and
- 78 timeout registrations.

Seventeen phase subroutines have identical HP and timeout successor sets.
Fifty-three configure timeout only. Four have a partially shared literal
successor set:

| Stage/sub | Timeout site and target | HP sites and targets |
| --- | --- | --- |
| Stage 2 / sub 29 | `0x3D98`: frame 2280 -> sub 44 | `0x3DAC`: slot 1, HP 4100 -> sub 44; `0x3DC4`: slot 0, HP 2100 -> sub 51 |
| Stage 3 / sub 35 | `0x3D94`: frame 2220 -> sub 44 | `0x3DC0`: slot 0, HP 2000 -> sub 46; `0x3DD8`: slot 1, HP 3700 -> sub 44 |
| Stage 3 / sub 38 | `0x46B0`: frame 2280 -> sub 62 | `0x46C4`: slot 1, HP 4300 -> sub 62; `0x46DC`: slot 0, HP 2400 -> sub 66 |
| Stage 5 / sub 56 | `0x5780`: frame 3600 -> sub 63 | `0x5794`: slot 0, HP 6200 -> sub 63; `0x57AC`: slot 1, HP 3200 -> sub 74 |

These rows prove exact multi-boundary content under the full-configuration
write gate. They do not prove that damage chooses a different eventual route:
the native loop, retained thresholds, newly started ECL, and later registry
writes can make a target transient, sequential, overwritten, or unreachable.

The nine eligible but CFG-unreachable sites are retained explicitly: three in
Stage 2 and six in Stage 3. They are not silently counted as route execution.

## Formal Problem Contract

One static atlas state is:

```text
(content digest,
 route and difficulty,
 stage,
 timeline Boss root,
 conservative same-enemy component,
 ECL instruction identity,
 literal HP/timer/threshold/timeout operands,
 successor-write gate)
```

Two physical histories with the same row are not control-equivalent. They may
differ in enemy generation, engine mode, old successor registers, executed
branch, instruction pointer/call stack, current thresholds, HP, timer,
damageability, hazards, player resources, and action history.

There is no controller/nature recurrence in this static checkpoint. The
joined native transition prefix is causal and slot ordered, but the atlas does
not execute it over a runtime root. Unknown CFG branches are retained rather
than maximized as separately observable hidden choices.

If solved exactly, the finite static problem answers which literal
configuration writes can occur in the pinned route content and how the
manager would consume a fully observed registry. It does not answer which
writes occurred, the actual phase sequence, phase duration, delivered damage,
or survival benefit.

The analyzer exactly preserves pinned file identity, eligible literal
operands, decoded instruction identity, declared ownership edges, and the
native successor-write gate. CFG reachability is conservative. Missing old
register state under the suppressed-write branch and omitted ECL side effects
have unknown direction, so they remain outside hard safety authority.

A falsifier would be a shipped handler with a different argument order or
write target; a full-configuration runtime bracket whose register writes
disagree with the report; or an exact same-enemy execution PC outside the
declared closure. A runtime engine-mode sample alone is not enough: it must
bracket the instruction and pre/post registry.

The analyzer is offline and has no issue-time deadline. No live consumer reads
the atlas. The unchanged Boolean policy plus fresh local hard certificate
remains the fallback.

## Authority And Next Gate

This checkpoint grants:

- shipped Route-2/Lunatic Final-B content identity;
- observed native semantics for ECL `0x83..0x86`, including the mode gate;
- exact literal phase-configuration operands; and
- conservative full-configuration-mode Boss program/transition indexing.

It grants no:

- runtime ECL instruction execution or prior successor-register state;
- unconditional successor installation;
- actual Boss phase sequence or duration;
- causal action-to-HP delta;
- survival-equivalent damage benefit; or
- planner, target-ranking, Focus/Shot, route, or action authority.

The next causal gate must capture one immutable runtime root containing:

```text
content digest
+ stage/gameplay epoch
+ Boss pointer and generation
+ engine flags
+ main ECL VM instruction pointer/call stack
+ pre/post HP, timer, four thresholds, and five successors
+ player-shot damage and damageability gates
+ pending/confirmed transition cause
```

The read-only Boss snapshot now captures the four HP-successor registers and
timeout-successor register in its existing manager-frame consistency bracket,
adds them to phase identity, and reports the selected target in the bounded
transition prefix. This is capture readiness only: no compatible runtime
sample has been retained, engine-mode stability and ECL execution remain
unjoined, and the static atlas artifact is unchanged.

Only then may a pure-survival branch and a damage-oriented branch be compared
from the same viable root. Physical gameplay remains separately authorized.
