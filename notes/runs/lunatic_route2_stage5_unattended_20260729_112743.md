# Lunatic Route-2 Stage-5 Attempt `20260729_112743`

Date: 2026-07-29

Checkpoint: `5fae77a`

Status: contaminated infrastructure failure; excluded from survival and V4
delivery acceptance

## Observed Scope

- Exact executable identity and no-life-decrement patch passed.
- Supervisor enabled Caps Lock, selected Lunatic Sakuya/Remilia Stage 5, and
  armed the controller on PID 67520.
- The raw trace contains 1,169 decisions through summary frame 2,736.
- One nonspell hit was observed at frame 2,726 after global viability-kernel
  exhaustion.
- Before the spell-107 trace window, the foreground guard detected that the
  foreground PID was no longer TH08. The controller failed closed with
  `TH08 lost foreground; refusing to send or retain keys`.
- No auxiliary batch was emitted, so this run contains no V4 delivery
  evidence.
- The supervisor recorded `status=failed`, released input, terminated the
  exact game process, and left no game/controller process alive.

This run is not a `<=10`-hit pass. The single hit is ordinary early-nonspell
geometry evidence but cannot be used as a clean route score because the
attempt ended through external foreground contamination.

## Provenance

- raw trace bytes: 31,645,957;
- raw trace SHA-256:
  `94f3a68306f230a96341311f474c8d4f1e9f577aaa2e26653cfe32cd79c47114`;
- normalized session SHA-256:
  `9ea76db56ccf43fcc55c544a095b0c4fd449652b7075f8e82f7c06fd52662a5f`;
- raw summary:
  `last_frame=2736`, `counter_gaps=70`, `hit_count=1`,
  `termination_reason=agent_error`; and
- durable counterexample: CE-0171.

## Next Gate

Retry the unchanged checkpoint only after exact cleanup and foreground
preflight. Retain the next result independently. A completed V4 physical
report and two consecutive corrected Stage-5 runs at no more than ten hits
remain required.
