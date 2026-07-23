# Lunatic Route-2 Transition-Guard Partial Runs

Date: 2026-07-23

These traces are retained as diagnostic partial runs. They are not complete-run
acceptance evidence and must not be combined into a route score: the first
controller exited at a Stage-1 resource unload, and the second was stopped
deliberately so the corrected scene guard could be loaded.

## Stage-1 Partial

- Raw trace:
  `artifacts/runtime_reports/lunatic_route2_hotkey_longrun_20260723_150027.jsonl`
- Tracked compact report:
  `artifacts/runtime_reports/lunatic_route2_hotkey_longrun_20260723_150027.summary.json`
- Summary SHA-256:
  `c8a6d171a8a13872a673984f435f50faf4663d6b234e19e5fd1bd540a20b28fb`
- Controlled frames: `1..20587`
- Decisions: `5,975`
- Native hit edges: `2367`, `5013`, `11909`, `13930`
- Termination: `gameplay_ended` (incorrect)

At Stage 1 completion, `g_engine_flags & 0x04` cleared during the normal stage
resource transition. The frozen-counter branch treated one inactive sample as
the end of the whole route. Its exit handler then observed Stage 2 active and
pressed Escape, making the failure look like an auto-confirm stall in Stage 2.

This run also falsified lane-only corridor commitment. Immediately before the
first hit, the retained bottleneck was still labelled `center`: frame 2358
targeted approximately x=264 with gate slack `+2.1269`, but frame 2361 selected
approximately x=88 with slack `-12.2599`. A three-bucket lane name does not
identify a connected component or path branch within that lane.

## Stage-2 Reload Partial

- Raw trace:
  `artifacts/runtime_reports/lunatic_route2_hotkey_longrun_20260723_150659.jsonl`
- Tracked compact report:
  `artifacts/runtime_reports/lunatic_route2_hotkey_longrun_20260723_150659.summary.json`
- Summary SHA-256:
  `191ba8504e75923f0ba95fddb59ca0ddcf395d69fc29ba4eb3f71449bf72a1a0`
- Controlled frames: `21280..41315`
- Native hit edges: `26201`, `31866`, `34154`
- Termination: `external_stop`

This controller was still the old in-memory module. It was stopped through its
sentinel at the Stage-2 tail, allowed to release every injected key and pause,
and only then was its daemon replaced. It must not be used to validate the
scene-transition correction.

## Corrected Acceptance Run

The first clean trace
`artifacts/runtime_reports/lunatic_route2_hotkey_longrun_20260723_151557.jsonl`
started from manager frame 1 under the first scene-guard revision. It survived
the Stage-1 unload and resumed Stage 2, proving that the original immediate
exit was fixed, but exposed one more ordering fact:

- Controlled frames: `1..23664`
- Decisions: `7,054`
- Native hit edges: `5823`, `19772`
- Termination: deliberate `external_stop`
- Tracked summary SHA-256:
  `a6a46ed37700e89991f6112dd154b29340342b6bfd1085b6e5eb37fc59edda9c`
- Boundary events: inactive at frame `20827` for 0.272 seconds, then resumed
  Stage 2 without terminating.

TH08 wrote stage index 1 while the gameplay bit was still active. The guard
therefore mislabelled the source as Stage 2 and expected Stage 3, even though
the actual resume was Stage 2. If left unfixed, the same early index write at
Stage 5 would label the source Final B and terminate during its transition.
The trace was stopped early and is a third partial, not an acceptance run.

The next clean run uses stable stage identity: the identity is committed only
at initial arm or after an inactive interval resumes. Acceptance requires all
of the following:

1. Each non-final boundary emits `scene_inactive`, zero or more
   `auto_confirm_transition_pulse` records, and `scene_resumed`.
2. The resumed stage matches route-2 progression `0,1,2,3,5,7`.
3. The agent never exits merely because `g_engine_flags & 0x04` is transiently
   clear.
4. Final-B unload remains inactive for five wall-clock seconds and terminates
   as `route_complete`.
5. The completed raw trace receives the same dossier, per-hit CSV, executable
   regression corpus, and review Markdown treatment as the first full run.

## Residual-Item Auto-Confirm Partial

The stable-identity trace
`artifacts/runtime_reports/lunatic_route2_hotkey_longrun_20260723_152539.jsonl`
proved the corrected Stage-1 boundary:

- Controlled frames: `2..28459`
- Decisions: `8,864`
- Stage transition: index 0 to 1 at frame `20277`
- Scene unload: 0.295 seconds, `expected_stage_matched=true`
- Native hit edges: `4533`, `4942`, `13858`, `22077`, `23170`
- Tracked summary SHA-256:
  `3d4f1292d2afa62524f2f8040096021a3f59a354a38667204c421d43727384b2`
- Termination: deliberate `external_stop`

It then froze at a Stage-2 dialogue on frame 28,459. The last snapshot had
phase 3, zero bullets, zero lasers, Bomb inactive, and eight collectible items.
The following runtime probe showed the same frozen counter with phase 0. Since
the eligibility predicate required `not items`, no wall-clock Z edge could ever
be produced and frozen items could never leave. The trace was stopped rather
than accepting an operator key press.

Items are not hazards and Z is already the held shot key. The corrected policy
therefore depends only on player phase 0/3, Bomb inactivity, and zero active
bullets/lasers. Collectible count is deliberately absent from the predicate.
