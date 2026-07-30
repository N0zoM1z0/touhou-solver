# Boss Phase Transition Model Contract

Date: 2026-07-31

Taskbook workstream: `WS-H`

Status: native-semantic/offline checkpoint; no live action authority

## Question

What exact HP-threshold and timeout state does the shipped enemy manager use
to end a Boss phase, and can read-only telemetry distinguish “the boundary
condition became true” from “the transition subroutine has already started”?

The physical objective remains NMNB survival. Earlier Boss phase completion is
only a secondary objective among actions with identical hard viability and
issue safety.

## Revalidated Native Order

The following are **observed** in shipped instructions and relevant
callers/dataflow:

- `enemy_manager_update` starts at `0x0042C660`.
- After the enemy ECL VM and motion update, the manager enters a short-circuit
  loop at `0x0042CE31`:

  ```text
  while (apply_health_transition()
         || (timeout >= 0 && apply_timeout_transition())) {
  }
  ```

- Player-shot collision, scaling, and the HP subtraction at `0x0042D349`
  occur later in the same enemy update.
- `enemy_apply_health_phase_transition` (`0x0042B490`) scans threshold slots
  `0..3`. A slot fires only when its signed threshold is nonnegative and
  `current_hp < threshold`; equality does not fire.
- A health transition sets current HP and phase-start HP to that threshold,
  clears the selected slot, disables the timeout, starts the associated ECL
  subroutine, and returns one. The manager loop can then consume another
  already-crossed slot.
- `enemy_apply_timeout_phase_transition` (`0x0042B930`) compares the timer's
  integer elapsed field with timeout using `>=`. The fractional timer field
  does not independently trigger the transition.
- A timeout fires only if no health transition fired first. It restores
  current/phase-start HP to the greatest strictly positive retained threshold,
  clears that slot, starts the timeout subroutine, disables the timeout, and
  resets the phase timer to integer/fraction `(0, 0.0)`.
- Equal maximum thresholds retain the first slot because the native selection
  predicate is strict `best < candidate`.

Five durable IDA comments were added at `0x0042CE31`, `0x0042B50B`,
`0x0042B99C`, `0x0042BA15`, and `0x0042D349`.

## Corrected Observation Semantics

The manager ordering creates a normal one-update boundary state:

1. the pre-damage transition loop sees HP above a retained threshold;
2. player-shot damage subtracts enough HP to fall below that threshold; and
3. the update returns with the threshold still retained.

The threshold transition occurs only on the next **eligible** enemy update.
Bomb/player-transition pauses, `flags2` update blocking, and broader manager
freeze semantics can delay it. A stable capture in this state is not a new
phase.

The old `th08_boss_phase.py` decoder filtered active thresholds to
`threshold <= current_hp`. For current HP 490 and retained thresholds
`(500, 100, -1, -1)`, it therefore reported phase end 100. The native current
phase still ends at 500 and has a pending health transition. CE-0221 retains
this falsifier.

The corrected adapter:

- retains every nonnegative threshold;
- reports the first slot-order crossed threshold while a health transition is
  pending, otherwise the greatest retained threshold;
- permits signed negative post-damage HP telemetry instead of dropping the
  sample as malformed;
- projects the native slot-order/health-before-timeout loop;
- exposes `completion_pending` as `health`, `timeout`, or null;
- captures the four HP-successor registers and timeout-successor register in
  the same manager-frame bracket;
- reports the selected successor on each projected transition step;
- includes the complete threshold/successor registry in phase identity; and
- attributes a later observed phase-key change to health or timeout only when
  the preceding stable sample carried that pending condition and both samples
  share gameplay epoch, stage, and Boss pointer continuity.

An unbracketed disappearance or a phase change without a preceding pending
sample remains unknown. The tracker does not invent an exit cause across
missing observations.

## Executable Boundary

`project_boss_phase_transition_prefix()` implements only the known immediate
field mutations:

- current HP;
- phase-start HP;
- four threshold slots;
- integer/fractional phase timer; and
- timeout frame.

The projection now identifies the captured successor register selected by
each health or timeout step. It does not execute that subroutine or model the
timeout helper's later successor-register rewrite. Starting the selected ECL
subroutine can change flags, health, callbacks, emissions, movement, spell
state, registry fields, or later control flow. Those effects are explicitly
outside this projection. The returned state is not a complete phase or hazard
successor.

The read-only sensing trace now records:

- pending completion kind;
- confirmed completion cause when bracketed;
- four HP successors and one timeout successor;
- the successor selected by a pending projected boundary;
- health remaining and normalized health progress; and
- remaining timeout time.

This is telemetry only. No live objective, candidate ordering, movement,
Focus/Shot decision, publication service, or fallback changed.

## Formal Problem Contract

For this bounded recurrence, one model state is:

```text
(current_hp,
 phase_start_hp,
 threshold_slots[4],
 health_successor_slots[4],
 timer_integer,
 timer_fraction,
 timeout_frame,
 timeout_successor)
```

Two captured histories map to the same state only for the immediate native
boundary-field projection. They are not control-equivalent for physical
survival: enemy generation, ECL VM state, transition subroutine, flags,
spell ownership, hazards, player state, and update eligibility remain
separate observations or unknowns.

The recurrence contains no controller choice. Nature includes whether another
eligible update occurs before the next observation and all effects of the
started ECL subroutine. The scalar prefix does not maximize hidden branches
separately.

If solved exactly, this finite model answers which retained boundary fires,
which captured successor it selects, and the known immediate writes before
player-shot damage. It does not answer whether the selected subroutine runs
to completion, whether a Boss is damageable, how much damage an action
delivers, how long a new phase lasts, or whether shortening it improves
physical survival.

The implementation is exact for the revalidated comparisons, priority,
slot-order scan, threshold restoration, and timer reset. A shipped trace in
which:

- equality fires a health transition;
- fractional time alone fires timeout;
- timeout wins over an already-crossed health threshold; or
- timeout restores a nonmaximum positive threshold

would falsify the model.

The remaining approximation is omission of ECL/subsystem side effects. Its
direction is unknown, so projected post-transition states remain outside hard
safety authority.

The trace fields are computed from the already captured immutable observation
and are not an issue-time expansion. Any miss or unstable capture continues
to use the unchanged Boolean policy and fresh local hard certificate.

## Authority And Next Gate

This checkpoint grants:

- observed shipped ordering and field semantics;
- deterministic implementation of the bounded transition prefix;
- stable read-only capture of all five successor registers and exact selected
  target attribution;
- correct pending-boundary telemetry; and
- bracketed health-versus-timeout cause attribution.

It grants no:

- causal action-to-HP-delta or phase-duration result;
- survival-equivalent damage ranking;
- Boss attack-alignment or Focus-switch authority;
- ECL successor execution or side effects; or
- physical predictive authority.

Nine focused Boss tests and Ruff pass. Complete discovery passes 1,471 tests
in 14.568 seconds on Linux and 30.340 seconds through the Windows UNC loader,
with the three existing skips. No TH08, controller, replay, or physical trial
was run.

The next causal S10/WS-H gate needs one immutable root with stable Boss
generation/phase identity, exact engine mode, ECL PC/call state, pre/post HP,
frame damage, timer, thresholds and successors, shot timer/pool/options/RNG,
target geometry, and unchanged viable actions. The capture implementation is
ready, but no compatible runtime successor sample has been retained. Focused,
unfocused, and dynamic schedules may be compared only inside the same exact
survival-safe action set. Until that root exists, this model is read-only
infrastructure.
