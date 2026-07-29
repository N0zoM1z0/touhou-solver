# Runtime Report Retention And Emission Audit

Date: 2026-07-29

Status: emission correction implemented; historical raw cleanup audited but
not executed

## Scope

This audit answers two separate questions:

1. which files under `artifacts/runtime_reports/` are required to execute,
   diagnose, replay, or retain a physical result; and
2. which files are duplicate output or old local raw data that may be removed
   under the bounded-retention rule in `AGENTS.md`.

No historical raw bundle was deleted in this checkpoint.

## Observed Inventory

At audit time:

- directory allocation: `27G`;
- ignored raw JSONL: 66 files, `26.126 GiB`;
- tracked/staged compact files: 1,008 files, `81.137 MiB`;
- ignored launch logs: 65 files, `0.024 MiB`;
- artifact dossier Markdown: 125 files, `1.328 MiB`;
- artifact Markdown exactly equal to its `notes/runs/` copy: 74 files,
  `0.776 MiB`.

Raw JSONL by workload:

| Workload | Files | Raw size |
| --- | ---: | ---: |
| Hard full route | 1 | 1.713 GiB |
| Hard Stage 1 | 10 | 1.431 GiB |
| Hard Stage 4A | 4 | 1.357 GiB |
| Hard Stage 5 | 1 | 0.424 GiB |
| Hard Stage 6B | 1 | 0.628 GiB |
| Lunatic Stage 4A | 24 | 9.297 GiB |
| Lunatic Stage 5 | 20 | 9.001 GiB |
| Lunatic Stage 6B | 5 | 2.275 GiB |

The accepted V6 Stage-5 raw trace is 497,042,649 bytes. Its 12,039 decision
rows account for `473.978 MiB`; all other row classes together are small.
Within the decision rows, serialized `nearby_bullets` account for
`236.239 MiB`, `items` for `23.470 MiB`, `local_pipeline_root` for
`27.658 MiB`, `timing_ms` for `14.990 MiB`, and `robust_control` for
`14.480 MiB`.

## Output Classification

### Required or retention-bounded

- `.jsonl`: required while a result is being monitored and while its dossier,
  strict audit, replay, first-hit witness, geometry, resources, or observer
  semantics may need regeneration. It is local and retention-bounded, not a
  permanent file for every Git checkpoint.
- `.session.json`: required for exact launch flags, immutable identities,
  menu actions, acceptance, cleanup, and prelaunch/partial failures.
- `.summary.json`: required compact terminal/controller state.
- `.dossier.json`: canonical compact physical analysis.
- `.regressions.json`: normalized regression/gate result.
- `.deaths.csv`: smallest directly reviewable hit/phase attribution.
- `.comparison.json`: compact comparison to the selected accepted baseline;
  emitted only when a baseline exists.
- `notes/runs/<run-id>.md`: durable human-readable run record, later extended
  with experiment-specific interpretation.
- `.launch.log`: required for a launch failure that occurs before the agent
  trace is useful. Its total size is negligible, so deleting or disabling it
  does not address the capacity problem.

Tracked compact history is intentional and only about 81 MiB. Do not remove
it merely because the corresponding raw trace is later pruned.

### Proven duplicate

Practice and full-route materializers previously generated
`artifacts/runtime_reports/<run-id>.dossier.md` and then copied it byte for
byte to `notes/runs/<run-id>.md`. No code consumer reads the artifact
Markdown path; the run note is the durable, annotated authority.

The materializers now write the dossier Markdown directly to `notes/runs/`.
Focused tests require one Markdown output and assert that no runtime-report
Markdown duplicate exists. The uncommitted V6 duplicate was removed; tracked
historical copies are preserved.

## Raw Cleanup Analysis

Keeping only the two newest completed bundles per broad workload plus every
singleton would retain 13 raw files (`6.817 GiB`) and expose a
`19.309 GiB` deletion ceiling. This broad calculation is not safe enough:
observer flags, event schemas, and decision layouts changed across physical
experiments.

The stricter comparison grouped accepted runs by:

- workload;
- exact session observer/backend flags;
- controller-config record SHA-256;
- the set of raw `schema` labels; and
- the first decision's top-level-key fingerprint.

An old raw was considered only when the same signature had at least two newer
accepted bundles and the old run retained session, dossier, summary,
regression, deaths, and run-note compact files. This found nine
schema-compatible candidates (`3.254 GiB`). One is deliberately withheld:
the Stage-5 `20260728_185838` raw path is still named by its native auxiliary
VM batch report and result note.

The remaining eight exact-compatible, non-raw-path-referenced candidates are:

- `hard_route2_stage1_unattended_20260727_153821.jsonl`;
- `hard_route2_stage1_unattended_20260727_173735.jsonl`;
- `hard_route2_stage1_unattended_20260727_175715.jsonl`;
- `lunatic_route2_stage4a_unattended_20260728_031127.jsonl`;
- `lunatic_route2_stage4a_unattended_20260728_040144.jsonl`;
- `lunatic_route2_stage4a_unattended_20260728_065316.jsonl`;
- `lunatic_route2_stage4a_unattended_20260728_070838.jsonl`; and
- `lunatic_route2_stage4a_unattended_20260728_101804.jsonl`.

Together they occupy `2.711 GiB`. They satisfy the repository's mechanical
two-newer-compatible-plus-compact condition, but this checkpoint does not
delete them because the user asked for an audit, not destructive cleanup.
Before removal, produce a file-level path/size/SHA-256 manifest, recheck the
two successors, obtain explicit deletion approval, and record the material
removal in the current daily shard.

The other roughly 16 GiB above this strict set must not be bulk-deleted yet.
Most are older observer/schema families or unique/singleton workloads. They
need an explicit decision to retire legacy replay, archive externally, or
retain a compatible successor.

## Emission Decision

**Observed:** full decision rows, especially bullet geometry, dominate disk
usage and are consumed by replay, dossier attribution, transform analysis,
and first-hit diagnosis.

**Inferred:** omitting bullet/item geometry from the existing JSONL schema
would make the current raw bundle non-replay-capable and violate the evidence
contract. It is not a valid default suppression.

**Proposed:** if raw storage remains a problem after bounded pruning, define a
versioned lossless delta/compressed trace with streaming monitoring and
independent replay parity. Do not silently remove fields or gzip the live
file: the supervisor tails it during gameplay, and many auditors currently
expect plain line-delimited JSON.
