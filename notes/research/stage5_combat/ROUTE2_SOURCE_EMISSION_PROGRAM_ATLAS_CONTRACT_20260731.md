# Route-2 Source/Emission Program Atlas Contract

Date: 2026-07-31

Taskbook card: `COMBAT-KILL-01`

Status: shipped-content/static candidate checkpoint; runtime join required

## Question

Across the full Sakuya/Remilia Lunatic Final-B route, which timeline-spawned
enemy programs contain later source-owned bullet/laser sites, staged-periodic
fire, or child-emitter births that could be removed by an earlier verified
source kill?

The physical objective remains NMNB survival. This atlas identifies candidate
source programs only. It does not assert that any instruction executes, that
an enemy is damageable, that a disappearance is a kill, or that killing a
source improves survival.

## Native Lifetime Boundary

The following are **observed** in shipped instructions and revalidated
callers/dataflow:

- `enemy_manager_update` skips the main enemy update when active bit `0x01`
  is clear (`0x0042C88D`).
- For an active source, the main ECL VM steps at `0x0042C9A0`, before
  player-shot collision and HP subtraction later in the update.
- Direct ECL fire opcodes `0x60..0x68` either emit or stage the shared
  descriptor according to native deferred-fire state. Opcode `0x6D` emits the
  current descriptor; `0x72/0x73` create lasers.
- The fixed staged-periodic path at `0x00423159..0x004231BD` requires current
  HP greater than zero and a positive period, advances its integer timer,
  emits the retained 44-byte descriptor when due, and resets the timer.
- This ECL/periodic work happens before later player-shot HP subtraction. A
  kill in one update cannot undo births or child spawns already produced by
  that update.
- Ordinary defeat mode 0 clears the source active bit at `0x0042D899` but does
  not globally cancel bullets or lasers. Existing projectiles persist unless
  a distinct cancel/cleanup path acts.

Four durable IDA comments retain these boundaries at `0x0042C88D`,
`0x0042C9A0`, `0x00423159`, and `0x0042D899`.

## Static Source Ownership

The analyzer starts from every difficulty-eligible timeline spawn in:

- Stage 1;
- Stage 2;
- Stage 3;
- Stage 4A / Reimu;
- Stage 5; and
- Final B / Kaguya.

All inputs are pinned by the immutable shipped-content manifest. Route ID 2,
difficulty index 3, and difficulty mask `0x08` are folded. Other conditional
branches remain conservative.

For one timeline root, the same-source component traverses only:

- direct ECL calls;
- installed interrupt subroutines; and
- auxiliary VMs belonging to the same enemy object.

It does **not** merge:

- child-spawn targets, which become independent enemy generations;
- `call_with_enemy` targets, whose ownership is a different indexed enemy; or
- enemy-end, HP-phase, or timeout-phase exits.

For a child-spawn site, the report separately records whether the target child
program contains direct/periodic emission candidates. Killing the parent can
prevent that child only before the child-spawn instruction executes. Killing
the parent afterward does not retire the already-created child.

Absence of a reachable Boss-control opcode makes a program
`ordinary_compatible`; it is not runtime proof that one concrete generation
is ordinary. Every such classification still requires a generation/flags
join.

## Reproduction

Analyzer:

`scripts/analysis/th08_source_emission_program_atlas.py`

Command:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_source_emission_program_atlas.py \
  --decoded-dir artifacts/decoded \
  --content-manifest \
    artifacts/runtime_reports/th08_immutable_content_manifest_20260731.json \
  --output \
    artifacts/runtime_reports/th08_source_emission_program_atlas_20260731.json
```

Retained artifact SHA-256:

`6ae9494a40ff5a08143564c653b3c2007e1125063a16b1108854db84f74531b5`

Internal pre-digest:

`33ef575bc8bafec1b557d6341357199bd227762d742856f257f0c20a25db4b48`

Size: 1,039,866 bytes. A second generation is byte-identical.

## Result

The six stage files contain 991 eligible timeline spawn instances and 70
unique root source programs. Conservative control flow has no unresolved
dynamic subroutine edge for this route/difficulty configuration.

| Stage | Spawns | Unique programs | Boss-possible | Ordinary emitter candidates | Candidate spawns | Candidate direct sites | Candidate child-emitter sites | Candidate periodic controls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Stage 1 | 177 | 10 | 3 | 6 | 173 | 9 | 8 | 12 |
| Stage 2 | 295 | 12 | 2 | 9 | 292 | 22 | 4 | 24 |
| Stage 3 | 121 | 14 | 3 | 9 | 81 | 16 | 4 | 3 |
| Stage 4A | 247 | 10 | 3 | 5 | 241 | 11 | 8 | 0 |
| Stage 5 | 130 | 15 | 4 | 8 | 108 | 6 | 60 | 0 |
| Final B | 21 | 9 | 7 | 2 | 14 | 1 | 4 | 0 |
| **Total** | **991** | **70** | **22** | **39** | **909** | **65** | **88** | **39** |

The high candidate-spawn count is not a kill policy. Many instances reuse a
small number of ECL roots, and static reachability deliberately keeps
unresolved runtime branches.

The atlas exposes different experiment families rather than one blanket
weight:

- direct-fire-heavy programs, such as Stage-3 root subroutine 0, with seven
  direct sites and six positive local VM timer guards;
- deferred/periodic programs, such as Stage-2 roots 13 and 14, which require
  exact staged descriptor, period, and timer capture; and
- child-emitter programs, especially Stage-5 roots 2, 9, 15, and 22, where a
  parent/child generation bracket is mandatory.

These examples are static triage labels, not promotion candidates. A local VM
timer guard is not elapsed source age or a manager-frame kill deadline.

## Formal Problem Contract

One static index state is:

```text
(content digest,
 stage,
 timeline spawn site,
 root subroutine,
 conservative same-source component,
 direct/periodic/child emission sites)
```

Two physical histories with the same index row are not control-equivalent.
They can differ in enemy generation, instruction pointer, VM timer/call stack,
auxiliary contexts, deferred descriptor, periodic timer, callback state,
damageability, HP, target geometry, RNG, child existence, and active
projectiles.

There is no controller/nature recurrence in this checkpoint. The CFG retains
unknown conditional successors and does not maximize hidden branches
separately. Runtime state and player/nature choices are deliberately absent.

If solved exactly, the finite static problem answers only whether a pinned ECL
program contains a conservative source-owned site. It does not answer whether
the site will execute, produce a birth, remain after a kill, or be avoidable
by one survival-feasible action.

The algorithm exactly preserves pinned file identity, route/difficulty
eligibility, decoded instruction/edge identity, and the declared ownership
partition. Conservative CFG reachability is an overapproximation. Runtime
execution, absolute deadlines, and prevented-birth counts are unknown
direction and remain outside hard authority.

A counterexample to the ownership partition would be a shipped instruction
showing that direct calls/auxiliary/interrupt VMs execute on a different enemy
generation, or that a child/cross-enemy target is retired automatically with
the parent contrary to the native pool/link semantics. A runtime PC outside
the retained component after an exact same-source join would falsify its
static coverage.

The analyzer is offline and has no publication deadline. No issue-time
consumer reads it. The unchanged Boolean policy plus fresh local hard
certificate remains the fallback.

## Authority And Next Gate

This checkpoint grants:

- shipped Route-2/Lunatic Final-B content identity;
- conservative same-source ECL component membership;
- symbolic direct/periodic/child emission candidate sites; and
- a route-wide candidate family index for selecting causal roots.

It grants no:

- runtime instruction execution or source/birth ownership;
- enemy generation, damageability, kill, or end-reason evidence;
- absolute kill deadline or prevented-birth count;
- exposure reduction, survival benefit, target ranking, or action authority.

The next gate must join:

```text
content digest
+ stage/gameplay epoch
+ enemy generation
+ main/aux VM instruction pointer and timer
+ staged descriptor/periodic timer
+ ordered lifecycle event
+ bullet/laser births and persistence
```

to exact pre/post HP, frame damage, damageability, and the unchanged viable
action certificate. A pure-survival and damage-maximizing branch may be
compared only from the same immutable root. The old active-only Stage-5 trace
cannot satisfy this join and must not be reused as kill evidence.

Three focused tests and Ruff pass. Complete discovery passes 1,447 tests in
15.217 seconds on Linux and 29.408 seconds through the Windows UNC loader,
with the three existing skips. No TH08, controller, replay, or physical trial
was run.
