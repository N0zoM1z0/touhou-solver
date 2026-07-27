# Touhou Solver Current Handoff

This is the volatile entrypoint for the TH08 Sakuya/Remilia no-Bomb solver.
`AGENTS.md` is the durable contract, `STRATEGY.md` is the promotion ledger,
and design/run notes retain derivations and history.

## Read In This Order

1. `AGENTS.md`
2. this file
3. `STRATEGY.md`
4. `notes/review/CONSOLIDATED_RESEARCH_AND_REFACTOR_ROADMAP_20260727.md`
   for the agreed implementation order; the formal notes below remain
   authoritative
5. `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
6. `notes/PIPELINE_ROOT_AND_HAZARD_COVERAGE_CONTRACT_20260727.md`
7. `notes/COMPLETE_MASK_ISSUE_ACTION_CONTRACT_20260727.md`
8. `notes/DUAL_BOUND_QUERY_LOCAL_REFINEMENT_CONTRACT_20260727.md`
9. `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`
10. `notes/EXACT_AUGMENTED_PARTIAL_SURVIVAL_WITNESS_CONTRACT_20260727.md`
11. `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`
12. `notes/HARD_FULL_ROUTE_FEASIBILITY_DIAGNOSIS_20260726.md`
13. `notes/PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md`
14. `notes/NATIVE_SUPPLEMENTAL_ROLLOUT_DEADLINE_CONTRACT_20260726.md`
15. `notes/EXACT_VERSION_ASYNC_SUPPLEMENTAL_PUBLICATION_20260726.md`
16. `notes/TH08_SEMANTIC_DIFFERENTIAL_FUZZER_CONTRACT_20260726.md`
17. `notes/SUPPLEMENTAL_DIRECT_ROOT_WINDOWS_CONTENTION_GATE_20260726.md`
18. the relevant recent run note and counterexample rows before live work

Before trusting a result, verify that the physical problem, formal
recurrence, implementation, immutable version, and publication deadline still
describe the same decision. Python/C++ parity is not physical correctness.

## Exact Checkpoint

- Repository branch: `main`.
- Latest committed algorithmic checkpoint:
  `5e48f3d Add exact stationary partial survival witnesses`. The first G3
  checkpoint exhaustively evaluates every root action against declared
  stationary causal continuations, merges hidden remaining-delay histories
  before continuation, applies cadence recursively, preserves pending
  no-write semantics, and retains exact problem/policy/witness digests plus a
  deterministic worst observation-compatible branch. Four randomized and
  adversarial tests match the existing independent scalar labels and native
  belief workspace. The focused control suite passes `167/167`; complete
  quick suites pass `720/720` on Linux in `9.678 s` and Windows in `13.093 s`
  with three platform skips. The 31-line compatibility facade owns no
  recurrence; digest, portfolio, replay, recurrence, and immutable records
  live under `touhou_control/partial_witness/`. This is offline attainable
  lower-witness authority only.
- The preceding G2 checkpoint `c38665b Define dual-bound refinement
  quantifiers` adds conservative patch dependency closure, candidate-guided
  8/4-pixel refinement, an independent scalar oracle, and a retained
  vectorized rectangle gate. Its six-root semantic gate passes, but the
  multi-second patch/solve timings fail delivery.
- Latest live algorithmic checkpoint remains
  `d4467bd Add deadline-aware native supplemental gate`; no live action
  authority changed in the complete-mask correction.
- Latest offline research checkpoint:
  `e24544d Retain the exact-root loss dossier`. G0 content-addresses all 61
  Hard Stage-4A empty roots and their fresh/terminal dependencies. Full replay
  matched 549 finite variants and 122 pipeline variants with zero query-field,
  digest, or completion mismatch. This is offline finite-model evidence and
  changes no live authority.
- Latest G1 shadow correctness checkpoints:
  `ff1af3c Define canonical pipeline and hazard coverage contracts` and
  `e4d994f Add the shadow pipeline pickup audit`, followed by
  `4b0f959 Define complete-mask issue actions` and
  `7facf80 Extend belief actions to complete masks`. Complete-mask roots join
  exact observation and immutable observation/hazard/policy/model/clock
  versions under SHA-256; missing/unknown hazard slabs fail closed. Physical
  audit `153821` passed trace/continuity checks but found CE-0134. Its
  movement alias is now corrected offline; full pipeline authority remains
  blocked by live integration, hazard coverage, clock, publication, and
  performance gates.
- Latest structural checkpoint:
  `d25507e Split practice dossier summary ownership`. Shared planner
  consistency, practice timing/sensor, control/viability, and behavior/spell
  summaries now live in five focused modules under `analysis/dossier/`.
  Full-run/practice entry points are 676/448 lines and retain exact historical
  aliases. A
  complete 548,614,220-byte Stage-5 replay produced byte-identical JSON,
  Markdown, death CSV, and regression JSON. A retained full-run fixture kept
  the exact pre-extraction rendered Markdown and CSV hashes. The fresh quick
  suites pass `716/716` on Linux in `8.994 s` and Windows in `12.961 s` with
  three platform skips.
  The preceding renderer checkpoint
  `1cd3a9c Separate dossier rendering from aggregation` moved stable full-run
  and practice Markdown/CSV construction into
  `analysis/dossier/full_run_render.py` and `practice_render.py`.
  The preceding attribution checkpoint `8149262 Extract shared dossier death
  attribution` moved physical contact witnesses, cause classification,
  warning leads, death-ledger construction, and clustering into
  `analysis/dossier/attribution.py`; both practice and full-run entry points
  consume that owner, while original full-run private imports remain exact
  compatibility aliases.
  The preceding live checkpoint `a388a1d Extract issue-time input overrides`
  moved deadline-hold construction and the ordered
  deathbomb/counter/auto-confirm/final hard-no-Bomb checks into
  `th08_live.issue_overrides`; physical dispatch, actuator mutation, and
  scene lifecycle remain controller-owned. The preceding native
  checkpoint `a0a7afb Separate native pipeline compatibility adapters` moved
  direct-pipeline v1 create/query adapters into `pipeline/direct_compat.cpp`;
  belief
  32-bit v2 query/upper adapters join the older create/query/upper adapters in
  `pipeline/belief_compat.cpp`. Current direct/belief workspace files retain
  the recurrence, memo, resume/cancel, and current query implementations. The
  46-symbol ABI and legacy call behavior are unchanged.
  Earlier offline checkpoint `aa9358e` moved bounded JSONL
  scanning/provenance, epoch/scope selection, compact-decision lowering, and
  stable percentile/resource statistics under `scripts/analysis/dossier/`.
  Original private imports remain compatibility aliases.
  `th08_live_dodge_agent.py`, runtime, practice/full-route supervisors,
  hotkey daemon, semantic cases, and ECL tool are compatibility/composition
  entry points over narrow packages. The live package now owns session and
  resource lifecycle, sensing/input, policy/scene clock, trace publication,
  sensing models, movement contracts, hazard projection, local certificates,
  objectives, and the complete local-planner pass. Native exports remain the
  checked-in 46-symbol ABI while geometry, local kernels, viability families,
  pipeline exports, compatibility adapters, and declaration headers have
  dedicated owners.
  Historical imports and monkeypatch seams still resolve current
  implementation globals. R2/R3/R4 remain complete. The remaining structural
  target is the staged iteration contract inside `_run_live_session`, recorded
  in `notes/review/PYTHON_MODULE_STRUCTURE_AUDIT_20260727.md`, plus the
  staged action-alignment/dispatch contract inside `_run_live_session`.
  Offline dossier entry points are now bounded aggregation, validation,
  regression, and CLI composition. No model, recurrence, float comparison,
  worker policy, action authority, report schema, attribution, summary, or
  rendering semantics changed; strategy is also unchanged.
- Structural checkpoint `6dbcc8b Split dual refinement into focused modules`
  splits the G2 implementation behind stable
  compatibility facades. Spatial cells, transitions, root scope, patch
  selection, clearance, result validation, scalar oracle, vector data plane,
  and candidate guides now live in
  `scripts/touhou_control/corridor/dual_refinement/`; the former
  897/1022-line public modules are 44/22-line facades.
- Current live-structure checkpoint introduces immutable, validated
  `CapturedIteration`, `ServiceUpdate`, `PublishedGuidance`, and
  `FreshIssueResult` boundaries inside `_run_live_session`. The local planner
  now consumes the captured contract and actuator state is updated from the
  fresh-issue contract. The surrounding controller remains the composition
  owner; this is a staged extraction, not a wholesale move.
- The fresh enemy-prefix issue stage now lives in
  `th08_live.fresh_issue`. It owns the bounded issue-time prefix read,
  dormant-body merge, aligned change detection, and conditional hard
  recertification result. The controller injects its current capture/change/
  merge/commit callbacks on every iteration, preserving historical
  monkeypatch and backend dispatch seams. Deadline handling, Bomb policy, and
  auto-confirm mask selection now delegate to the pure
  `th08_live.issue_overrides` boundary. Candidate lookup, physical dispatch,
  actuator updates, and trace publication remain controller-owned.
- Post-extraction physical retention
  `lunatic_route2_stage4a_unattended_20260727_220330` completed Stage 4A over
  frames `2..41645` with 13,295 decisions, maximum 1,362 bullets, zero Bomb
  input, accepted terminal unload, compact artifacts, supervisor completion,
  and cleanup. All 13,295 decisions retained an issue observation; 2,178
  changed observations produced exactly 2,178 recertifications, 39 action
  overrides, and zero silent outside-global selections. Seven hits all
  followed global-kernel exhaustion, extending CE-0136 rather than indicating
  a structural regression.
- Post-override-extraction retention
  `lunatic_route2_stage5_unattended_20260727_224146` completed Stage 5 over
  frames `1..43371` with 13,953 decisions, maximum 1,529 bullets, zero Bomb
  input, accepted terminal unload, compact artifacts, supervisor completion,
  and cleanup. All 13,953 decisions retained the issue guard; 2,419 geometry
  changes produced exactly 2,419 recertifications, 58 overrides, and zero
  silent outside-global selections. It took 13 hits, all after global-kernel
  exhaustion. This retains the structural input-override path and extends
  CE-0137; it is not route acceptance or controlled evidence that the
  refactor changed survival.
- Corridor-trace characterization checkpoint `6a75a6a` adds a pure
  `th08_live.corridor_trace` record builder. The live loop still constructs
  the historical inline record and asserts exact equality with the extracted
  record before publishing the latter. This deliberately duplicates work for
  one checkpoint so deletion of the inline path has an
  executable schema-parity gate; no action decision or issue ordering moved.
- Structural checkpoint `3606656 Extract corridor trace serialization`
  removes the characterized inline path. `controller.py` now delegates
  corridor trace construction to the pure builder and is 6,126 lines, down
  from 6,614 at the iteration-stage checkpoint. The builder consumes only
  completed publications and lookup-only values after issue; it performs no
  sensing, query expansion, worker mutation, or dispatch.
- Candidate-trace characterization checkpoint `77418c0` adds pure outcome,
  snapshot, publication, and complete shadow-service record builders under
  `th08_live.candidate_trace`. Structural checkpoint
  `fab3d51 Extract candidate verifier trace serialization` removes the
  characterized controller helpers and inline record. Historical private
  imports resolve aliases to the focused module; candidate verification
  remains shadow-only.
- Decision-control trace characterization checkpoint `0b7aa85` adds an
  immutable `DecisionControlTraceInput` and a pure builder for deadline,
  delay, dispatch, local-certificate, objective/guidance, player, damage
  shadow, robust-control, and terminal-threat fields. The historical inline
  fields were compared key-for-key before update. Structural checkpoint
  `40daa6c Extract decision control trace fields` removes those inline fields
  and consumes the extracted field set.
- Sensing-trace characterization checkpoint `f70bccd` adds an immutable
  `SensingTraceInput` and pure boss/ECL/hazard/alignment/issue-guard record
  builder. Structural checkpoint `ad8de27 Extract live sensing trace fields`
  removes the characterized inline sensing path and consumes the extracted
  fields.
- The pending final trace-characterization checkpoint adds pure declared
  timing-boundary and optional nearby/transform hazard builders under
  `th08_live.decision_trace`. Historical inline fields remain for one
  checkpoint and are compared before update.
- The current release-preparation commit must be a descendant of that
  checkpoint.
- Release verification rebuilt both native targets and passed the reduced
  quick suite `584/584` on Linux in `5.213 s` and Windows in `14.365 s`.
- The completed R4 checkpoint passes the expanded quick suite `614/614`
  on Linux in `5.655 s` and Windows in `8.603 s` with three platform skips.
- The R5 code checkpoint passes `628/628` on Linux and Windows with three
  platform skips. Its six-workload intensive semantic run has exact
  Python/native actions and hard vectors with zero collision, clearance-sign,
  or batch-invariance mismatch.
- The G0 checkpoint passes the expanded quick suite `635/635` on Linux and
  Windows with three Windows platform skips. The exact-root package is split
  into source, result-semantics, dossier, and replay modules; the legacy
  differential audit remains its compatible evidence source.
- The final G1 checkpoint passes `653/653` on Linux in `5.628 s` and Windows
  in `8.784 s` with three platform skips, including CE-0134's explicit
  promotion-blocker regression.
- The complete-mask correction rebuilds Linux and Windows native libraries
  with an exact 46-symbol ABI manifest and passes `663/663` on Linux in
  `6.049 s` and Windows in `8.859 s` with three platform skips. The bounded
  formal audit and 16-case belief benchmark report zero corrected
  scalar/native, upper, candidate, bound, portfolio, or certification
  failure.
- The G2 offline semantic checkpoint passes `683/683` quick tests on Linux in
  `8.381 s` and Windows in `12.852 s` with three Windows platform skips. All
  six retained spatial roots satisfy lower/reference/upper action inclusion
  and are recovered by a completed lower witness without a full-field patch.
  Patch construction takes `3160.63..14153.12 ms`, vector solving takes
  `859.02..4008.67 ms`, and the worst root refines 77.47% of the field.
  `S09` therefore remains offline/shadow-only.
- The post-G2 module split passes `686/686` quick tests on Linux in `9.057 s`
  and Windows in `13.067 s` with three Windows platform skips. Three explicit
  structure tests preserve old-facade/new-module symbol identity.
- The live iteration-contract checkpoint passes `689/689` quick tests on
  Linux in `8.887 s` and Windows in `12.802 s` with three Windows platform
  skips. Its supervised Windows retention smoke
  `hard_route2_stage1_unattended_20260727_173735` completed Hard Stage 1 over
  frames `1..20950` with 7,680 decisions, zero hits, zero Bomb input,
  accepted terminal unload, route completion, artifact materialization, and
  no residual game/controller/supervisor process.
- The corridor-trace characterization checkpoint passes `691/691` quick
  tests on Linux in `8.593 s` and Windows in `13.001 s` with three Windows
  platform skips. Two focused tests cover absence and representative
  publication serialization; the live loop additionally compares the
  complete old and extracted records at runtime before enqueuing.
- After deleting the inline corridor serializer, the same `691/691` quick
  tests pass on Linux in `8.417 s` and Windows in `12.730 s` with three
  Windows platform skips. Supervised physical retention
  `hard_route2_stage1_unattended_20260727_175715` completed Hard Stage 1 with
  7,305 decisions, 7,263 corridor records, zero required-field omissions,
  zero Bomb input, accepted route completion, artifact materialization, and
  no residual process. It took one native hit at frame 6,385 after global
  viability-kernel exhaustion, so this is structural/trace retention
  evidence, not a clean survival pass.
- Candidate-trace characterization passes `694/694` quick tests on Linux in
  `8.468 s` and Windows in `13.079 s` with three Windows platform skips.
  Thirteen focused tests cover witness-publication authority, status
  precedence, disabled service behavior, and completed-result serialization.
- After deleting the candidate helpers and inline serializer, `controller.py`
  is 5,817 lines and the same `694/694` quick tests pass on Linux in
  `8.747 s` and Windows in `13.115 s` with three Windows platform skips.
  Supervised physical retention
  `hard_route2_stage1_unattended_20260727_181119` completed Hard Stage 1 with
  7,686 decisions, zero Bomb input, route completion, accepted artifacts, and
  no residual process. The default workload did not enable the candidate
  shadow, so candidate serialization authority rests on deterministic tests;
  the physical run retains surrounding live-loop and lifecycle behavior. It
  took one native hit at frame 2,043 after global-kernel exhaustion and is not
  a clean survival pass.
- Decision-control trace characterization passes `695/695` quick tests on
  Linux in `9.067 s` and Windows in `13.266 s` with three Windows platform
  skips. Live-focused tests pass `108/108`.
- After deleting the inline decision-control fields, `controller.py` is 5,594
  lines and `695/695` quick tests pass on Linux in `8.936 s` and Windows in
  `13.006 s` with three Windows platform skips. Supervised physical retention
  `hard_route2_stage1_unattended_20260727_182434` completed Hard Stage 1 over
  frames `2..20663` with 7,557 decisions, zero hits, zero Bomb input, accepted
  route completion, artifacts, and no residual process. All 7,557 decision
  records retained the required control-field groups.
- Sensing-trace characterization passes `696/696` quick tests on Linux in
  `8.767 s` and Windows in `13.385 s` with three Windows platform skips.
  Live-focused tests pass `109/109`.
- After deleting inline sensing fields, `controller.py` is 5,411 lines and
  `696/696` quick tests pass on Linux in `8.558 s` and Windows in `13.785 s`
  with three Windows platform skips. High-pressure Windows retention
  `hard_route2_stage4a_unattended_20260727_183640` completed Hard Stage 4A
  over frames `2..45392` with 15,122 decisions, maximum 1,072 active bullets,
  zero Bomb input, accepted route completion, artifacts, and no residual
  process. All decision records retained the 18 required sensing field groups.
  The run took eight hits, six after global-kernel exhaustion, so it is
  structural retention plus CE-0136 survival-failure evidence, not a route
  acceptance result.
- Timing/optional-hazard characterization passes `698/698` quick tests on
  Linux in `8.957 s` and Windows in `13.124 s` with three Windows platform
  skips. Live-focused tests pass `111/111`.
- After deleting the inline timing and optional-hazard paths,
  `controller.py` is 5,377 lines. Live-focused tests pass `111/111`; the
  Linux quick suite passes `698/698` in `9.177 s`; the Windows quick suite
  passes `698/698` in `12.894 s` with three platform skips. Supervised
  high-pressure retention
  `hard_route2_stage5_unattended_20260727_185422` completed Hard Stage 5 over
  frames `2..40448` with 12,602 decisions, maximum 1,190 active bullets,
  zero Bomb input, accepted route completion, compact artifacts, supervisor
  completion, and no residual process. Every decision retained the required
  timing fields and enabled optional-hazard records. The run took eight hits,
  all after global-kernel exhaustion, so it is structural retention plus
  CE-0137 survival-failure evidence rather than route acceptance.
- Planner-pass split characterization freezes five complete decisions after
  excluding physical timing measurements: open field, incoming bullet,
  multi-delay certification, hard viability constraint, and supplemental
  recovery. The pre-split quick suite passes `699/699` on Linux in `8.633 s`
  and Windows in `13.137 s` with three platform skips.
- Planner-pass contracts now live in `th08_live.planner_pass_types`:
  controller-owned dependencies, mode transition, and timing accumulator.
  The behavior implementation is 1,599 lines and the Linux quick suite
  retains `699/699` in `8.982 s`; the five-decision digest is unchanged.
- Baseline native-reducer preparation and `BaselineBeamContext` execution now
  live in `th08_live.planner_pass_baseline`; the remaining orchestrator is
  1,503 lines. The supplemental async job is still submitted before baseline
  execution. Five complete decisions are unchanged; quick suites pass
  `699/699` on Linux in `8.837 s` and Windows in `13.130 s` with three skips.
- Supplemental pre-submit, direct/native search, exact-version lookup,
  deadline/cancel/error fallback, position cost, and terminal labeling now
  live in `th08_live.planner_pass_supplemental`; the orchestrator is 852
  lines. Five complete decisions and six semantic differential gates are
  unchanged; a fresh Linux quick suite passes `699/699` in `8.878 s` and
  Windows passes `699/699` in `12.977 s` with three skips. The Linux suite
  also exposed an unresolved 1-ms wall-deadline test flake: the pipeline
  prewarm deadline gate failed twice in full-suite order, passed focused, and
  passed the final fresh full run. No test was weakened.
- Endpoint ranking, robust override, pre-loss admission, damage shadow,
  decision assembly, and relaxed-viability transition now live in
  `th08_live.planner_pass_finalize`. The pass entry point is a 320-line
  prepare/orchestration layer; baseline/finalize/supplemental/contracts are
  209/587/755/109 lines. Five complete decision digests remain unchanged;
  quick suites pass `699/699` on Linux in `8.862 s` and Windows in `13.247 s`
  with three skips.
- High-pressure retention
  `hard_route2_stage6b_unattended_20260727_193155` completed Hard Stage 6B
  over frames `1..72862` with 22,140 decisions, maximum 1,454 active bullets,
  maximum 256 active lasers, zero Bomb input, accepted route completion,
  compact artifacts, supervisor completion, and no residual process. Every
  decision retained the required planner groups with zero supplemental
  failures. The run took 13 hits, all after global-kernel exhaustion, so it
  is CE-0138 survival-failure evidence rather than route acceptance.
- Post-refactor Lunatic retention
  `lunatic_route2_stage4a_unattended_20260727_210928` completed Stage 4A over
  frames `2..45549` with 15,110 decisions, maximum 1,528 active bullets,
  native decode/hazard/beam backends, zero Bomb input, accepted terminal
  unload, artifact materialization, supervisor completion, and no residual
  game/controller process. It took 22 hits, all after global-kernel
  exhaustion. The fresh-attempt frame-1,174 bullet overlap followed a
  last-alive root whose hazard contract already marked the next slab unknown;
  the contacting slot first appears in the retained nearby set at the hit.
  This is CE-0139 future-event coverage evidence and native/live structural
  retention, not survival or model-validity acceptance.
- Post-refactor Lunatic Stage-5 retention
  `lunatic_route2_stage5_unattended_20260727_212624` completed frames
  `2..41508` with 12,770 decisions, maximum 1,533 bullets, zero Bomb input,
  accepted terminal unload, compact artifacts, supervisor completion, and no
  residual process. It took eight hits, all after global-kernel exhaustion.
  The fresh hit followed global loss by 230 frames, robust action-set
  exhaustion by nine frames, and negative short-pipeline clearance by two
  frames. This extends CE-0137: global loss is an early causal warning, not
  an imminent-collision label, and current distant recovery does not provide
  a completed viable continuation.
- Post-refactor Lunatic Stage-6B retention
  `lunatic_route2_stage6b_unattended_20260727_213748` completed Final B over
  frames `2..73670` with 22,430 decisions, maximum 1,536 bullets and 245
  lasers, zero Bomb input, accepted terminal unload, compact artifacts,
  supervisor completion, and no residual process. It took 16 hits, all after
  global-kernel exhaustion: seven bullet overlaps, six modeled
  committed-prefix collisions, two laser overlaps, and one simultaneous
  multi-hazard overlap. Spells 154 and 162 completed their laser phases
  without hits, while spells 158 and 166 retain exact laser contacts. This
  extends CE-0138 and keeps laser-specific correction separate from the
  broader boundary/recovery failure.
- Query-local public value contracts now live in
  `touhou_control.query_survival_types`: pending command, reachable root,
  scalar/belief stats, upper certification, action recommendation, and query
  result. The retained legacy always-issue scalar recurrence now lives in the
  independent `touhou_control.query_survival_scalar` module and shares only
  cadence/lattice validation from `query_survival_lattice`; it does not call
  the native implementation it audits. Exact kinematic next-root enumeration
  now lives in `query_survival_roots`, including its reusable prepared
  context; the facade preserves both the public enumerator and historical
  private prewarm import. The legacy versioned native memo, cancellation and
  deadline aliases, stale-version error, prewarm/merge, and lookup-only
  consumer now live in `query_survival_workspace`. The non-clairvoyant
  belief workspace, attainable-budget queries, admissible upper
  certification, and action-column recommendation now live together in
  `query_survival_belief_workspace`. One-shot native dispatch and the
  independent scalar fallback boundary now live in
  `query_survival_dispatch`. Immutable numeric problem ownership, dense
  policy factories, post-publication label construction, and workspace
  factories now live in `query_survival_problem`. The compatibility facade is
  80 lines. Focused
  query-survival/complete-mask/variable-cadence/policy-synthesis tests pass
  `17/17`, `3/3`, `8/8`, and `4/4`; quick suites pass `699/699` on Linux in
  `9.179 s` and Windows in `13.095 s` with three skips.
- Viability actions, configuration, Boolean query results, and continuous
  safety-value query results now live in `touhou_control.viability_types`;
  cached lattice-transition construction now lives in
  `viability_transitions`; queryable Boolean and signed-clearance policy
  objects now live in `viability_policy`; Boolean and signed-value induction
  now live in `viability_builders`. `viability` is a 29-line compatibility
  facade that preserves original public identities, signed nearest-lattice
  error arrays, and the historical patchable `native_backend` attribute. Its
  focused suite passes `20/20`; quick suites pass `699/699` on Linux in
  `9.451 s` and Windows in `12.965 s` with three skips.
- Native-local immutable decoded/rollout results, supplemental exceptions,
  pointer aliases, and ctypes query/output layouts now live in
  `touhou_control.native.local_abi`; hazard queries and raw bullet-pool
  decoding, together with their loaders, now live in
  `native.local_sensing`; baseline and supplemental quantized beam reducers,
  with their distinct loaders/orderings, now live in
  `native.local_reducers`; persistent rollout lifecycle, frame-major packing,
  cancellation/deadline decoding, and result ownership now live in
  `native.local_supplemental`. `native.local` is a 54-line compatibility
  facade with a loader-injection shim; its and `native_backend`'s exports
  retain object identity. Native facade,
  hazard/beam, and semantic differential suites pass `4/4`, `5/5`, `5/5`,
  and `6/6`; bullet-runtime decoding passes `12/12`; the Linux quick suite
  passes `699/699` in `9.290 s`; Windows passes `699/699` in `13.974 s` with
  three skips.
- TH08 input masks, playfield geometry, measured movement speeds, planner
  action construction, and complete local actuator-state naming now have one
  owner in `th08_live.movement`. `controller.py` re-exports the historical
  names and consumes the same immutable action tuples. Live-focused tests
  pass `101/101`; the Linux quick suite passes `699/699` in `9.671 s`.
  This is a structural ownership change only; masks, float values, ordering,
  no-Bomb behavior, and action authority are unchanged.
- Local item projection/ranking, transformed-bullet frame projection, the
  independent NumPy hazard kernel, and the parity-gated native hazard adapter
  now live in `th08_live.local_hazards`. Backend selection remains
  controller-owned so historical runtime and benchmark patch seams retain
  their semantics. `controller.py` is 4,812 lines. Hazard, bullet-decoder,
  certificate, live-controller, and semantic differential focused suites
  pass; the Linux quick suite passes `699/699` in `9.006 s`.
- Held-input player projection, travel-time lower estimates, scalar/vector
  boundary risk, boundary reserve deficit, and opposed-direction detection
  now join masks/speeds/actions in `th08_live.movement`. Controller aliases
  preserve the historical surface. Local certificate and live-controller
  focused suites pass; the Linux quick suite passes `699/699` in `9.281 s`.
  All equations and float operations moved unchanged.
- Control-prefix evaluation, retained legacy last-desired differential
  certificates, and explicit active/held/pending pipeline certificates now
  live in `th08_live.local_certificates`. The 4,344-line controller keeps
  exact-signature wrappers which inject its current hazard dispatcher, so
  backend selection and historical monkey-patch fault injection remain live.
  Quick suites pass `699/699` on Linux in `9.140 s` and Windows in
  `13.505 s` with three platform skips.
- Survival-first item tie-breakers, endpoint ranking, terminal continuation
  warnings, and clamped-boundary degeneracy detection now live in
  `th08_live.local_objectives`. The 4,190-line controller injects its current
  hazard dispatcher only into the warning rollout, preserving backend and
  fault-injection behavior. The Linux quick suite passes `699/699` in
  `9.106 s`; item objectives remain disabled in live acceptance.
- The former 1,134-line native `local/kernels.cpp` is now three explicit
  translation units: `local/hazards.cpp` (399 lines),
  `local/bullet_decode.cpp` (196), and `local/beam_reduce.cpp` (573).
  The checked-in build source list names all three. Linux and Windows release
  libraries rebuild with the unchanged 46-symbol manifest; focused
  hazard/beam/decode/semantic gates pass. Quick suites pass `699/699` on
  Linux in `8.927 s` and Windows in `13.102 s` with three skips.
- The former 1,211-line native `viability/kernels.cpp` is now explicit
  worker-limit, Boolean viability, signed-value/policy, and survival-label
  translation units of 41, 354, 508, and 362 lines plus an 8-line internal
  worker header. Linux/Windows release builds retain the exact 46-symbol ABI;
  viability/query-survival/differential gates pass. Quick suites pass
  `699/699` on Linux in `8.942 s` and Windows in `13.284 s` with three skips.
- Legacy belief-pipeline create/query/upper implementation adapters now live
  in `pipeline/belief_compat.cpp` (398 lines); the current 64-action
  workspace, recurrence, class-dependent 32-bit guards, certificates,
  recommendation, cancel, and destroy stay in `belief_workspace.cpp`
  (2,264). Both release builds retain the exact 46-symbol ABI. Quick suites
  pass `699/699` on Linux in `8.836 s` and Windows in `12.961 s` with three
  skips.
- The former 982-line native `geometry/clearance.cpp` is now four explicit
  ABI-family TUs: clearance volume (314), segment trajectory (225), AABB
  trajectory (182), and piecewise AABB (233), sharing only an 89-line inline
  segment-primitive header. Both release builds retain the 46-symbol ABI;
  corridor/native-facade/ABI gates pass. Quick suites pass `699/699` on Linux
  in `9.099 s` and Windows in `13.393 s` with three skips.
- The former 934-line native `abi/pipeline_abi.cpp` is now direct-pipeline
  (242), belief-pipeline (633), and query-local (69) export-family TUs. This
  changes no exported declaration or implementation target. Both release
  builds retain the exact 46-symbol manifest; quick suites pass `699/699` on
  Linux in `9.006 s` and Windows in `13.099 s` with three skips.
- The former 864-line native internal implementation-declaration header is
  now a 6-line compatibility include over geometry (102), local (165),
  pipeline (467), and viability (139) declaration headers. This changes no
  declaration or build source. Both release builds and the exact ABI gate
  pass; quick suites pass `699/699` on Linux in `8.930 s` and Windows in
  `12.846 s` with three skips.
- The original focused Windows physical smoke
  `hard_route2_stage1_unattended_20260727_133807` completed Stage 1 and
  supervisor cleanup with 7,541 decisions and zero Bomb input. It had one
  native hit at frame 5,262; this is CE-0132 and is survival-failure evidence,
  not a clean-pass or strategy-promotion result.
- The post-planner-extraction retention smoke
  `hard_route2_stage1_unattended_20260727_144128` completed Hard Stage 1 with
  7,502 decisions over frames `1..20768`, zero hits, zero Bomb input, accepted
  terminal unload, artifact materialization, supervisor cleanup, and no
  residual game/controller process. It is an implementation-retention gate,
  not route-strategy promotion.
- G1 physical shadow
  `hard_route2_stage1_unattended_20260727_153821` completed 7,574 decisions
  through Hard Stage 1, `route_complete`, zero Bomb input, supervisor cleanup,
  and no residual process. Linux and Windows replay agreed on 7,574 valid
  identities, 3,106 writes, 4,468 no-writes, 1,513 multikey transactions, 173
  last-write-wins replacements, 92 pending no-write carries, 2,900 observed
  pickups, and zero audit failure. It took one hit at frame 2,651 after
  kernel exhaustion, so it is not a clean survival pass.
- The same audit found 135 complete-mask writes with unchanged movement/focus
  projection. At frame 13,133, `right+SHOT -> right` was a real write while
  right was pending and stay was active; the movement-only recurrence calls
  it no-write. CE-0134 blocks full pipeline promotion until the corrected
  complete issue identity reaches an exact-version physical consumer; the
  scalar/native offline recurrence is now corrected.
- The first CE-0134 correction checkpoint defines a game-neutral injective
  complete-mask alphabet and a 36-token TH08 no-Bomb adapter. It preserves the
  old 17 movement projections while distinguishing equal-velocity Shot/Focus
  writes.
- The native correction adds backward-compatible 64-bit belief ABI v7/v3 and
  keeps old direct/viability and belief ABI boundaries at 32 actions. A
  deterministic six-frame witness shows equal-velocity pending identity swaps
  root values `(5,+1)` and `(2,-1)`; all 36 Python/native action labels,
  high best-action bits, and high upper-unresolved bits agree. This remains
  offline/shadow infrastructure only.
- No TH08 process, controller daemon, supervisor, or unfinished experiment is
  expected to be alive.
- Native build output, raw traces, screenshots, caches, and the local
  `image.png` are ignored. The user-supplied `audits/` directory remains
  intentionally untracked; other repository work is clean.

Sanity check:

```bash
git status --short
git log -5 --oneline
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

## Current Result

### Local micro-control

**Observed:** persistent pool-read destinations, packed native bullet decode,
hazard-major shared native C++ queries, and native quantized no-item beam
reduction match their independent Python/NumPy paths on retained direct roots
and generated semantic cases. The live issue path still uses a fresh exact
local collision certificate and hard no-Bomb fallback.

**Observed:** the 256-case semantic gate and 96-case research profile had zero
collision, clearance sign/value, risk, batch-invariance, or supplemental
endpoint mismatches. Research maxima were 3,900 bullets, 1,387 lasers,
62 bodies, and horizon 24. NumPy/native geometry p95 was
`121.538/40.500 ms`; Python/native supplemental p95 was
`9.931/3.337 ms`.

**Conclusion:** local decode/geometry performance is serviceable and is not
the dominant physical failure in current Hard evidence. This is implementation
and sampled finite-semantics evidence, not complete shipped-game or physical
safety proof. Keep the Python oracles and explicit rollback paths.

**Observed structural gate:** the R4 local-planner split preserves all six
generated intensive action/hard-vector comparisons with zero collision,
clearance-sign, or batch-invariance mismatch. The isolated live-like native
sequence measured `28.325/28.865 ms` median/p95 versus the retained
`27.178/27.942 ms`; this is not a significant pure-refactor regression.
Fresh/global historical regressions, field-by-field issue metadata rebinding,
and hard no-Bomb checks pass. This is implementation parity, not new model or
physical authority.

### Physical Hard evidence

**Observed:** Hard Stage-1 run `175049` completed 7,099 decisions with zero
hits, Bombs, or deadline misses.

**Observed:** the post-R5-decomposition Hard Stage-1 smoke `133807` completed
7,541 decisions, terminal scene handling, post-stage no-save, controller
shutdown, and game cleanup with zero Bomb input. It had one native bullet hit
at frame 5,262 during spell 0. The global kernel was queryable but empty, with
a 12-frame warning lead. This validates the physical lifecycle/trace boundary,
not survival equivalence; see CE-0132 and the retained run dossier.

**Observed:** complete original-game Hard Route-2 run `184942` reached Final B
and `route_complete` with 70,699 decisions, 39 hits, zero Bombs, and stage hit
counts `1/1/8/11/9/9`. Global viability was already empty before 38/39 hits.
Boundary and fast-mode factors appeared on 30 and 29 hits. Per-stage
local-plan median/p95 remained within `11.81..14.55/20.86..26.90 ms`, at up
to 1,231 bullets and 256 lasers.

**Observed:** Hard Stage-4A audit `202439` retained 1,741 validated capsules.
The G0 replay independently reproduced all 61 empty same-root queries:
six are `SPATIAL_AMBIGUITY`, eight are `SHORT_HORIZON_ONLY`, and 47 remain
`MODELED_LOSING_UNRESOLVED`. Seven orthogonal `FUTURE_BIRTH_GAP` witnesses
must not be counted as false-empty explanations. Uniform full-field 4-pixel
solving cost `1062.85/3506.43 ms` median/p95 on 12 roots and is not a live
design.

**Observed:** all 15 contacts have a retained same-epoch nonempty-to-empty
boundary. Leads are `10..874` frames with median 63; four are more than 240
frames before contact. CE-0133 rejects assuming a fixed pre-hit window
contains the exhaustion boundary.

**Conclusion:** the primary algorithmic problem is preserving global
feasibility earlier, conservatively covering future hazard events before
issue, and defining certified behavior after finite-kernel exhaustion, not a
wholesale local geometry rewrite. CE-0139 physically demonstrates that
implementation parity cannot close a hazard slab the model itself declares
unknown.

### Issue transaction and supplemental search

**Observed:** CE-0127/0128's fresh/global issue transaction passed no-audit
Hard Stage-4A runs `211210` and `212756`: 4,627 transactions had zero silent
outside-global selections, zero Bombs, and no latency regression.

**Observed:** adding repair volume to shared beam pruning regressed two of 800
pre-hit terminal hard vectors (CE-0129). The historical beam and native reducer
ABI therefore remain unchanged. The width-4 supplemental lane preserves the
historical endpoint and passed same-root finite nonregression checks, but is
proposal-only.

**Observed:** the complete native supplemental boundary uses a persistent C++
workspace, 5-ms absolute deadline, cooperative cancellation, and
complete-only results. Native rollout cost `0.876/1.365/1.942 ms`
median/p95/max under the retained Windows workload, but end-to-end synchronous
delivery still had `7.054/53.721 ms` paired p95/max and one new deadline proxy
miss.

**Observed:** exact-version asynchronous publication used a below-normal,
newest-wins worker, exact identity, stale cancellation/discard, and
nonblocking lookup. It completed 728/729 eligible roots and retained 294/294
reference changes with zero finite/parity/fallback violations, but paired
latency remained `2.240/8.139/12.214 ms` and created CE-0131's new hybrid
deadline miss.

**Decision:** both current-issue supplemental delivery forms are rejected.
Keep the live four-worker global planner, keep supplemental modes default-off,
and do not enter a focused physical A/B without a new causal publication
design and the unchanged Windows contention gate.

### Frozen manager-frame boundary

**Observed:** during post-spell/dialogue transitions,
`enemy_manager_frame` can freeze while held input continues moving the player
(CE-0120). The 50-ms repeated-counter detector fired on ordinary slow
decisions, churned versions, and starved viability (CE-0121).

**Decision:** the native FRScreen/MSG episode sensor remains shadow-only. No
wall-time threshold or manager counter currently has live actuator authority.
This remains a parallel sensing/control obligation, but it is not the primary
global-planning objective.

## Authority Boundary

| Status | Component | Authority |
| --- | --- | --- |
| live | native-state sensing and TH08 hazard projection | Gameplay state comes from native memory; screenshots are not a runtime sensor. |
| live | native local implementation acceleration | Pool buffers, packed decode, shared hazard query, and local reducer implement existing semantics with Python rollback. They add no model authority. |
| live | issue-time local collision certificate | Fresh hard fallback, per-position batch semantics, hard no-Bomb, and the CE-0127/0128 fresh/global transaction. Live callers still use the active-equals-held estimator fallback. |
| live | coarse Boolean robust viability | Current global finite-model safety authority, subject to declared resolution/horizon/uncertainty and the unresolved transition-clock boundary. |
| shadow | native FRScreen/MSG input-clock boundary | Detects episodes; cannot retire/reset policy or neutralize movement. |
| shadow | explicit complete-mask active/held/pending certificate | Canonical trace identity and a 36-action scalar/native recurrence exist. CE-0134 is corrected offline; future-event unknown coverage, CE-0120, performance/publication, and physical integration block live ranking. |
| shadow | restricted losing-root candidate verifier/publication | May prove a declared finite candidate and retain its witness; cannot claim unrestricted losing/optimality or change input. |
| offline/shadow | belief lower bounds, revealed-delay upper, resumable refinement | Feasibility/optimality research; too slow or optimistic for current live authority. |
| proposal-only | losing-state control reserve | Ranks fresh-hard-equivalent actions after Boolean exhaustion; physical effect unmeasured. |
| proposal-only | final-only continuation and width-4 supplemental lane | Preserves hard membership and the historical incumbent in finite replay; no live CLI or delivery authority. |
| rejected | repair-aware shared beam pruning | CE-0129 terminal-hard regressions. |
| rejected | synchronous native supplemental delivery | End-to-end Windows latency gate failed. |
| rejected | same-issue exact-version async supplemental delivery | CE-0131 deadline-proxy miss. |
| rejected | repeated-manager-frame wall-time guard | CE-0121 false firing and publication starvation. |
| rejected | every-root candidate submission / inline survival refinement | Measurable contention on the live publication path. |
| proposal-only | greedy, learned, Monte Carlo, MCTS, unproved beam/pruning | May order proposals; cannot replace worst-case verification. |

Promotion requires an updated formal review, exact authority boundary,
deterministic regressions, clean side-effect-free shadow evidence, delivery
measurement, and a `STRATEGY.md` status change.

## Open Problems In Priority Order

### P0 — Preserve global feasibility and define post-loss authority

Current Hard failures overwhelmingly follow finite-kernel exhaustion.
G0 exact-root classification and the G1 shadow identity/coverage audit are
complete. G1 rejected live promotion after CE-0134 exposed a real
complete-mask write collapsed to movement no-write. That alias is corrected
offline, but every physical root remains future-event `model_unknown`,
CE-0120 is open, and no complete-mask publication/consumer gate exists. G2
provides a branch-preserving query-local lower/reference/upper semantic gate
for six retained spatial roots, but its multi-second Python patch/dense solve
fails delivery. G3 now has an exact stationary scalar witness and complete
all-root-action portfolio with small-case scalar/native parity. The next
useful checkpoint is the retained Stage-4A/Stage-6B exact-root witness report,
with G5 future-event coverage in parallel. Work should:

1. run the G3 witness on retained first-loss roots and publish guaranteed
   frames, bottleneck margin, worst branch, policy digest, exact immutable
   root identity, and explicit completion status;
2. extend beyond stationary continuations only through a declared causal,
   observation-compatible, budget-complete class; unresolved/timeout actions
   remain unresolved rather than losing;
3. use completed restricted witnesses only as attainable post-loss lower
   bounds and intersect any later consumer with a fresh local hard set;
4. add complete issue identity to the scalar/native recurrence, then complete
   future-birth, transform, body, pending-command, and clock coverage
   without treating missing hazards as false-empty rescue evidence;
5. move only G2's sparse data plane toward native/cancellable execution while
   preserving its retained cell-intersection/union, dependency-closure, and
   branch-preserving tube contract; never use uniform full-field 4-pixel
   solving;
6. keep survival hard and route/resource objectives inside the viable set;
7. publish the authoritative Boolean result before optional work;
8. use extra CPU through deterministic process-level independent-root shards,
   without increasing the live same-root worker default beyond four;
9. validate recurrence/geometry changes with the semantic fuzzer and validate
   delivery claims on Windows direct roots.

Candidate exhaustion, timeout, or a budgeted lower bound must remain
unresolved rather than “losing.”

### P1 — Complete sensing and future-hazard semantics

One Hard-route contact was a sensor gap, one enemy-body contact was absent
from the action snapshot, and earlier cached-global selections were contradicted
by fresh local prefixes. Continue birth, transform, body, and issue-snapshot
audits with retained minimal witnesses. Do not broaden action authority from
incomplete sensing.

### P2 — Resolve CE-0120 at the actuator boundary

Retain exact episode-entry active/held/pending roots and a no-write
counterfactual that removes movement while preserving `SHOT`. Extend the
negative set across pauses, unloads, dialogues, and `msg_state == -2`;
measure probe and delivery contention. Only then consider an explicitly
scoped physical neutralization/reset trial.

### P3 — Reopen supplemental delivery only with a new causal boundary

The finite selector remains useful offline. Reopen it only if the exact
hazard/policy version can exist before the issue transaction or execution
resources are genuinely isolated. Rerun the unchanged Windows gate; do not
weaken four global workers or reuse a merely similar root.

## Formal References

- Base physical/information contract:
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
- Reachable tube:
  `notes/AUGMENTED_PIPELINE_REACHABLE_TUBE_20260725.md`
- Lower/upper/anytime synthesis:
  `notes/DUAL_BOUND_QUERY_LOCAL_REFINEMENT_CONTRACT_20260727.md`,
  `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`,
  `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`,
  `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`,
  `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`
- Candidate witness/publication:
  `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`,
  `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`
- Local pipeline and native acceleration:
  `notes/LOCAL_PIPELINE_CERTIFICATE_AND_BEAM_AUDIT_20260726.md`,
  `notes/LOCAL_NATIVE_GEOMETRY_AND_CONTENTION_20260726.md`
- Hard feasibility:
  `notes/HARD_FULL_ROUTE_FEASIBILITY_DIAGNOSIS_20260726.md`,
  `notes/HARD_STAGE4A_VIABILITY_DIFFERENTIAL_20260726.md`,
  `notes/EXACT_ROOT_LOSS_DOSSIER_20260727.md`
- Pre-loss/supplemental:
  `notes/PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md`,
  `notes/IMMUTABLE_SUPPLEMENTAL_CONTINUATION_LANE_20260726.md`,
  `notes/NATIVE_SUPPLEMENTAL_ROLLOUT_DEADLINE_CONTRACT_20260726.md`,
  `notes/EXACT_VERSION_ASYNC_SUPPLEMENTAL_PUBLICATION_20260726.md`,
  `notes/SUPPLEMENTAL_DIRECT_ROOT_WINDOWS_CONTENTION_GATE_20260726.md`
- Frozen input clock:
  `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`
- Canonical pipeline root and hazard coverage:
  `notes/PIPELINE_ROOT_AND_HAZARD_COVERAGE_CONTRACT_20260727.md`
- Generated differential:
  `notes/TH08_SEMANTIC_DIFFERENTIAL_FUZZER_CONTRACT_20260726.md`

Relevant durable failures include CE-0108, CE-0109, CE-0111, CE-0118,
CE-0120 through CE-0125, and CE-0127 through CE-0134. Historical notes do not
override the authority table above.

## Retained Workloads

| Workload | Bundle | Purpose |
| --- | --- | --- |
| Lunatic Route-2 Stage 4A | `100451`, `103856` | CE-0120/0121 canonical transition evidence and replay floor. |
| Hard Route-2 Stage 1 | `175049`, `144128`, `153821` | Zero-hit native/local and refactor gates; G1 trace/pickup gate with one survival failure. |
| Hard Route-2 full route | `184942` | Complete route, 39-hit feasibility diagnosis; one-bundle evidence only. |
| Hard Route-2 Stage 4A | `202439`, `211210`, `212756` | Capsule audit and fresh/global issue transaction; `211210/212756` form the newest compatible no-audit floor. |

Compact benchmark evidence:

- `artifacts/benchmarks/local_pipeline_certificate_20260726.json`
- `artifacts/benchmarks/local_native_hazard_hazard_major_windows_20260726.json`
- `artifacts/benchmarks/native_packed_bullet_decode_windows_20260726.json`
- `artifacts/benchmarks/local_issue_contention_windows_20260726.json`
- `artifacts/benchmarks/hard_supplemental_direct_root_contention_windows_20260726.json`
- `artifacts/benchmarks/hard_supplemental_full_native_direct_root_contention_windows_20260726.json`
- `artifacts/benchmarks/hard_supplemental_exact_async_final_direct_root_contention_windows_20260726.json`
- `artifacts/benchmarks/th08_semantic_differential_gate_20260726.json`
- `artifacts/benchmarks/th08_semantic_differential_research_20260726.json`

Raw replay bundles remain local and ignored. Do not delete an older workload
bundle until the two-newer-compatible-bundle rule in `AGENTS.md` is satisfied.

## Environment And Build

- WSL distribution: `ubuntu`
- Windows game directory:
  `D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)`
- Target: `th08.exe`
- Required SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
- Launcher: `run_th08_no_life_decrement_attach.bat`
- No-life-decrement patch byte: `0x0044D0FA`, expected `0x00`
- Windows Python:
  `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`

The external launcher calls
`scripts\tools\th08_attach_no_life_decrement.py`. Windows tools under
`scripts/tools/` prepend their parent `scripts/` path before imports.

Rebuild ignored native libraries after C++ changes:

```bash
python3 scripts/tools/build_native_planner.py --target linux
python3 scripts/tools/build_native_planner.py --target windows
```

Use `TOUHOU_DISABLE_NATIVE_PLANNER=1` only for explicit NumPy/Python ablation.

## Test Commands

Focused local pipeline:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_touhou_control_local_pipeline_oracle.py'
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_th08_local_pipeline_certificate.py'
```

Quick suite:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

Bounded formal/performance profiles:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/audit_pipeline_formal_correctness.py \
  /tmp/pipeline-formal-quick.json
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_belief_pipeline_workspace.py \
  /tmp/belief-pipeline-quick.json
```

Semantic gate:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_semantic_differential.py \
  --profile gate --seed 0xce0132 --count 256 \
  --output /tmp/th08-semantic-gate.json
```

Run broad/unrestricted/capsule profiles only when their model/kernel changes
or evidence is being retained.

Windows UNC discovery must use the loader below; ordinary
`unittest -s <UNC>`, UNC `cmd.exe` `cd/pushd`, and a PowerShell-only `PSDrive`
do not produce an importable root:

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe -c \
  'import sys,unittest; root=r"\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08"; sys.path.insert(0,root+r"\scripts"); tests=root+r"\tests"; suite=unittest.TestLoader().discover(tests,pattern="test_*.py",top_level_dir=tests); result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(0 if result.wasSuccessful() else 1)'
```

Change only `pattern` for a focused Windows run.

## Physical Trial Commands

Do not start a physical run merely to validate a documentation checkpoint.
Use non-TTY WSL launch.

Practice:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat' \
  --stage 4a --status-seconds 15 --stall-timeout 120
```

Continuous Hard Route-2, leaving the accepted game alive for manual replay
save:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_full_route_agent.bat' \
  --difficulty hard --leave-game-running \
  --status-seconds 30 --stall-timeout 120
```

Omit `--leave-game-running` for identity-scoped automatic cleanup. The switch
never chooses save/no-save and cannot preserve a failed run. Route-2 practice
stages are `1 2 3 4a 5 6b`; 4B and 6A are route-locked.

Operational rules:

- never launch the supervisor with a PTY;
- WSL command return is not supervisor completion;
- avoid Windows console/process probes during active gameplay;
- stop the supervisor first and allow `finally` cleanup;
- release all keys before any identity-scoped process termination;
- require Final-B `terminal_unload` and later
  `termination_reason=route_complete`;
- record manual input, manual `Z`, foreground loss, reset tails, unexpected
  Bombs, and auto-confirm failure;
- never end a turn with a required game, supervisor, or daemon alive.

Monitor:

```bash
trace=$(ls -1t artifacts/runtime_reports/*unattended*.jsonl | head -n1)
PYTHONPATH=scripts python3 scripts/analysis/th08_longrun_status.py "$trace"
tail -n 1 "$trace"
```

## Common Traps

- Do not use REA.
- Do not equate implementation parity with physical correctness.
- Do not turn timeout, candidate exhaustion, or a restricted lower bound into
  unrestricted losing/optimality.
- Do not let hidden delay/cadence branches choose separate future actions.
- Do not reset pending delay on held/no-write input.
- Do not use manager frame or a short wall-time threshold as the sole physical
  input clock.
- Do not grant candidate, label, continuation, or supplemental shadow output
  live action authority.
- Do not share optional work with the authoritative publication critical path
  without measuring contention.
- Do not reuse labels across immutable versions.
- Do not tune one stage/spell into universal mechanics.
- Do not add tests that protect only formatting, help text, or schema plumbing.
- Do not confuse compact reports with replay-capable raw evidence.
- Do not stage raw traces, screenshots, native builds, caches, game
  executables, or credentials.
