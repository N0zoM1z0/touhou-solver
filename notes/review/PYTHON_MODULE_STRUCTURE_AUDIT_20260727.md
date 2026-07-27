# TH08 Python Module Structure Audit

Date: 2026-07-27

Status: structural checkpoint audit; no model or strategy promotion

## Scope And Evidence Boundary

This audit records the Python decomposition performed after
`CONSOLIDATED_RESEARCH_AND_REFACTOR_ROADMAP_20260727.md`, the remaining
coupling, and the order for later structural work.

- **Observed:** the changes through `02d0e32` preserve the quick-suite result:
  `628/628` on Linux and `628/628` on Windows with three existing
  platform skips.
- **Observed:** deterministic old/new comparisons preserved:
  144 semantic-case payloads plus one shrink result, seven hotkey launch
  contracts, full-route parser/retention behavior, all 23 public ECL symbols,
  and five complete local-planner decisions after timing fields were removed.
- **Observed:** the post-extraction Windows physical smoke
  `hard_route2_stage1_unattended_20260727_144128` completed Hard Stage 1 with
  7,502 decisions over frames `1..20768`, zero hits, zero Bomb input, accepted
  terminal unload, artifact materialization, supervisor completion, and no
  residual game/controller process.
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

The extraction reduced `scripts/th08_live/controller.py` from roughly 8,000
lines to 6,566 lines. The remaining dominant block is the 3,559-line
`_run_live_session`.

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

All compatibility facades preserve the historical import surface. The
runtime, practice, full-route, hotkey, ECL, and live facades alias the
implementation module where module-level patch identity matters.

## Remaining Long Modules: Decision

| Module | Lines | Decision | Reason |
| --- | ---: | --- | --- |
| `th08_live/controller.py` | 6,566 | split next, contract first | `_run_live_session` still combines capture, service updates, publication lookup, proposal, fresh issue, and trace construction. |
| `th08_live/planner_pass.py` | 1,685 | retain for now | Large but now one causal planner pass. Split baseline, supplemental, and finalization only after the dependency boundary has retained workload evidence. |
| `analysis/th08_run_dossier.py` | 2,451 | split after live iteration contract | Offline reader, attribution, aggregation, validation, and rendering are separable and low authority-risk. |
| `analysis/th08_practice_dossier.py` | 2,307 | split with shared dossier primitives | It duplicates trace reading, statistics, schema construction, and rendering responsibilities. |
| `th08_automation/practice_supervisor.py` | 683 | retain orchestration | Resource/process/menu/monitor/artifact logic is already behind narrow modules; the remaining file is composition and lifecycle flow. |
| `th08_corridor_adapter.py` | 691 | retain; watch growth | This is the TH08-specific hazard-lowering and control-spec adapter required by the workspace boundary. Its dependencies point inward to game-neutral control code. |
| `th08_corridor_runtime.py` | 643 | retain; watch growth | It is a cohesive publication/query lifecycle for corridor artifacts. A split is warranted only if candidate-verifier and prewarm lifecycles diverge further. |
| `th08_item_model.py` | 542 | retain | It is a deterministic item state/resource model with one domain responsibility. |
| `th08_simulator.py` | 503 | retain | It composes deterministic update-order executors; splitting each manager step would add navigation without reducing coupling. |

Line count alone is not a refactor criterion. A split must create a stable
contract, isolate ownership or side effects, or make an independently testable
semantic unit.

## Next Live-Session Contract

Do not move `_run_live_session` wholesale into another 3,500-line file. First
introduce an explicit iteration state and stage results while keeping the
physical-frame contract unchanged.

The next structural sequence is:

1. Add immutable `CapturedIteration`:
   observed game state, source/snapshot frames, player, pools, scene identity,
   input clock, and capture timings.
2. Add `ServiceUpdate`:
   completed corridor/enemy/candidate/prewarm results and exact policy version.
3. Add `PublishedGuidance`:
   lookup-only exact-version guidance and declared miss/fallback reason.
4. Reuse `LocalProposal` as the local planning output; do not place fresh
   issue observations in it.
5. Add `FreshIssueResult` around `IssueTransaction`:
   fresh enemy prefix, recertification, selected action, send/no-write result,
   issue frame, and deadline status.
6. Build trace records from those immutable stage outputs after the issue
   transaction.

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
Windows Stage-1 no-strategy-change physical smoke before declaring the R5
exit gate retained.

## Dossier Tool Follow-Up

After the live iteration contract is stable, create shared offline modules
under `scripts/analysis/dossier/`:

- `trace_reader.py`: bounded JSONL iteration, parse errors, and scope epochs;
- `statistics.py`: percentiles, histograms, and timing summaries;
- `attribution.py`: stage/spell/death/cause classification;
- `schema.py`: compact report objects and validation;
- `render.py`: Markdown/CSV/JSON rendering;
- thin practice and full-route entry points.

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
