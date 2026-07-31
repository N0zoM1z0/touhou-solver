# TH08 Solver Goal

## Primary completion target

Build a solver and live controller that **physically completes a fresh,
full-game Touhou 8 Lunatic Route-2 run with Sakuya/Remilia as No Miss No Bomb
(NMNB)**.

The minimum achievement witness is one retained, reviewable run that:

- starts from the normal game-start state, including initial Power and
  resources;
- is a full route, not Stage Practice, replay playback, save-state, or a
  native snapshot/root continuation;
- progresses through the real shipped TH08 engine across Stages 1, 2, 3, 4A,
  5, and Final-B to route completion;
- records zero collision hits, zero life losses, and zero Bomb uses;
- uses only ordinary movement, Focus, Shot, and dialogue/menu inputs during
  gameplay;
- preserves enough native trace, replay, resource, stage/phase, input, and
  timing evidence to audit the NMNB claim.

Repeat clean full routes are the robustness acceptance gate: they establish
that the solver generalizes beyond one favorable RNG root. Extra is follow-on
scope after the Lunatic target closes; it is not a substitute for Lunatic
NMNB.

## What counts as progress

The primary research metric is a causal improvement to the general solver,
planner, model, or live delivery path that reduces physical full-route hit
risk. Stage 3, Stage 4A, Stage 5, Final-B, fixed-root wind-tunnel branches,
and focused physical trials are representative workloads used to iterate
quickly and test generalization.

A fixed-root no-hit witness, offline/model success, replay success, clean
practice stage, or lower hit count on a different RNG root is valuable
evidence, but none is the completion target by itself. A change is promoted
only through the evidence and physical-validation loop in `STRATEGY.md`.

Prefer general survival, combat, Focus, Power, planning, and delivery
improvements over spell- or stage-specific patches. After a major integrated
gain, pay a fresh full-route Lunatic run to measure whether the work moves
this goal.
