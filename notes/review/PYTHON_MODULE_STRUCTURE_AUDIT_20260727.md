# TH08 Python Module Structure Audit

Date: 2026-07-27

Status: structural checkpoint audit; no model or strategy promotion

## Scope And Evidence Boundary

This audit records the Python decomposition performed after
`CONSOLIDATED_RESEARCH_AND_REFACTOR_ROADMAP_20260727.md`, the remaining
coupling, and the order for later structural work.

- **Observed:** the changes through the current decision-control trace
  extraction preserve the quick-suite result: `695/695` on Linux and Windows
  with three existing Windows platform skips.
- **Observed:** deterministic old/new comparisons preserved:
  144 semantic-case payloads plus one shrink result, seven hotkey launch
  contracts, full-route parser/retention behavior, all 23 public ECL symbols,
  and five complete local-planner decisions after timing fields were removed.
- **Observed:** the post-extraction Windows physical smoke
  `hard_route2_stage1_unattended_20260727_144128` completed Hard Stage 1 with
  7,502 decisions over frames `1..20768`, zero hits, zero Bomb input, accepted
  terminal unload, artifact materialization, supervisor completion, and no
  residual game/controller process.
- **Observed:** the next Windows physical retention smoke
  `hard_route2_stage1_unattended_20260727_173735` completed Hard Stage 1 with
  7,680 decisions over frames `1..20950`, zero hits, zero Bomb input,
  accepted terminal unload, route completion, compact artifact
  materialization, supervisor completion, and no residual process.
- **Observed:** after removing the characterized inline corridor serializer,
  Windows smoke `hard_route2_stage1_unattended_20260727_175715` completed
  Hard Stage 1 with 7,305 decisions, zero Bomb input, accepted route
  completion, artifact materialization, and no residual process. Its 7,263
  corridor records had zero required-field omissions. It took one hit at
  frame 6,385 after global-kernel exhaustion and is not a clean survival
  pass.
- **Observed:** after removing the characterized candidate-verifier trace
  path, Windows smoke `hard_route2_stage1_unattended_20260727_181119`
  completed Hard Stage 1 with 7,686 decisions, zero Bomb input, accepted
  route completion, artifact materialization, and no residual process. The
  default workload had candidate shadow disabled, so deterministic tests
  retain that schema branch. The run took one hit at frame 2,043 after
  global-kernel exhaustion and is not a clean survival pass.
- **Observed:** after removing inline decision-control trace fields, Windows
  smoke `hard_route2_stage1_unattended_20260727_182434` completed Hard Stage 1
  over frames `2..20663` with 7,557 decisions, zero hits, zero Bomb input,
  accepted route completion, artifact materialization, and no residual
  process. Streaming validation found zero required control-field omissions.
- **Observed:** after removing inline sensing fields, high-pressure Windows
  smoke `hard_route2_stage4a_unattended_20260727_183640` completed Hard Stage
  4A over frames `2..45392` with 15,122 decisions, maximum 1,072 bullets, zero
  Bomb input, accepted route completion, artifact materialization, and no
  residual process. All 18 required sensing field groups were present on
  every decision. Eight native hits make this survival-failure evidence, not
  a clean pass.
- **Observed:** post-native-split Lunatic Stage-4A retention
  `lunatic_route2_stage4a_unattended_20260727_210928` completed 15,110
  decisions over frames `2..45549`, reached 1,528 bullets, retained native
  decode/hazard/beam execution, passed hard no-Bomb, materialized accepted
  compact artifacts, and left no residual game/controller process. Its 22
  hits are CE-0139 physical-model evidence, not a structural gate failure:
  the native decomposition remained operational, while the canonical contact
  occurred inside a hazard slab already declared unknown.
- **Observed:** post-native-split Lunatic Stage-5 retention
  `lunatic_route2_stage5_unattended_20260727_212624` completed 12,770
  decisions over frames `2..41508`, reached 1,533 bullets, passed hard
  no-Bomb, materialized accepted artifacts, and left no residual process.
  The eight CE-0137 hits remain model/recovery failures; the completed native
  backends and lifecycle provide structural retention under a second
  high-pressure workload.
- **Observed:** post-native-split Lunatic Stage-6B retention
  `lunatic_route2_stage6b_unattended_20260727_213748` completed 22,430
  decisions over frames `2..73670`, reached 1,536 bullets and 245 lasers,
  passed hard no-Bomb, materialized accepted artifacts, and left no residual
  process. The long mixed-hazard workload retained native geometry/local/
  viability/pipeline execution and phase transitions. Sixteen CE-0138 hits,
  including two exact laser overlaps and one multi-hazard overlap, remain
  physical-model/recovery evidence rather than structural acceptance.
- **Observed:** after extracting the fresh enemy-prefix issue stage, Lunatic
  Stage-4A run `lunatic_route2_stage4a_unattended_20260727_220330` completed
  13,295 decisions over frames `2..41645`, reached 1,362 bullets, passed hard
  no-Bomb, materialized accepted artifacts, and left no residual process.
  Its 13,295 issue observations contained 2,178 changes and exactly 2,178
  recertifications, with 39 overrides and zero silent outside-global
  selections. Seven CE-0136 hits remain survival evidence, not a structural
  regression.
- **Observed:** after extracting issue-time deadline and post-hit input
  overrides, Lunatic Stage-5 run
  `lunatic_route2_stage5_unattended_20260727_224146` completed 13,953
  decisions over frames `1..43371`, reached 1,529 bullets, passed hard
  no-Bomb, materialized accepted artifacts, and left no residual process.
  Its 2,419 changed issue observations produced exactly 2,419
  recertifications, 58 overrides, and zero silent outside-global selections.
  The 13 CE-0137 hits all followed global-kernel exhaustion and remain
  survival evidence rather than a structural regression.
- **Observed:** shared dossier death-attribution checkpoint `8149262` passes
  `711/711` quick tests on Linux in `8.795 s` and Windows in `12.688 s` with
  three platform skips. A complete Stage-5 replay over the retained
  548,614,220-byte trace produced byte-identical JSON, Markdown, death CSV,
  and regression JSON before and after extraction.
- **Observed:** renderer checkpoint `1cd3a9c` passes a fresh `713/713` Linux
  quick suite in `8.409 s` and Windows in `12.383 s` with three platform
  skips. Full-run/practice renderer ownership tests pass `2/2`; the complete
  Stage-5 output remains byte-identical, and the retained full-run
  Markdown/CSV rendering retains its exact pre-extraction hashes. The first
  Linux full run repeated the recorded 1-ms cold-prewarm deadline flake;
  focused `5/5` and the fresh unmodified full run passed.
- **Workload decision:** Stage 1 remains sufficient for lifecycle, cleanup,
  and trace-schema changes. Subsequent planner, recurrence, clearance, or
  native compute checkpoints use Hard Stage 4A as the primary focused
  physical gate because its retained roots exercise dense geometry, kernel
  exhaustion, and delivery. Stage 6B or the full route remains reserved for
  late-stage resource, clock, or transition claims.
- **Inferred:** passing parity and physical lifecycle gates establishes
  implementation preservation for the exercised workloads. It does not prove
  physical-model validity, global optimality, or route acceptance.

## Completed Decomposition

### Live controller

The public `scripts/th08_live_dodge_agent.py` is now a 22-line compatibility
and composition entry point. The live package owns narrow modules for:

- session and resource ownership;
- native sensing and input issue boundaries;
- policy and scene-clock coordination;
- trace publication;
- sensing value models;
- bullet, laser, item, and enemy decoding;
- the complete local-planner pass.

`scripts/th08_live/planner_pass.py` owns the causal local pass and receives
controller-owned backends, constants, and hazard/certificate callbacks through
`PlannerPassDependencies`. The controller wrapper constructs this dependency
object for every pass, so existing monkey-patch seams resolve current values
instead of stale import-time bindings.

The earlier extraction reduced `scripts/th08_live/controller.py` from roughly
8,000 lines to 6,566 lines. Validated stage contracts temporarily raised it
to 6,614 lines. Extracting the characterized corridor trace builder reduces
the controller to 6,126 lines; extracting candidate-verifier trace ownership
reduces it to 5,817 lines, and extracting decision-control trace fields
reduces it to 5,594 lines. Extracting sensing trace fields reduces the current
controller to 5,411 lines; extracting timing and optional-hazard trace fields
reduced it to 5,377 lines. Movement contracts/geometry, local hazard
projection, pipeline certificates, and local objective extraction reduce the
controller to 4,190 lines. Extracting the fresh enemy-prefix issue stage
reduces the controller to 4,181 lines while replacing an inline
sensor/recertification transaction with a typed, independently tested
boundary. Extracting the ordered deadline and post-hit input overrides reduces
the current controller to 4,168 lines. The dominant block remains
`_run_live_session`.

`scripts/th08_live/iteration.py` now defines and the live loop consumes:

- `CapturedIteration`: exact source/snapshot/hazard/delay identity and decoded
  physical inputs;
- `ServiceUpdate`: active/pending corridor publications for one context;
- `PublishedGuidance`: lookup-only policy result tied to that capture;
- `FreshIssueResult`: proposal, fresh guard, deadline alignment, dispatch, and
  timing tied to the same physical version.

The local planner reads the captured contract, and controller actuator state
is updated from the fresh-issue contract. Mutable worker, sensor, process,
trace, and lifecycle ownership remains in the controller.

### Runtime and automation

- `th08_runtime_agent.py` is a 20-line facade. `th08_runtime/` separates
  composition, verified addresses, sensing, Win32/process access, and physical
  input.
- `th08_practice_supervisor.py` is a 20-line facade.
  `th08_automation/practice_*` separates menu contracts, native menu state,
  Windows process/window operations, monitoring, artifacts, and orchestration.
- `th08_full_route_supervisor.py` is a 13-line facade.
  `th08_automation/full_route_*` separates native menu operations, evidence
  materialization, and trial orchestration.
- `th08_agent_hotkey.py` is a 13-line facade.
  `agent_contract.py` owns pure launch/summary contracts and
  `agent_hotkey.py` owns the Windows lifecycle.

### Offline semantic and ECL tools

- `th08_semantic_cases.py` is a 21-line facade.
  `th08_semantics/` separates the canonical replay schema, deterministic
  generation, and deterministic shrinking.
- `th08_ecl.py` is a 13-line facade.
  `th08_ecl_tool/` separates binary model/parser, semantic decoding/listing,
  catalogs/reports, and CLI composition.

### Offline dossier ingestion

- `analysis/dossier/trace_reader.py` owns whole-file SHA-256 provenance,
  streaming JSONL parse-error handling, run-trace compaction, and practice
  epoch/scope selection.
- `analysis/dossier/schema.py` owns the shared compact-decision schema
  lowering.
- `analysis/dossier/statistics.py` owns the historical floor-indexed p95 and
  resource-range conventions.
- `analysis/dossier/attribution.py` owns physical-contact witnesses, spell
  attribution, warning predicates, cause classification, death-ledger
  construction, and death clustering.
- `analysis/dossier/full_run_render.py` and `practice_render.py` separately
  own the two stable Markdown and death-CSV schemas.
- `analysis/th08_run_dossier.py` and
  `analysis/th08_practice_dossier.py` retain compatibility aliases for their
  former private reader/schema/statistics imports; the full-run entry point
  additionally preserves its former attribution imports as exact aliases.
  Aggregation, validation, regression composition, and CLI I/O remain in the
  entry modules for later behavior-preserving checkpoints.

Checkpoint `aa9358e` reduced the entry modules from 2,451/2,307 lines to
2,134/2,058 lines. A Windows/UNC regeneration from the retained 421,171,745-
byte Stage-4A trace matched the existing JSON, Markdown, deaths CSV, and
regression JSON byte for byte.
Checkpoint `8149262` then reduced the full-run entry point to 1,305 lines and
removed practice-to-full-run coupling for death semantics. A complete
Stage-5 replay retained all four outputs byte for byte.
Checkpoint `1cd3a9c` moved stable rendering into separate 501/621-line owners,
reducing the entry points to 815/1,449 lines while retaining complete output
and compatibility-alias parity.

All compatibility facades preserve the historical import surface. The
runtime, practice, full-route, hotkey, ECL, and live facades alias the
implementation module where module-level patch identity matters.

## Remaining Long Modules: Decision

| Module | Lines | Decision | Reason |
| --- | ---: | --- | --- |
| `th08_live/controller.py` | 4,168 | continue through stage contracts | `_run_live_session` still combines scene lifecycle, capture, service mutation, action alignment/dispatch, and outer composition; immutable handoffs plus pure trace, movement, hazard, certificate, objective, fresh-enemy issue, and input-override modules are live. |
| `th08_live/planner_pass.py` | 320 | staged split complete | Prepare/orchestration only; shared contracts, baseline, supplemental lifecycle, and final selection/assembly have dedicated modules. |
| `th08_live/planner_pass_supplemental.py` | 755 | retain through finalization gate | Cohesive pre-submit/search/exact-version lookup/fallback/terminal-label lifecycle; split native job construction from search only if later work makes either responsibility change independently. |
| `th08_live/planner_pass_finalize.py` | 587 | retain | One selection/assembly responsibility: endpoint rank, robust override, pre-loss admission, damage shadow, decision assembly, and relaxed retry. |
| `analysis/th08_run_dossier.py` | 815 | retain entry composition | Reader, schema, statistics, attribution, and rendering are extracted; the remaining module owns full-run aggregation, validation, regression assembly, and CLI I/O. |
| `analysis/th08_practice_dossier.py` | 1,449 | continue shared aggregation checkpoints | Shared ingestion, attribution, and rendering are complete; the entry still owns many independent timing/control summaries plus dossier/regression composition. |
| `th08_automation/practice_supervisor.py` | 683 | retain orchestration | Resource/process/menu/monitor/artifact logic is already behind narrow modules; the remaining file is composition and lifecycle flow. |
| `th08_corridor_adapter.py` | 691 | retain; watch growth | This is the TH08-specific hazard-lowering and control-spec adapter required by the workspace boundary. Its dependencies point inward to game-neutral control code. |
| `th08_corridor_runtime.py` | 643 | retain; watch growth | It is a cohesive publication/query lifecycle for corridor artifacts. A split is warranted only if candidate-verifier and prewarm lifecycles diverge further. |
| `th08_item_model.py` | 542 | retain | It is a deterministic item state/resource model with one domain responsibility. |
| `th08_simulator.py` | 503 | retain | It composes deterministic update-order executors; splitting each manager step would add navigation without reducing coupling. |

Line count alone is not a refactor criterion. A split must create a stable
contract, isolate ownership or side effects, or make an independently testable
semantic unit.

## Repository-Wide Long-Module Inventory

The 2026-07-27 measured inventory separates entry points from implementation;
small facades are not evidence that the underlying composition has been
decomposed.

### Live and game-neutral control

| Module | Lines | Decision |
| --- | ---: | --- |
| `th08_live_dodge_agent.py` | 22 | keep facade |
| `th08_live/controller.py` | 4,168 | P0 staged extraction through iteration contracts |
| `th08_live/planner_pass.py` | 320 | staged split complete |
| `touhou_control/query_survival.py` | 80 | compatibility facade; focused scalar/root/workspace/dispatch/problem modules complete |
| `touhou_control/query_survival_types.py` | 140 | retain public contracts |
| `touhou_control/viability.py` | 29 | compatibility facade; builders/policy/transitions/types own implementation |
| `touhou_control/native/local.py` | 54 | compatibility facade; ABI/sensing/reducers/supplemental modules own implementation |
| `touhou_control/native/viability.py` | 779 | P2 split only with matching C ABI ownership |
| `touhou_control/native/belief.py` | 549 | P2 split only with matching C ABI ownership |
| `touhou_control/native/pipeline.py` | 464 | retain for now |
| `touhou_control/corridor/clearance.py` | 731 | P2 split scalar geometry/packing/backend dispatch |

### TH08-specific Python

`th08_corridor_adapter.py` (691), `th08_corridor_runtime.py` (643),
`th08_item_model.py` (542), and `th08_simulator.py` (503) remain cohesive at
their current game-adapter or deterministic-model boundaries. The next band—
`th08_route_manifest.py` (467), `th08_ecl_runtime.py` (408), `th08_sht.py`
(396), `th08_timeline_model.py` (389), `th08_laser_model.py` (362),
`th08_route2_player_runtime.py` (354), `th08_bullet_transform_model.py` (341),
`th08_pbgz.py` (334), and `th08_ecl_flow.py` (333)—is review-on-change, not an
automatic split queue. Binary formats, one deterministic state machine, or one
game-specific adapter can legitimately be several hundred lines.

The compatibility entry points requested in this review are already small:
`corridor_planner.py` is 169 lines and `th08_live_dodge_agent.py` is 22 lines.
Their heavy implementations are the modules listed above.

### Offline analysis

`analysis/th08_run_dossier.py` (815) is now a reasonable full-run aggregation
and entry module. `analysis/th08_practice_dossier.py` (1,449) remains the
highest-value low-authority split. Shared reader, provenance, scope, compact
schema, stable statistics, complete death/cause attribution, and rendering
ownership is complete. Next group independently testable practice
timing/sensor/control summaries without changing their numeric conventions.
Other analysis/benchmark programs
above roughly 800 lines should move shared readers/statistics/renderers into
`analysis/dossier/` or benchmark helpers, while their executable files remain
thin explicit entry points.

### Native

The original `native/robust_viability_kernel.cpp` concern is structurally
closed: it is a two-line compatibility translation unit. The remaining long
implementation units are:

| Module | Lines | Next seam |
| --- | ---: | --- |
| `pipeline/belief_workspace.cpp` | 2,171 | state identity / recurrence / certificates / current workspace ABI |
| `pipeline/belief_compat.cpp` | 498 | cohesive legacy create/query/upper implementation adapters |
| `pipeline/direct_workspace.cpp` | 1,352 | transition build / solve / resume / current workspace ABI |
| `pipeline/direct_compat.cpp` | 82 | legacy v1 create/query implementation adapters |
| `viability/boolean.cpp` | 354 | Boolean/terminal viability induction |
| `viability/value.cpp` | 508 | signed safety value and best-action policy |
| `viability/survival.cpp` | 362 | survival-frame/bottleneck label induction |
| `viability/workers.cpp` | 41 | thread-local worker-limit ownership |
| `local/hazards.cpp` | 399 | cohesive local bullet/laser/body hazard query |
| `local/bullet_decode.cpp` | 196 | cohesive packed native-pool decoder |
| `local/beam_reduce.cpp` | 573 | baseline/supplemental quantized beam reduction |
| `geometry/clearance_volume.cpp` | 314 | full bullet/segment clearance volume |
| `geometry/segment_trajectory.cpp` | 225 | segment trajectory in-place lowering |
| `geometry/aabb_trajectory.cpp` | 182 | AABB trajectory in-place lowering |
| `geometry/piecewise_aabb.cpp` | 233 | piecewise-event AABB lowering |
| `abi/direct_pipeline_abi.cpp` | 242 | direct workspace exported family |
| `abi/belief_pipeline_abi.cpp` | 633 | belief workspace exported family |
| `abi/query_local_abi.cpp` | 69 | one-shot query-local export |
| `internal/abi_impl.hpp` | 6 | compatibility include facade |
| `internal/geometry_impl.hpp` | 102 | geometry implementation declarations |
| `internal/local_impl.hpp` | 165 | local sensing/beam/workspace declarations |
| `internal/pipeline_impl.hpp` | 467 | direct/belief/query-local declarations |
| `internal/viability_impl.hpp` | 139 | viability/value/survival declarations |
| `local/supplemental_workspace.cpp` | 804 | workspace lifecycle / search / result packing |

Native splits must keep the checked-in explicit source list, exact exported
symbol manifest, status/error behavior, Python/C++ parity, and Windows/Linux
build gates. Line movement alone is not an accepted native checkpoint.

Checkpoint `a0a7afb` consolidates the direct v1 and belief 32-bit v2 adapters
behind the current workspace implementations. A narrow internal action-count
predicate preserves the belief v2 rejection of workspaces wider than 32
actions without exposing the private recurrence class. Both release targets,
the exact 46-symbol manifest, legacy direct v1 and belief v2 calls, independent
belief-oracle parity, and the Linux/Windows quick suites pass. The next native
split should target a behavior-owning transition/solve boundary; do not move
the complete class definition into a large header merely to lower one file's
line count.

## Next Live-Session Contract

Do not move `_run_live_session` wholesale into another 3,500-line file. First
introduce an explicit iteration state and stage results while keeping the
physical-frame contract unchanged.

The structural sequence and current status are:

1. Add immutable `CapturedIteration`: **implemented and consumed**.
   observed game state, source/snapshot frames, player, pools, scene identity,
   input clock, and capture timings.
2. Add `ServiceUpdate`: **implemented and consumed**.
   completed corridor/enemy/candidate/prewarm results and exact policy version.
3. Add `PublishedGuidance`: **implemented and consumed**.
   lookup-only exact-version guidance and declared miss/fallback reason.
4. Reuse `LocalProposal` as the local planning output; do not place fresh
   issue observations in it.
5. Add `FreshIssueResult` around `IssueTransaction`: **implemented and
   consumed at the outer physical dispatch boundary**. Fresh enemy-prefix
   capture, aligned change detection, and conditional recertification now
   live behind `th08_live.fresh_issue`; deadline and post-hit mask overrides
   now live behind `th08_live.issue_overrides`. Action alignment, physical
   send/no-write, and actuator-state mutation remain the next bounded
   extraction.
   fresh enemy prefix, recertification, selected action, send/no-write result,
   issue frame, and deadline status.
6. Build trace records from those immutable stage outputs after the issue
   transaction: **corridor subrecord implemented and consumed**. One
   checkpoint compared the full historical inline record with the pure
   builder; the next removed the inline path. Candidate-verifier trace
   followed the same characterization/removal sequence and is now consumed.
   Decision-control and sensing fields completed the same
   characterization/removal sequence and are now consumed. Timing and
   optional detailed-hazard fields also completed that sequence and are
   consumed after issue. Outer record composition remains controller-owned.

The bounded iteration then becomes:

```text
capture
-> update services/epoch
-> lookup immutable publication
-> local proposal
-> fresh issue transaction
-> send or no-write
-> enqueue trace
```

Each extraction checkpoint must preserve:

- one explicit source/snapshot/issue frame contract;
- exact-version publication lookup only;
- no cold expansion on the issue thread;
- active/held/pending no-write semantics;
- controller cadence and delay support;
- foreground, executable, route, scene, and no-Bomb guards;
- newest-version-first cancellation and single resource ownership;
- all exception/stop key-release paths;
- trace field parity.

After each issue-path extraction, run focused Linux tests, the full Linux and
Windows quick suites, deterministic retained-case parity, and a supervised
Windows physical retention workload proportional to the changed authority.
Stage 1 remains a cheap lifecycle smoke; planner, hazard, viability, and
native checkpoints use Stage 4A, Stage 5, or Stage 6B before declaring the R5
exit gate retained.

## Dossier Tool Follow-Up

Shared offline modules under `scripts/analysis/dossier/` now have this status:

- `trace_reader.py`: **implemented** for bounded JSONL iteration, parse errors,
  provenance, scope epochs, and both current reader contracts;
- `statistics.py`: **partially implemented** for exact historical
  percentiles and resource ranges; move histograms/timing summaries only when
  a second caller is characterized;
- `schema.py`: **partially implemented** for compact decision objects;
- `attribution.py`: **implemented** for physical-contact witnesses,
  stage/spell/death/cause classification, warning leads, complete ledger
  entries, and clustering;
- `full_run_render.py` and `practice_render.py`: **implemented** with exact
  Markdown/CSV output characterization;
- thin full-run entry point: **implemented enough to retain** at 815 lines;
- thinner practice entry point: pending summary aggregation checkpoints.

These tools remain offline. Their refactor must compare complete generated
JSON/Markdown/CSV outputs against retained fixtures; schema or attribution
changes require a separate research checkpoint.

## Authority Result

- **Observed:** this checkpoint changes source ownership and import topology.
- **Observed:** no action mask, recurrence, uncertainty branch, float
  comparison, deadline, worker policy, trace schema, or live strategy was
  intentionally changed.
- **Inferred:** smaller ownership modules and explicit dependencies reduce
  debug blast radius and make later iteration-stage tests possible.
- **Not claimed:** model validity, finite feasibility, unique/global
  optimality, or Lunatic/Extra route acceptance.
