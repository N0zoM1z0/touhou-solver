# Live Physical-Issue Stage Refactor

Date: 2026-07-28

Status: behavior-preserving structural checkpoint with Linux/Windows tests
and one supervised Hard Stage-1 physical retention workload complete. No
model, recurrence, planner, action-selection, delay-support, Bomb, cadence,
trace-schema, or strategy authority changed.

## Boundary Extracted

`scripts/th08_live/issue_stage.py` now owns one typed physical issue
transaction after the final deadline/hit/auto-confirm overrides:

1. read player phase, predeath counter, and issue frame in the historical
   order;
2. construct `ActionIssueAlignment` from the source, capture, issue, and
   delay-support identity;
3. perform exactly one `IssueController.dispatch`;
4. construct the immutable `FreshIssueResult`;
5. register an issued command with the adaptive delay estimator only when
   the dispatch contains physical transitions; and
6. return the exact next desired mask and direction state to the controller.

The controller still owns:

- discontinuity detection and all epoch/session/resource reset behavior;
- hit counting/contact capture and stop-after-hit policy;
- deadline, deathbomb, hard no-Bomb, and auto-confirm overrides;
- candidate-verifier publication;
- post-issue research services;
- trace composition; and
- all stop/error key-release paths.

This is a behavior-owning seam, not a relocation of `_run_live_session`.

## Preserved Physical Semantics

- The three issue-time reads remain `u8(ADDR_PLAYER)`,
  `i32(ADDR_PLAYER + PLAYER_PREDEATH_COUNTER_OFFSET)`, then
  `u32(ADDR_ENEMY_MANAGER_FRAME)`.
- `ActionIssueAlignment` still rejects inconsistent frame order and retains
  the same deadline and contiguous-epoch predicates.
- Input transition construction, ordering, foreground policy, no-Bomb
  rejection, and `SendInput` remain owned by the unchanged
  `IssueController`.
- Selecting the complete mask already held remains no-write. It emits no
  transitions and does not call `AdaptiveControlDelay.issued`, so pending
  command support is not reset or resampled.
- A real transition registers the same source frame, issue frame, expected
  complete mask, support high, and complete delay support as before.
- Issue-path and observe-to-issue clocks are sampled after dispatch in the
  same order.
- The next desired mask is the issued complete mask; next direction is that
  mask intersected with the unchanged four-direction mask.
- Compatibility imports for `FreshIssueResult` and `ActionIssueAlignment`
  remain available from the controller facade.

## Automated Validation

New focused tests prove:

- exact issue-time address/read order and alignment identity;
- one dispatch per commit;
- write-path delay registration with exact arguments;
- no-write preservation of delay-estimator state;
- exact next mask/direction state; and
- immutable `FreshIssueResult` frame/mask consistency.

Focused Ruff passes. Complete discovery passes:

- Linux: 945 tests;
- Windows UNC: 945 tests with three existing platform skips.

## Physical Retention

Supervised run `hard_route2_stage1_unattended_20260728_203408` completed:

- frames `1..20950`;
- 7,755 decisions;
- one native hit at frame `2520`;
- hard no-Bomb;
- one successful automatic terminal confirmation;
- `route_complete`;
- accepted session/artifact gates;
- exact key release and identity-scoped process cleanup; and
- no residual game, controller, or supervisor process.

The action policy and model did not change. One hit versus earlier zero- and
one-hit Stage-1 structural workloads is RNG/workload evidence, not a causal
survival regression or improvement.

A streaming transaction audit over every decision reports:

- 7,755 self-consistent transaction rows;
- 3,018 physical writes;
- 4,737 no-write selections;
- zero target-mask, transition-count, write-required, or estimator-issued
  disagreement;
- zero Bomb rows; and
- zero deadline-suppressed row that still performed a write.

Decision cadence is p50/p95 `2/3` frames. The run retained the normal
write-heavy and no-write paths, a hit transition, dialogue confirmation,
terminal unload, and cleanup.

The replay-capable raw trace remains local and ignored:

- bytes: `166288334`;
- SHA-256:
  `1c8434c8a768e98492b81c4eb189df9efdfc71b7859c5916c03a75ff433844ac`.

Session SHA-256 is
`d97fdff9df305836f259260bf059f2f100df8c6629784528c274b25158db7fd4`;
summary SHA-256 is
`5cb064e70c1b8259eff96a5e33cccadd9a290cb2aa30a5571a3469eb84b8d1c2`.

## Next Structural Step

The dominant controller remains about 4,751 lines because later G5
instrumentation grew around the earlier 4,168-line audit baseline. The next
bounded extraction is the roughly 300-line post-issue bullet-birth
observation/build/publication stage. It has no action consumer, owns its own
previous-emit state and reset behavior, and already has independent observer,
contention, and record-builder modules. Extract it behind one request/result
contract before returning to runtime-ECL identity work.
