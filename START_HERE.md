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
18. `notes/STATIONARY_WITNESS_WINDOWS_DELIVERY_CONTRACT_20260728.md`
19. `notes/STATIONARY_WITNESS_WINDOWS_DELIVERY_GATE_20260728.md`
20. `notes/TH08_FUTURE_BULLET_BIRTH_OBSERVATION_CONTRACT_20260728.md`
21. `notes/G5_CALLBACK_LOOKAHEAD_COMPLETENESS_CONTRACT_20260728.md`
22. `notes/G5_MATERIALIZATION_TAIL_ATTRIBUTION_CONTRACT_20260728.md`
23. `notes/G5_MATERIALIZATION_TAIL_PHYSICAL_ATTRIBUTION_20260728.md`
24. `notes/G5_CORRIDOR_COMPLETION_PRIORITY_EXPERIMENT_20260728.md`
25. `notes/G5_ECL_CONTROL_FLOW_FAIL_CLOSED_PERFORMANCE_CONTRACT_20260728.md`
26. `notes/G5_CAPTURE_ALIGNED_VM_LOCAL_SHADOW_CONTRACT_20260728.md`
27. `notes/G5_BIRTH_OBSERVER_MATCHED_PATH_PERFORMANCE_CONTRACT_20260728.md`
28. `notes/G5_REALIZED_BIRTH_TO_HIT_PROVENANCE_CONTRACT_20260728.md`
29. `notes/G5_DERIVED_PATTERN_SOURCE_SHADOW_CONTRACT_20260728.md`
30. `notes/G5_NONSPELL_MAIN_VM_SOURCE_SHADOW_CONTRACT_20260728.md`
31. `notes/G5_NONSPELL_MAIN_VM_STAGE5_RESULT_20260728.md`
32. `notes/G5_AUXILIARY_VM_RUNTIME_IMAGE_OBSERVATION_CONTRACT_20260728.md`
33. `notes/G5_AUXILIARY_POINTER_STAGE5_RESULT_20260728.md`
34. the relevant recent run note and counterexample rows before live work

Before trusting a result, verify that the physical problem, formal
recurrence, implementation, immutable version, and publication deadline still
describe the same decision. Python/C++ parity is not physical correctness.

## Exact Checkpoint

- Repository branch: `main`.
- The newest action-neutral G5 checkpoint is Stage-5 run
  `lunatic_route2_stage5_unattended_20260728_171633`, executed from parent
  `3adad09` plus the enclosing checkpoint changes. It completed 12,032
  decisions over frames `2..41630`, hard no-Bomb, with eight hits at
  `[12324, 14116, 24615, 25486, 30504, 33449, 36710, 40462]`,
  `route_complete`, exact key/process cleanup, and no residual process. All
  rows are strict schema 12 with stable enemy-prefix brackets, zero invalid
  main VMs, zero invalid auxiliary pointers, and zero added enemy-pool RPM.
  Non-null auxiliary contexts per capture are p50/p95/p99/max
  `4/26/32/34`; 56 of 57 unique heap addresses recur across different
  `(slot, auxiliary-index)` observations, so pointer value is not a stable
  source identity. The selected proposed Phase-B delivery is one bounded
  native compact batch with owner/pointer recheck. The 104-byte projection
  payload is p50/p95/p99/max `416/2704/3328/3536` bytes. Exact shipped
  runtime ECL byte identity remains pending; the normalization primitive has
  synthetic authority only. Density-report internal/file digests are
  `43f98f71...7c5c` / `0845f258...7fb3`; raw SHA-256 is
  `de697d66...8ec`. The live action path did not change, so the lower hit
  count is not a causal survival claim.
- The first-64 ordinary-enemy main-VM phase-A checkpoint is complete. The
  opt-in schema-v11 decoder reuses the existing contiguous enemy-prefix blob
  and issues no added enemy-pool RPM. Retained Stage-5 run
  `20260728_155426` completed 11,891 decisions over frames `1..41612` with
  11 hits, hard no-Bomb, `route_complete`, exact cleanup, and no residual
  process. It has 11,890 stable brackets, one capture-spanned bracket,
  138,255 valid VM rows, zero invalid active VMs, and 64 unique PCs.
  Physical decode p50/p95/p99/max is
  `0.1068/0.2384/0.3136/0.5379 ms`; combined observer p95 is
  `0.2029 ms`, narrowly failing the fixed `0.20 ms` limit while p99/max pass.
  This useful signal remains explicit opt-in and action-free rather than being
  rejected solely for the small performance miss.
- The modular offline join finds one unique complete affine mapping,
  `runtime_pc = 0x0B1D0048 + ecldata5_file_offset`, for all 64 PCs. Twenty
  exact captured opcode-`0x60` advances align one-to-one with 20 activation
  batches containing 260 bullets. IDA additionally proves that opcode `0x87`
  allocates one of four auxiliary VM contexts rooted at `enemy+0x3384` and
  schedules it after the main VM. The trace has 81 exact `0x87` advances;
  all align with activation support, covering 105 batches and 1,520 bullets.
  Runtime byte identity, exact operand/geometry lowering, slot-reuse
  exclusion, and hit causality remain unproved. CE-0162 makes exact runtime
  ECL identity plus bounded auxiliary-context observation the next source
  gate. The corrected source-join report digest is `106ef264...b4488`; raw SHA-256 is
  `8569d64d...3a7`.
- The G5 realized birth-to-hit gate is complete and action-free. Its modular
  streaming audit joins all 15 Stage-5 `124930` dossier candidates to exact
  native decision epochs and same-epoch slot generations. Four candidates are
  exact overlaps and eleven are nearest-only diagnostics. Three exact
  overlaps activated before their reported loss boundary; slot 1,295 at hit
  frame 14,043 activated in support `13868..13869`, four to five frames after
  loss, in a nonspell 30-bullet wave for which the active-spell-main-VM-only
  observer has no intent. The canonical slot-1,357 overlap instead activated
  161–162 frames before loss. This proves that future birth can become a
  physical overlap but is not the sole canonical explanation. The report is
  byte-stable at internal/file digests `4d774124...ff5c` /
  `7934ac27...d676`; Linux/Windows pass 876 tests. No forecast,
  counterfactual, or action authority is added.
- The first nonspell source hypothesis is now physically rejected under
  `G5_DERIVED_PATTERN_SOURCE_SHADOW_CONTRACT_20260728.md`. Lunatic Stage-5
  run `20260728_150827` completed 11,801 decisions over frames `2..42172`
  with 12 hits, hard no-Bomb, `route_complete`, exact cleanup, and no
  residual process. All schema-v10 source scans validated but returned zero
  ready-parent candidates, including reproduced 30-bullet waves at frames
  13861 and 13879. The tested predicate therefore cannot attribute the wave;
  between-capture transforms remain unresolved. Combined birth/source
  p95/p99/max `0.2633/0.4982/9.0368 ms` also fails the fixed gate. The run
  inherited `gil-released`, so its extreme native-call tail is not comparable
  to the accepted GIL-held B4 workload, but the second pass's roughly
  0.05-ms p95 cost is still ineligible. CE-0161 isolates the failed shadow
  behind `--trace-derived-pattern-sources`; ordinary birth tracing stays
  schema v9 and pays no added scan. The deterministic report/raw SHA-256 are
  `a08f1370...c9bda` / `9081e3ed...565b`.
  Isolated Linux/Windows source reports pass, native libraries build for both
  targets, and complete Linux/Windows discovery passes 889 tests.
- The next G5 source gate revalidates auxiliary call depth/saved-frame offsets,
  freezes a native compact-batch ABI and budget, proves scalar/native parity
  under churn/reuse/unreadable/max-density cases, and measures Windows timing
  before one action-neutral spell-107 physical trial. Separately capture and
  byte-compare one exact shipped Stage-5 runtime ECL image outside the issue
  boundary. Do not fuse or publish the zero-signal ready-parent class.
  Callbacks, deferred enemy state, sources outside the first 64 records, and
  non-ECL native sources remain later unresolved classes. Earlier viability
  preservation under CE-0158 and general performance work continue in
  parallel; roadmap candidates are not a ceiling.
- The latest harder-workload physical checkpoint is
  `lunatic_route2_stage5_unattended_20260728_133633`. It completed 13,304
  decisions over frames `1..44822` with 23 hits, hard no-Bomb, two successful
  automatic dialogue confirmations, `route_complete`, exact key release, and
  no residual game/controller/supervisor process. Its 1,879 diagnostic
  capsules are all readable. Capsule I/O explicitly contaminates timing, and
  the hit count is eight above the preceding run and 2.5 above the accepted
  historical median; different RNG, phase timing, density, and post-death
  resources forbid a causal regression claim.
- All 23 contacts followed global viability exhaustion. The exact loss
  episode containing the canonical first hit begins at frame 3752 and contact
  occurs at frame 4027, a 275-frame interval after 24 earlier recovered loss
  episodes. The G3/G4 audit selects exact decision/query roots
  `3750/3749 viable -> 3752/3751 losing`, completes both `36 x 36`
  portfolios, replays every worst path, and has zero scalar/native mismatch.
  At G4 the issued mask `0x55` retains 30 frames while best masks
  `0x10/0x11` retain 32; at G3 issued `0x85` retains 22 while
  `0x20/0x21` retain 32. Both roots are `model_unknown` from the first
  successor due uncovered future hazards. This is a finite-proxy
  discriminator, not a physical counterfactual or live ranking. CE-0158 stays
  open and the next hit-reduction gate returns to G5 causal future-hazard
  coverage.
- CE-0159 records a long-standing artifact defect exposed by this run:
  unreachable `lane=none` plans copied `-Infinity` into 9,104 raw decision
  rows and 98 compact lane transitions, which strict JSON readers reject.
  Future corridor traces serialize that sentinel as `null`; live JSONL and
  all compact supervisor/dossier boundaries now reject any other nonfinite
  value. The current raw trace remains immutable at its recorded SHA, while
  its derived summary/session were deterministically normalized. Linux and
  Windows pass 866 tests; representative strict-encoding median overhead is
  about `0.003/0.008 ms`. This code correction has no action authority and
  has not yet received a post-fix physical timing gate.
- The same Stage-5 run is a successful B4 transfer workload:
  observer p50/p95/p99/p99.9/max is
  `0.0973/0.1936/0.3387/0.5376/0.8346 ms` across all 13,326 rows, with zero
  over-budget samples and zero completed GC. This does not erase CE-0156 or
  close the failed Stage-4A maximum gate. The generic ECL projection gates
  pass all 4,871 callback rows under the explicit `core` workload profile;
  Stage-4A-only spell gates remain the default. Spell 115 retains 1,220
  `unsupported_control_flow` unknown rows and no incomplete prefix is
  lowered.
- The latest unchanged physical performance gate is
  `lunatic_route2_stage4a_unattended_20260728_121028`. It completed 14,066
  decisions with ten hits, hard no-Bomb, accepted route completion, and exact
  cleanup. The cycle-delta optimization moves observer p95 below the fixed
  limit (`0.1986 ms`) and p99 also passes (`0.3400 ms`), but materialization
  tails at frames 11969/38043 produce `8.3269/5.0455 ms` observations.
  Therefore B4 remains open on its `2.00 ms` maximum. No completed GC overlaps
  either tail; one has ordinary same-cohort cycles and the other has the
  run-wide maximum materialization cycles plus corridor
  `inflight -> done`. CE-0156 forbids claiming a physical pass or reviving
  the rejected priority intervention.
- The same run validates all 5,663 VM projections. Its static ECL replay
  proves a retained-file/runtime-image mismatch at frame 44212. CE-0157
  corrects the auditor so this first failure invalidates all later static
  mappings: 27 late spell-73 rows are conservatively excluded, no
  unknown-to-complete transition remains, and the all-row gate stays failed.
  Recovering those rows requires retained raw instruction bytes or immutable
  runtime image identity; live coverage and action authority are unchanged.
- The next validation-preserving materialization patch removes 36,549 nested
  copy-helper calls on the fixed profile, performs finite-flag conversion in
  one owned allocation, and retains all length/shape/code/read-only failures.
  Linux passes all 23 profiles. The first Windows report fails only the ABBA
  decode ratio at `1.05839`; two adjacent complete repeats pass at
  `1.01980/1.00674`. Profiler observer cumulative time improves
  `0.295 -> 0.275 s`, but Windows controller p95 is statistically flat.
  This deterministic work reduction is retained; it does not close B4.
- Latest G5 observation/performance checkpoints:
  `Reduce validated birth materialization work`,
  `Retain failed optimized B4 physical gate`,
  `Verify physical ECL loop transitions offline`,
  `Add exact offline ECL loop shadow`,
  `Validate ECL local projection physically`,
  `Capture ECL VM locals without widening authority`,
  `Define capture-aligned ECL local shadow`,
  `Retain physical ECL control-flow gate`,
  `Fail closed on hidden ECL control branches`,
  `Define fail-closed ECL control boundary`,
  `Implement corridor completion priority experiment`,
  `Define corridor completion priority experiment`,
  `Retain schema-v9 physical attribution`,
  `Implement schema-v9 tail attribution`,
  `Retain schema-v8 callback physical gate`,
  `Fail closed on incomplete ECL lookahead`,
  `617e03a Retain first GIL-held Stage 4 pass`,
  `62e2248 Test native birth calls with the GIL held`,
  `7333cc8 Retain native-call Stage 4 tail attribution`,
  `200c259 Attribute native bullet birth wall tails`,
  `e892863 Retain native Stage 4 birth tail failure`,
  `bc57168 Add exact native bullet birth extraction`,
  `efac80f Retain schema-v4 Stage 4 birth gate`,
  `e48cd65 Bound bullet birth trace flush latency`,
  `4eecd4a Retain schema-v3 Stage 4 birth gate`,
  `70077e2 Compact birth evidence and preserve ECL capture`,
  `449e01f Retain failed bullet birth physical gate`, and
  `35f3502 Reuse compact bullet birth observer scratch`, building on
  `9f5b37c Align deferred bullet emission state` and
  `360c79b Add deterministic bullet birth residual audit`. The schema-v2
  physical recheck `20260728_040144` completed Lunatic Stage 4A over frames
  `1..44215`, 14,642 decisions, 17 hits, hard no-Bomb, accepted artifacts,
  and cleanup. Exactly aligned deferred state was available on 5,723/5,780
  active-spell rows and yielded 1,642 timed sightings, physically closing the
  discarded-state omission CE-0144. Only 2,860/87,673 activation edges had
  one temporal main-VM match and all were in spell 69; CE-0145 retains the
  omitted-source/control-flow residual. Observer p95/p99/max improved to
  `0.4496/0.9314/10.2189 ms` but still failed the fixed gate, while previous
  emission p95/max was `1.2484/12.8322 ms`. Schema v3 now removes
  output-linear per-birth objects and repeated JSON keys without dropping
  evidence: Linux/Windows 592-birth observer p95 is `0.1704/0.1528 ms`,
  record-plus-JSON p95 is `0.7763/1.0727 ms`, and payload falls
  `160,077 -> 32,956` bytes. Enhanced per-phase analysis also found CE-0146:
  2,386 rows lost valid VM snapshots because a legal header-only ECL
  instruction caused a zero-byte RPM and one broad exception erased capture
  with classification. Zero payload is now local `b""`, and modular
  `th08_live.ecl_capture` preserves the snapshot while keeping callback
  events fail-closed. Linux/Windows quick suites pass `786/786` in
  `8.841/15.258 s`, with three Windows skips. Schema-v3 physical repeat
  `20260728_043724` completed frames `1..45742`, 15,009 decisions, 20 hits,
  hard no-Bomb, and cleanup. All 6,101 active-spell rows now classify and
  spell 61 adds 3,054 temporal matches; CE-0146 is physically closed.
  Observer p95/p99/max is still `0.3413/0.6625/10.6158 ms`, so B4 fails.
  CE-0147 also shows every spell-57 callback lookahead exhausting 256
  instructions without horizon coverage while its empty event list remains
  consumable. Schema v4 now replaces redundant per-evidence flush with
  error-immediate/same-iteration-decision bounded flush, records CPU/wall
  extraction separately, and uses a scalar gather up to 32 candidates.
  Fixed Linux/Windows 1/8/32-candidate p95 is
  `0.0578/0.0627/0.1038` and `0.0495/0.0790/0.0963 ms`. Schema-v4 physical
  run `20260728_050305` completed frames `2..44273`, 14,394 decisions,
  12 hits, hard no-Bomb, accepted artifacts, and cleanup. Removing the
  redundant flush reduced previous birth-record emit p95
  `1.1783 -> 0.1708 ms`, but observer wall p95/p99/max was still
  `0.2997/0.5772/10.2234 ms`, so B4 remains failed. Windows thread CPU
  samples were quantized in 15.625-ms steps and cannot replace the wall
  gate. A separate trace-only native library now performs one slot-order
  scan without changing the 46-symbol production ABI. Four Linux/Windows
  native tests cover 16 randomized full-pool generations, boundary/nonfinite
  cases, reset/validation, canonical record parity, and atomic capacity
  failure. CE-0148 records a rejected wrapper whose per-call ctypes
  allocations triggered a repeatable 5.409-ms cyclic-GC tail; caching the
  persistent blob view, pointers, and count storage removes it with GC still
  enabled. Final unpinned Linux/Windows full-density p95 is
  `0.0120/0.0109 ms`, 592-birth p95 is `0.0570/0.0452 ms`, all eight profile
  maxima are at most `0.4289/0.1433 ms`, and interleaved ratios are
  `0.931/0.930`. Trace schema v5 records the explicit `python`/`native`
  backend and residual-audit v3 rejects missing provenance. Complete
  Linux/Windows suites pass `792/792` in `8.826/15.449 s`, with three
  Windows skips. Explicit-native schema-v5 run `20260728_055104` then
  completed frames `2..45092`, 14,643 decisions, 13 hits, hard no-Bomb,
  accepted artifacts, and cleanup. All rows record native provenance with
  zero observation errors. Wall p50/p95/p99 improves to
  `0.0545/0.1393/0.2111 ms`, but p99.9/max is
  `2.3779/9.0498 ms`, so B4 still fails. Ten of sixteen samples above 2 ms
  have zero evidence and none is a large burst; CE-0149 requires separate
  native-call/materialization timing and overlapping-GC evidence without
  disabling GC, pinning the controller, or weakening the maximum. Callback
  incompleteness must also fail closed before Stage 5/6.
  Schema v6 now implements that attribution under
  `notes/G5_NATIVE_BIRTH_TAIL_ATTRIBUTION_CONTRACT_20260728.md`;
  residual-audit v4 validates reconciled segments and phase/generation GC
  counts. CE-0150 rejects the old block-ordered decode ratio after identical
  Windows runs flipped `1.077 -> 0.940`; ABBA-paired Linux and two adjacent
  Windows runs pass unpinned at `1.012/1.016/1.025`. All observer profiles
  and Linux/Windows `797/797` quick suites pass in `9.134/15.767 s`, with
  three Windows skips. Explicit-native schema-v6 attribution run
  `20260728_062321` completed Stage 4A over frames `1..45170`, 14,868
  decisions, 17 hits, hard no-Bomb, accepted artifacts, and cleanup.
  Observer p50/p95/p99/p99.9/max was
  `0.0648/0.1493/0.2245/2.1568/8.3514 ms`, so B4 again failed only its
  maximum. All 17 observations above 2 ms were dominated by the native-call
  interval; its p50/p95/p99/p99.9/max was
  `0.0365/0.0603/0.1125/2.1281/8.2585 ms`. Prepare, materialization, and
  controller-residual maxima were `0.0703/0.7076/0.2362 ms`, and all nine
  phase/generation GC completion totals were zero across the run. **Observed:**
  CE-0149 is a collection-free native-call wall tail, not a Python-copy or
  cyclic-GC tail. **Inferred:** release-GIL call-boundary scheduling is a
  plausible contributor; OS preemption is not directly observed. The next
  correction gate is an explicit GIL-held versus GIL-released call-boundary
  experiment under the same C++ recurrence, output, unpinned controller, GC,
  and wall limits. That experiment is now implemented with separate
  `CDLL`/`PyDLL` loaders and trace schema v7/residual-audit v5 provenance.
  Both modes are bit-exact to the independent Python oracle over 16
  full-pool generations. Unpinned Linux released/held profiles pass with
  full-density p95 `0.0119/0.0109 ms`, 592-birth p95
  `0.0598/0.0588 ms`, and decode ratios `1.0166/1.0293`; Windows passes at
  `0.0118/0.0098 ms`, `0.0465/0.0452 ms`, and `1.0382/1.0181`.
  Complete Linux/Windows suites pass `801/801` in `8.900/15.699 s`.
  One explicit `gil-held` Stage-4A diagnostic is eligible; two consecutive
  complete physical passes are required to close B4. The first held run
  `20260728_065316` is now one candidate pass: 13,896 schema-v7 held
  observations have p50/p95/p99/p99.9/max
  `0.0659/0.1475/0.2021/0.4001/1.0595 ms`; native-call maximum fell from the
  released run's `8.2585` to `0.5008 ms`, with no over-budget sample and no
  completed GC. It completed frames `2..43253`, 9 hits, hard no-Bomb,
  accepted artifacts, and cleanup. CE-0151 records an audit-v5 aggregation
  guard that initially validated schema v7 but omitted its diagnostics from
  the report; the raw fields were intact, `{6, 7}` aggregation and a
  fail-loud test now pass, the deterministic report was rebuilt, and complete
  Linux/Windows suites pass `801/801` in `9.202/15.761 s`. The second held
  run `20260728_070838` completed frames `2..45454`, 15,011 observations,
  15 hits, hard no-Bomb, accepted artifacts, and cleanup. Observation
  p50/p95/p99/p99.9/max was
  `0.0632/0.1420/0.1967/0.3999/0.9087 ms`; native-call maximum was
  `0.4384 ms`, with zero over-budget observations and zero completed GC.
  Together, the two consecutive held runs cover 28,907 observations and
  close the specific B4 observer-tail gate. This is a performance result,
  not a survival improvement: the 9/15-hit attempts are not controlled, and
  all 24 contacts followed global viability exhaustion. CE-0147 and
  first-successor `UNKNOWN` still block future-event/action authority and
  Stage 5/6 promotion.
  The CE-0147 correction now gives callback and birth-intent traversal an
  exact `COMPLETE`/`UNKNOWN` frame-support record. Only `complete_events`
  can reach velocity lowering; incomplete prefixes remain trace evidence,
  and the compatibility helper raises instead of returning one as a
  schedule. Trace schema v8/residual-audit v6 reject inconsistent callback
  or intent coverage. Re-auditing retained schema-v7 run `20260728_070838`
  labels 3,723 rows `legacy_declared_complete` and 2,405 rows
  `legacy_declared_unknown`; the latter were exposed through the old
  unchecked schedule interface. Of those incomplete rows, 975 contain tagged
  bullets, with a maximum of 1,367. Focused Ruff and complete Linux/Windows
  suites pass `806/806` in `9.046/15.657 s`, with three existing Windows
  skips. This closes the invalid prefix-consumption defect, not the unknown
  suffix: no conservative spatial envelope or repeated-state scheduler proof
  exists yet. Schema-v8 run `20260728_075455` now physically validates the
  corrected consumer over 14,903 rows and 6,089 active-main-VM joins:
  3,763 callback rows are complete and 2,326 are unknown, with exactly
  matching complete-lowered/incomplete-not-lowered counts. Spell 57 supplies
  1,313 instruction-limit unknowns; spell 73 supplies 1,013 repeated-state
  unknowns and 125 complete rows. There are 936 incomplete rows with tagged
  bullets, maximum 1,360. The run completed frames `1..45499`, 16 hits, hard
  no-Bomb, accepted artifacts, `route_complete`, and cleanup; all contacts
  follow global viability exhaustion.
  This semantic pass also exposes CE-0152 and reopens B4 performance
  regression status. Observation p50/p95/p99/p99.9/max is
  `0.0636/0.1448/0.2007/0.3858/8.9834 ms`. Its only over-budget row has 24
  evidence records and spends `8.9333 ms` in materialization while native
  call is `0.0335 ms`; no completed GC overlaps it, and adjacent 24-row
  materializations are at most `0.0741 ms`. Spell-57 ECL lookahead itself
  also costs p95/max `0.5460/10.3328 ms`.
  `G5_MATERIALIZATION_TAIL_ATTRIBUTION_CONTRACT_20260728.md` now fixes the
  next checkpoint: allocation-stable current-thread cycle deltas and
  lookup-only background-future endpoint states before another physical run
  or promotable Stage-5/6 claim. It authorizes telemetry only, not worker or
  copy intervention. That schema-v9/audit-v7 telemetry is now implemented:
  Windows uses a cached GIL-held `QueryThreadCycleTime` sampler, every native
  phase retains raw cycle deltas with fail-closed provenance, and the
  controller records lookup-only before/after states for its corridor,
  survival, and enemy futures. Both endpoint lookups are inside the existing
  observer wall interval. The retained overhead gates pass all eight native
  profiles on Linux/Windows; 592-birth p95/max is
  `0.0718/0.2150` and `0.0441/0.1388 ms`, while ABBA decode p95 ratios are
  `1.0401/1.0068`. Windows reports only
  `windows_query_thread_cycle_time`; Linux explicitly reports
  `unavailable_non_windows`. Complete Linux/Windows suites pass `812/812` in
  `9.709/15.434 s`, with three existing Windows skips. Audit v7
  deterministically re-audits the retained schema-v8 run without requiring
  unavailable historical cycles; its unchanged B4 maximum still fails.
  The planned gate was one explicit GIL-held schema-v9 Stage-4A attribution
  run. That accepted run `20260728_083433` is now complete over
  frames `1..43149`, 13,842 decisions, 12 hits, hard no-Bomb, route
  completion, artifact retention, and cleanup. All native rows have valid
  Windows cycle attribution. Observation p50/p95/p99/p99.9/max is
  `0.1001/0.2039/0.3454/0.5545/5.1274 ms`, so B4 remains failed.
  The only three ambiguous endpoint rows are all
  `corridor_future: inflight -> done`, and they are exactly the three largest
  materialization walls: `5.0415/4.2546/1.1657 ms`. The next-largest
  materialization is `0.4756 ms`; definite-overlap maximum is `0.4270 ms`.
  Two transition rows have ordinary-to-p95 same-bucket cycles, supporting
  descheduling/GIL handoff; the `4.2546 ms` row also has the run-wide maximum
  `646,576` materialization cycles, so attribution is mixed rather than a
  pure copy or pure scheduler result. All 12 hits follow global viability
  exhaustion and do not support a survival comparison. The next useful gate
  is now fixed by
  `G5_CORRIDOR_COMPLETION_PRIORITY_EXPERIMENT_20260728.md`: one explicit,
  default-off corridor-parent below-normal option using the already-tested
  solve seam. It preserves the four native workers and all recurrence/issue
  semantics, fails loud if priority is not applied, and rejects tail
  improvement that worsens publication age, queryability, support, action
  lag, or first-hit viability warning. Two consecutive complete physical
  passes are required. The option and its deterministic
  `th08-corridor-priority-audit-v1` are now implemented. It remains
  default-off, propagates explicitly through both supervisors, records
  requested/applied priority and the unchanged four-worker limit, and fails
  loud on an unapplied request. Re-auditing the normal-priority schema-v9
  baseline reproduces all retained delivery values exactly and fails only
  the expected application gate. Fresh Linux/Windows complete suites pass
  `820/820` in `8.943/16.230 s`, with three Windows skips. Fresh observer
  overhead/ABBA gates pass at Linux/Windows ratios
  `1.0232/1.0469`; no native source or 46-symbol ABI changed. One unrelated
  first Linux suite invocation reproduced the long-standing warm-cache
  sensitivity of a one-millisecond native deadline test. A separate
  test-only checkpoint enlarged the cold reachable region; 128/128 repeated
  deadline cases and fresh Linux/Windows `820/820` suites now pass in
  `9.488/16.010 s`. Priority-on run `20260728_092619` then completed frames
  `2..44999`, 14,649 decisions, 18 hits, hard no-Bomb, retention, and
  cleanup. All 1,900 solutions applied the request and unchanged four-worker
  limit. It is rejected: observer p95 `0.2049 ms` and expired-policy fraction
  `0.2472%` exceed their fixed limits, and no `inflight -> done` endpoint
  supplies the required completion witness. The lower `0.8925 ms` maximum is
  therefore non-attributable. All hits followed global-kernel exhaustion and
  the first retained positive `40/9`-frame viability/robust warnings. Do not
  run the second pass. B4 remains open; next analyze exact memoized/transfer
  summary callback traversal rather than another priority variant. IDA
  analysis then rejects naive memoization as the first step: spell 73 opcode
  `0x33` reads ECL variable `10050`, which is the current player/enemy
  Euclidean distance, while spell 57 opcode `0x05` depends on VM locals and
  RNG-derived loop state absent from the snapshot. The fixed next contract is
  `G5_ECL_CONTROL_FLOW_FAIL_CLOSED_PERFORMANCE_CONTRACT_20260728.md`: stop at
  the first unsupported transfer instead of spending the rest of the
  256-instruction cap on an unjustified fallthrough. This may shrink coverage
  and issue cost but cannot add callback or action authority. Dependency-
  complete transfer summaries remain a later gate. That correction is now
  implemented. Retained-trace replay finds CE-0154: 1,996 previously complete
  spell-61/65 horizon rows crossed unsupported `0x05/0x34` transfers.
  Across 5,788 exactly replayed rows, no unknown becomes complete and scanned
  instructions fall `563,466 -> 58,204` (`89.6704%`); spell 57 falls
  `344,320 -> 3,155`. Shipped representatives inspect `26/3` instructions
  for spell 57/73, and Linux/Windows p95 is
  `0.0223/0.0307` and `0.0039/0.0043 ms`. Full suites pass 823/823.
  Fifteen late transition rows are not byte-mappable to the retained decoded
  file, so the deterministic replay report deliberately fails its all-rows
  gate. Fresh normal-priority run `20260728_101804` now closes the live
  runtime scope without rewriting that historical limitation. It completed
  frames `1..43865`, 14,126 decisions, 13 hits, hard no-Bomb, route
  completion, retained artifacts, and cleanup. The deterministic live audit
  accounts for all 5,749 callback rows: 1,442 complete horizon schedules,
  4,307 `unsupported_control_flow` unknowns, zero legacy
  instruction-limit/repeated-state stops, and 25/25 valid phase-end rows.
  Spell 57 stops at control on all 1,308 rows with at most 26 instructions.
  The audit is byte-identical at SHA-256
  `e1d89da6cee5aced7a87187bde950a2d3fed2303292a366621134526bc963210`.
  The same run fails the unchanged observer p95 narrowly at
  `0.2018 > 0.2000 ms` despite max `0.7539 ms`, no completed GC, and no
  endpoint transition; B4 remains open. All 13 contacts follow global
  viability exhaustion, so the hit count is descriptive only. The next G5
  gate is a capture-aligned VM-local/control interpreter contract, not a
  spell shortcut or guessed transfer summary.
  That next phase-A boundary is now fixed in
  `G5_CAPTURE_ALIGNED_VM_LOCAL_SHADOW_CONTRACT_20260728.md`: extend the
  existing one-call VM capture from `0x40` to `0x68` bytes and retain raw
  locals only. IDA confirms `10036..10039` at context `+0x58..+0x64` and
  opcode `0x05` branches on the post-decrement lvalue. Call/return saves the
  full `0x228` context and remains unsupported. Phase A may not change live
  coverage. The projection is now implemented and Linux/Windows
  offline-validated: all 832 tests pass, the same-read/field-parity gates
  pass, and pure decode costs approximately 3.9/4.8 microseconds median on
  Linux/Windows. Fresh physical run `20260728_110438` now validates all
  5,615 projected callback rows and observes multiple `10036` values in
  spells 57/61/65 without changing fail-closed coverage. The native B4 p95 is
  still over budget at `0.2059 ms`. Proceed only to the independent offline
  scalar oracle and matched-path performance attribution; live promotion
  remains forbidden. Post-audit Linux/Windows suites pass 834 tests.
  The phase-B1 integer-loop shadow and structurally independent test oracle
  are now implemented under `scripts/th08_ecl_shadow/` and `tests/`.
  Synthetic counter, wrap, visited-state, and shipped spell-57 boundary tests
  pass. Float add/normalize remains unknown pending a rounding oracle; no
  live module imports the shadow. Complete Linux/Windows suites now pass 844
  tests. Retained replay of physical run `20260728_110438` now accounts for
  all 3,117 in-scope unknown spell-57/61/65 rows; the 1,008 dynamic spell-73
  rows remain explicitly excluded. It decodes every in-scope row, observes
  1,730 initial `0x05` rows, reduces them to 108 unique physical one-step
  cases, and agrees with the independent oracle with zero failures. No
  unknown row becomes a verified complete schedule. Two generations of the
  deterministic replay and fixture are byte-identical at SHA-256
  `b280467bb51ee2cc3c52343b8acf8fdcead5d4db46cbdc3f29192a68a8ae920f`
  and
  `6c34d09752abb7805c84e537b8df52ad24a1aea90614c8b5a2687d730d73ab3c`.
  Isolated one-step Linux/Windows p50 is approximately
  `0.0085/0.0101 ms`; this is an offline implementation baseline, not the
  open physical B4 observer boundary. Complete Linux/Windows suites pass 848
  tests, with three existing Windows skips. Next profile the matched live
  path and independently fix float32 add/normalization semantics before
  widening the shadow. Direct fire, RNG, dynamic state, calls, and
  interrupts remain unknown and live promotion remains forbidden.
  The parallel B4 checkpoint is now fixed in
  `G5_BIRTH_OBSERVER_MATCHED_PATH_PERFORMANCE_CONTRACT_20260728.md`.
  Regrouping the same physical rows shows zero/nonzero-evidence p95
  `0.1553/0.2516 ms` and no-known/definite-known-future-overlap p95
  `0.2015/0.2112 ms`. Windows profiling identifies non-allocating
  thread-cycle delta bookkeeping as the first narrow optimization candidate.
  The exact controller timing boundary, both future endpoint captures, GIL,
  GC, workers, and all observation records remain fixed. Benchmark schema v8
  now measures that exact controller wrapper with one persistent blob across
  15 birth/future profiles. All 23 combined profiles pass; the largest
  controller-path p95 is `0.06643/0.04872 ms` on Linux/Windows. This is only
  the offline implementation floor and cannot replace the fresh physical B4
  gate. The first production optimization now removes only generator/tuple
  work from exact Windows cycle-delta bookkeeping. Windows maximum
  controller-path p95 improves `0.04872 -> 0.04680 ms`, with an independent
  optimized repeat at `0.04410 ms`; Linux stays effectively flat
  `0.06643 -> 0.06603 ms`. All provenance and 23 profiles pass, as do 850
  tests. This is comparable to the physical `0.0059 ms` p95 miss but does not
  close B4 without a fresh unchanged normal-priority Stage-4A trace.
  See `notes/G5_BULLET_BIRTH_PHYSICAL_GATE_20260728.md` and
  `notes/G5_NATIVE_BULLET_BIRTH_EXTRACTION_CONTRACT_20260728.md`, plus
  `notes/G5_NATIVE_BIRTH_GIL_BOUNDARY_EXPERIMENT_20260728.md` and
  CE-0143/0144/0145/0146/0147/0148/0149/0150/0151/0152/0153/0154.
- Preceding G5 observation checkpoint:
  `98db592 Integrate trace-only bullet birth audit`, building on
  `52d0864 Add fail-closed ECL birth intent classifier`, `c3c5a83`, and
  `4260113`. `--trace-bullet-births` now constructs the pool-blob observer,
  reuses the active-spell boss main-VM snapshot and immutable instruction
  cache for an 80-frame intent classification, emits compact post-issue audit
  rows, and resets on every scene/sensor/action epoch boundary. It adds no
  RPM, planner field, Bomb, issue, coverage, or action authority. Direct-fire
  literals, dynamic parameters, aimed/RNG/deferred/current-pattern intents,
  pool/template/origin dependencies, and fail-closed control/source/emission
  boundaries have 15 focused tests; trace authority/alignment/error records
  have three. Linux/Windows quick suites pass `773/773` in `8.691/15.243 s`,
  with three Windows skips. The retained B1 performance remains p95
  `0.0318/0.0339 ms` and interleaved decode ratio `0.998/1.007`.
  The first shipped-runtime B4/B5 attempt is now retained as a failed gate
  above.
- Latest committed algorithmic checkpoint:
  `f8621bd Add cancellable stationary witness delivery benchmark`. A separate
  research-only DLL and modular newest-wins service now measure complete
  36-action internal stationary publications in the same Windows process.
  Numeric immutable path records and direct native output-buffer writes
  remove delivery overhead without changing the recurrence or production
  ABI. The one below-normal proposal worker can be pinned without changing
  process or authoritative-worker affinity. Linux/Windows quick suites pass
  `740/740` in `8.926/14.797 s`, with three Windows skips.
- Two consecutive fixed Windows gates pass with the proposal worker pinned to
  logical CPU 11, the highest logical CPU in Windows' maximum efficiency
  class. Complete-publication p95/max are `6.913/11.358` and
  `6.203/7.977 ms`; authoritative viability p95 ratios are `1.034/0.938` and
  throughput ratios are `0.929/0.961`. Cancellation ack p95 is
  `0.164/0.168 ms`; stale/partial publication is zero; Linux/Windows
  production exports remain exactly 46 symbols. The rejected unpinned-repeat
  and E-core variants remain retained. This permits only a separately
  reviewed default-off trace-only shadow; no consumer or action authority
  exists. See
  `notes/STATIONARY_WITNESS_WINDOWS_DELIVERY_GATE_20260728.md`.
- Post-fix physical CE-0141 gate
  `lunatic_route2_stage4a_unattended_20260728_020910` completed Lunatic Stage
  4A over frames `2..45659`, 15,260 decisions, 14 hits, hard no-Bomb,
  accepted artifacts, supervisor exit, and cleanup. All 15,069 canonical
  root/capsule joins passed with zero mixed roots, validation failures, or
  missing capsules. This physically closes the trace construction bug;
  future-event coverage remains `UNKNOWN` from the first successor and
  physical action authority remains none. Linux/Windows quick suites pass
  `741/741` in `8.850/14.854 s`, with three Windows skips. See
  `notes/G5_CE0141_PHYSICAL_RECHECK_20260728.md`.
- G5 bullet-birth work is now fixed by
  `notes/TH08_FUTURE_BULLET_BIRTH_OBSERVATION_CONTRACT_20260728.md`.
  B1 now reuses the persistent hostile-bullet pool capture to retain candidate
  native age, activation edges, timer regressions, capture support, and
  compact geometry with no additional RPM. B2's independent update-order
  fixture and B3's fail-closed active-spell main-VM intent classifier are
  complete; the default-off live trace seam is integrated. B4 physical
  correlation and B5 residual classification remain open. None of this can
  narrow the current first-successor `UNKNOWN` coverage slab.
- The preceding algorithmic checkpoint
  `d5866c4 Align hazard coverage with canonical query roots`. Physical Gate-5
  auditing found CE-0141: 1,613 of 14,599 available-query rows mixed a
  canonical `query_frame` root with coverage built from an earlier
  `manager_frame`. The trace-only builder now roots coverage at the canonical
  query frame. The G5 report retains exact failure counts with bounded
  samples instead of thousands of duplicate strings. No planner, issue, or
  action authority changed. Linux/Windows quick suites pass `732/732` in
  `8.757/14.621 s`, with three Windows skips; the later physical recheck
  passes.
- Physical Gate-5 workload
  `lunatic_route2_stage4a_unattended_20260728_005108` completed Lunatic Stage
  4A over frames `2..44411`, 14,804 decisions, ten hits, hard no-Bomb,
  accepted artifacts, supervisor exit, and cleanup. It retained 1,884
  capsules. The exact audit accepted 12,986 root/capsule joins, rejected the
  1,613 CE-0141 mixed roots, and found zero missing capsules. Physical
  decision/query/source `600/599/598` was Boolean-empty but completed all 36
  no-Bomb root actions with a 32-frame stationary witness and zero
  scalar/native mismatch. Future-event coverage is `UNKNOWN` from frame 600,
  so physical action authority remains none. The retained-artifact regression
  brings Linux/Windows quick suites to `733/733` in `8.581/14.794 s`, with
  three Windows skips. See
  `notes/G5_PHYSICAL_COMPLETE_MASK_CAPSULE_GATE_20260728.md`.
- The stationary-witness performance gate and its post-failure resource
  isolation variants are fixed in
  `notes/STATIONARY_WITNESS_WINDOWS_DELIVERY_CONTRACT_20260728.md`. CE-0142
  records a physical float32 equal-label nature tie: native and Python may
  choose different hidden pickup delays while both complete paths replay and
  root labels remain inside the declared tolerance.
- The preceding audit implementation checkpoint
  `48f7e56 Add exact complete-mask capsule audit`. The offline Gate-5 audit
  now reconstructs and digest-checks a physical 36-token complete-mask
  active/held/pending root, replays its exact hazard-coverage record, joins
  the capsule named by the same decision, completes all 36 no-Bomb root
  actions under the exact stationary-held continuation, replays every worst
  path, and checks scalar/native labels. Malformed slabs, JSONL, masks,
  roots, frames, provenance, and delay support fail closed. Linux quick tests
  pass `732/732` in `8.714/15.121 s` on Linux/Windows with three Windows
  platform skips; the focused new Windows file passes `6/6`. The physical
  join is now retained, while future-event coverage, delivery, and action
  authority remain open; see
  `notes/G5_COMPLETE_MASK_CAPSULE_JOIN_GATE_20260728.md`.
- The preceding native checkpoint
  `25d5f68 Add internal native stationary witness extraction`. Internal
  native extraction now retains the deterministic stationary worst path,
  including hidden remaining delay, recursive cadence, pickup/no-write,
  merged successor support, prefix bottleneck, nested labels, and failure or
  successor identity. Four randomized all-root-action cases plus pending
  no-write and unsafe-root cases match the independent Python witness on
  Linux and Windows. The production ABI remains exactly the checked-in 46
  symbols. Quick suites pass `726/726` on Linux in `9.635 s` and Windows in
  `14.362 s` with three platform skips. This remains internal/offline; see
  `notes/G3_NATIVE_STATIONARY_WITNESS_GATE_20260728.md`.
- The preceding retained-capsule checkpoint
  `ba4e66f Retain G3 stationary capsule witnesses` found that the first five
  eligible Boolean-empty exact roots in both retained Lunatic Stage 4A and Stage 6B
  contain all three restricted outcomes: full 32-frame feasibility, positive
  17/12-frame partial witnesses on unresolved roots, and no-positive
  stationary witnesses. Every portfolio completed all 17 root actions over
  all 17 singleton stationary continuations. Worst branches replay; selected
  witnesses match native guaranteed frames with margins inside `1e-5`; two
  report generations are byte-identical. CE-0140 rejects equating Boolean
  empty or stationary exhaustion with unrestricted exact losing. The
  44-line report entry point delegates to focused selection/validation,
  serialization, and workload modules. Quick suites pass `723/723` on Linux
  in `9.182 s` and Windows in `13.135 s` with three platform skips. This is
  exact only for the historical 17-movement-action capsule model and remains
  offline.
- The preceding G3 implementation checkpoint `5e48f3d Add exact stationary
  partial survival witnesses` owns the complete-root-action recurrence,
  immutable digests, deterministic worst path, and small-case scalar/native
  parity under `touhou_control/partial_witness/`.
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
all-root-action portfolio, small-case scalar/native parity, and a retained
Stage-4A/Stage-6B capsule report. CE-0140 proves that old Boolean-empty roots
can still contain full stationary witnesses; stationary zero-prefix roots
remain unrestricted-unresolved. Internal native worst-branch extraction now
passes full-path Linux/Windows parity without changing the public ABI. The
  exact complete-mask capsule audit now retains a joined Stage-4A workload.
  It found and rejected CE-0141 mixed root frames; construction and its
  physical recheck are now complete. The next useful gate keeps unknown
  future events fail closed while adding event coverage one class at a time.
  Work should:

1. keep the native G3 extractor internal until exact complete-mask,
   coverage, delivery, and separately reviewed ABI/publication gates pass;
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
incomplete sensing. The schema-v2 birth trace now exposes timed intent, but
84,740/87,673 Stage-4A activation edges remain temporally unmatched and the
observer still fails its retained physical timing gate. The columnar
implementation passes isolated extraction and per-phase diagnostics exposed
the header-only ECL capture bug. The schema-v3 repeat closes that capture loss
but still fails timing and exposes incomplete instruction-limit callback
coverage. Fix those boundaries and repeat the unchanged Stage-4A gate before
adding source topology or proposing a future-hazard envelope.

The retained Stage-5 realized-provenance audit now narrows that open boundary
without changing action authority. Across all 15 hits in `20260728_124930`,
four dossier candidates are exact observed overlaps and eleven are
nearest-only. Three exact-overlap slot generations activated before or at
their reported loss, including the canonical first hit. One 30-bullet
nonspell wave activated strictly after loss: slot 1295 has native support
`13868..13869`, after loss frame 13864, and later overlaps exactly at frame
14043. The trace has no captured intent for that wave and the current observer
scope excludes nonspell source topology. This is observed evidence for a
missing source class, not evidence that every hit is caused by future birth or
that a containing forecast is complete. Contract nonspell source identity and
its observation deadline before extending the live observer; continue earlier
viability preservation in parallel.

Ordinary main-source topology and zero-read auxiliary-pointer phase A are now
complete. Main-only coverage is structurally incomplete, auxiliary pointer
identity is physically unstable across slot/index reuse, and exact shipped
runtime bytes plus coherent auxiliary VM state remain unavailable. The next
P1 gate is therefore the bounded native compact batch and one-shot runtime
image comparison described by
`G5_AUXILIARY_VM_RUNTIME_IMAGE_OBSERVATION_CONTRACT_20260728.md`, not a
planner envelope. Unknown contexts remain unresolved source branches.

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
- Callback and birth-intent lookahead completeness:
  `notes/G5_CALLBACK_LOOKAHEAD_COMPLETENESS_CONTRACT_20260728.md`
- GIL-held materialization-tail attribution:
  `notes/G5_MATERIALIZATION_TAIL_ATTRIBUTION_CONTRACT_20260728.md`
- First-loss exact-root selection and restricted G3/G4 experiment:
  `notes/G3_G4_FIRST_LOSS_CAPSULE_EXPERIMENT_CONTRACT_20260728.md`
- Realized activation-to-hit provenance:
  `notes/G5_REALIZED_BIRTH_TO_HIT_PROVENANCE_CONTRACT_20260728.md`
- Generated differential:
  `notes/TH08_SEMANTIC_DIFFERENTIAL_FUZZER_CONTRACT_20260726.md`

Relevant durable failures include CE-0108, CE-0109, CE-0111, CE-0118,
CE-0120 through CE-0125, and CE-0127 through CE-0134. Historical notes do not
override the authority table above.

## Retained Workloads

| Workload | Bundle | Purpose |
| --- | --- | --- |
| Lunatic Route-2 Stage 4A | `100451`, `103856` | CE-0120/0121 canonical transition evidence and replay floor. |
| Lunatic Route-2 Stage 5 | `124930`, `155426`, `171633` | Birth provenance, ordinary main/auxiliary source mapping, and newest schema-12 pointer-density gate. |
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
- `artifacts/benchmarks/derived_pattern_source_observer_native_linux_20260728.json`
- `artifacts/benchmarks/derived_pattern_source_observer_native_windows_20260728.json`
- `artifacts/benchmarks/g5_auxiliary_context_pointer_inventory_linux_20260728.json`
- `artifacts/benchmarks/g5_auxiliary_context_pointer_inventory_windows_20260728.json`
- `artifacts/viability_audit/g5_derived_source_stage5_20260728_150827.json`
- `artifacts/viability_audit/g5_auxiliary_pointer_density_stage5_20260728_171633.json`

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
python3 scripts/tools/build_native_bullet_birth_trace.py --target all
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

The current explicit trace-only native birth-observer gate adds:

```bash
  --trace-bullet-births --bullet-birth-backend native \
  --bullet-birth-native-call-mode gil-held
```

Do not infer this backend from library availability; schema-v5 provenance and
the physical gate require the explicit selector. The accepted B4 comparison
boundary is GIL-held; the parser default remains GIL-released for historical
compatibility and must not be inherited by a B4 experiment.

The rejected derived-parent experiment additionally requires:

```bash
  --trace-derived-pattern-sources
```

It emits schema v10 and is retained only for reproduction. Ordinary
birth-observer runs omit this flag, remain schema v9, and do not pay the
second pool scan.

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
