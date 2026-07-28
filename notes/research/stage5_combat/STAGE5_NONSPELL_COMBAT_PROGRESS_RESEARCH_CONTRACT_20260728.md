# Stage-5 Nonspell Combat-Progress Research Contract

Date: 2026-07-28

Status: **proposed trace-only research line**. No live target selection, item
collection, damage alignment, planner ranking, or action authority is enabled
by this note.

This contract records the user observation that recent failures appear
concentrated in opening and middle nonspell enemy waves, together with the
related need to preserve Power and finish boss health bars promptly. It
specializes the existing damage-aware hypothesis in
`notes/review/DELIVERY_AWARE_STRATEGY_REASSESSMENT_20260724.md`.

## Physical Objective

The primary objective remains full-route Sakuya/Remilia survival on Lunatic
and Extra with hard no-Bomb behavior.

Only inside the physically viable, issue-safe action set, the secondary
lexicographic objectives are:

1. reduce exposure time by killing damageable ordinary enemies or bosses
   sooner;
2. retain or recover Power without taking an unsafe collection detour;
3. preserve useful shot alignment and damage rate; and
4. distinguish kill completion from timeout, scripted despawn, invulnerability,
   or transition.

“Move toward enemies,” “move upward,” “collect Power,” and “finish the phase”
are not safety rules. They are candidate objectives whose authority is
strictly below survival feasibility.

## Retained Stage-5 Observation

Ten complete retained Lunatic Stage-5 runs from 2026-07-28 contain 128 hit
edges over 125,088 decisions:

| Phase | Hits | Decisions | Hits / 1,000 decisions |
| --- | ---: | ---: | ---: |
| nonspell | 60 | 82,588 | 0.727 |
| spell 103 | 18 | 9,373 | 1.920 |
| spell 107 | 21 | 9,090 | 2.310 |
| spell 111 | 12 | 11,713 | 1.025 |
| spell 115 | 17 | 12,324 | 1.379 |

The five newest compatible runs contain 34/59 nonspell hits over
41,893/62,734 decisions. Their nonspell rate is `0.812` hits per 1,000
decisions versus `1.199` for all spell decisions.

**Observed:** every one of the ten canonical fresh-attempt first hits
occurred with no active spell and Power `128`. Their first-hit frames were
`[2167, 4027, 1394, 2390, 12324, 1490, 1489, 4184, 2038, 2397]`.

**Observed in the newest run
`lunatic_route2_stage5_unattended_20260728_212622`:**

- six of nine hits were nonspell, and they were the first six hits;
- nonspell occupied 8,002 of 12,100 decisions and had six hits;
- the six nonspell hit observations contained 10 to 21 active enemy bodies;
- spells 103, 107, and 111 had one hit each; spell 115 had none;
- Power fell from 128 to 31 after nine respawn-contaminated contacts, with a
  minimum of 19.

**Inferred:** opening/middle nonspell survival is a canonical route barrier,
not merely a late low-Power artifact. Its large absolute hit count is partly
explained by its much longer exposure. The retained data do not show that a
nonspell decision is intrinsically more dangerous than a spell decision.

**Hypothesized:** faster ordinary-enemy removal may shorten exposure to future
emissions and thereby prevent some nonspell kernel exhaustion. Existing
traces do not record sufficient enemy HP, confirmed kill time, shot damage,
despawn cause, or alternate-action outcomes to establish that causal link.

## Current Code And Evidence Boundary

The controller already:

- senses Power and item objects;
- holds Shot almost continuously in retained route evidence;
- tracks stable boss health/timer progress and damageability;
- computes a boss horizontal-alignment action as a shadow-only,
  survival-filtered tie-break; and
- keeps `ITEM_OBJECTIVES_ENABLED = False`.

It does not yet establish ordinary-enemy HP/damage progress, shot-to-target
damage attribution, kill versus scripted despawn, item pickup ownership,
Power gained per route segment, or a causal reduction in emitted hazards.
Boss damage shadow output has no action authority.

Power after later hits is endogenous: a hit changes Power and the following
route. Therefore end-Power/hit correlation across these runs is not an
estimate of the benefit of collection or damage alignment. Later contacts
remain geometry and planner evidence, not independent clean-route survival
samples.

The retained Stage-5 practice workloads begin at Power 128. Normal full-route
acceptance instead begins at Power 0 and must retain collection, damage, and
route progress from that initial condition. Post-death Power recovery is
useful for loss-recovery diagnosis, but it is outside the clean pre-loss
history and cannot justify final no-miss authority.

## Formal State And Information Contract

A combat-progress state must extend, not replace, the exact survival root:

```text
(survival root,
 route/stage/phase/epoch,
 enemy generation and source identity,
 observed health and damageability belief,
 phase timer and completion mode,
 player shot/option state,
 Power and relevant item/pickup state)
```

Two histories with identical geometry but different enemy generation, HP,
damageability, pending spawn/emission path, Power, or item ownership are not
control-equivalent for a combat-progress objective. Hidden histories that
produce the same available observation must be merged before any controller
choice; target selection may not maximize hidden branches separately.

Actions retain complete-mask issue/no-write and pickup-delay semantics. Bomb
bit `0x02` remains forbidden. RNG, player-aimed emissions, cadence, pickup
delay, incomplete future ECL paths, damage timing, and unobserved kill/despawn
causes remain nature branches or `UNKNOWN`.

If solved exactly, a finite combat model answers only its declared enemy,
damage, drop, and future-event scope. It does not become a physical survival
proof unless its hazard coverage and issue-time certificate are independently
complete.

The live fallback remains the current Boolean policy plus the fresh local hard
certificate. Trace collection and shadow scoring must complete after current
issue or from an earlier immutable version; no cold analysis enters the issue
thread.

## Hypotheses And Falsifiers

### H1 — Ordinary-enemy exposure compression

Some damageable ordinary enemies have a kill-before-saturation deadline.
Killing one before that deadline removes later dense tracking or homing
emission opportunities and preserves a viable continuation.

Falsifiers include identical emission/exposure after verified earlier kill,
scripted emissions independent of owner life, no identifiable density/deadline
change, or first-hit windows that occur before any eligible damage choice
could change kill time.

### H2 — Boss phase compression

Spellcards remain survival-first. Among actions with identical hard survival
authority, better verified shot alignment and damage rate may reduce boss
phase duration; this is a subordinate phase-compression objective, not a
requirement to chase damage through a pattern.

Falsifiers include no HP-delta improvement, invulnerability dominating the
window, longer unsafe positioning recovery, or no survival-equivalent action
choice.

### H3 — Power recovery inside viability

Power pickups selected only within the already viable issue-safe set can
improve later damage without reducing survival margin. The primary workload is
the normal route beginning at Power 0. Post-death recovery is retained only as
a separate diagnostic.

Falsifiers include a changed hard certificate, reduced clearance/reserve,
increased exposure, no verified pickup, or no later damage improvement.

### H4 — Phase-specific strategy profiles

Nonspell waves may need target/kill-time optimization while spellcards need
primarily pattern survival and boss damage alignment. One universal scalar
weight is unlikely to represent both.

Falsifiers include equivalent target/damage dynamics across the measured
phases or no repeated benefit across RNG-distinct runs.

## Ordered Research Gates

### C0 — Read-only native combat telemetry

Revalidate shipped instructions and runtime fields before naming them. Capture
ordinary-enemy generation, health/threshold, damageability, source identity,
spawn/end reason, and item/drop/pickup transitions if the binary and probes
support them. Retain raw values and evidence when semantics are uncertain.

The first narrower inventory/update-order gate is fixed in
`notes/research/stage5_combat/STAGE5_ENEMY_COMBAT_PROGRESS_OBSERVATION_CONTRACT_20260728.md`. It explicitly
forbids treating slot disappearance as a verified kill.

Its offline implementation and unchanged performance gate are accepted in
`notes/research/stage5_combat/STAGE5_ENEMY_COMBAT_PROGRESS_OFFLINE_GATE_20260728.md`. This closes only the
first-64 raw inventory sub-gate.

Its physical integration passes in
`notes/research/stage5_combat/STAGE5_ENEMY_COMBAT_PROGRESS_STAGE5_RESULT_20260728.md`: all 11,735
observations have stable brackets, the fixed decode/record timing gates pass,
and the strict report regenerates byte-identically. Generation identity, end
reason, drops, pickups, and source attribution remain open.

No inherited IDA name, comment, type, or prior offset is authority.

### C1 — Deterministic exposure audit

Build a streaming audit keyed by route, stage, gameplay epoch, enemy
generation, and phase. Report:

- spawn-to-kill/despawn exposure frames;
- verified health delta and damage per frame;
- Shot/option uptime and horizontal damage alignment;
- emitted bullet births while the source remains alive;
- Power/item deltas with explicit pickup ambiguity;
- viable-set size, issue-safe alternatives, clearance, and reserve;
- first-hit position relative to target and emission events; and
- kill, timeout, scripted despawn, transition, and unknown completion
  separately.

Do not infer counterfactual safety or alternate damage from one executed
trajectory.

### C2 — Trace-only survival-filtered target shadow

Define a versioned Stage-5 nonspell profile. It may rank only actions already
proved viable and issue-safe by the unchanged authority path. Retain baseline
and shadow action, target identity, predicted kill/exposure change, exact hard
certificate rows, and every unavailable reason. It cannot alter live action.

### C3 — Focused physical gate

Only after telemetry parity and deterministic replay:

- target one opening nonspell segment first;
- require repeated RNG-distinct complete samples;
- compare fresh-attempt first-hit survival, exposure frames, verified kill
  time, Power, damage, viable-set health, cadence, and timing;
- reject any Bomb, hard-mask change outside the declared tie set, missed
  transition, stale target, or issue-path regression.

A one-run lower hit count cannot promote the profile.

### C4 — Boss and cross-stage generalization

Repeat the shadow and focused gate on one boss phase and a different stage
before considering a route profile. Lunatic and Extra promotion remain
separate acceptance claims.

## Architecture Boundary

Do not add combat telemetry and target lifecycle directly to the 2,700-line
`_run_live_session` body.

- game-neutral progress/belief and lexicographic selection belong under
  `scripts/touhou_control/`;
- TH08 enemy/HP/drop/option layouts belong in TH08 adapters;
- the action-neutral live observation/trace transaction should be a narrow
  independently tested stage;
- streaming comparison belongs under `scripts/analysis/`; and
- route/difficulty/stage/phase priorities belong in explicit versioned
  profiles.

This seam is also a candidate for the next R5 controller extraction after the
runtime-ECL checkpoint is committed.
