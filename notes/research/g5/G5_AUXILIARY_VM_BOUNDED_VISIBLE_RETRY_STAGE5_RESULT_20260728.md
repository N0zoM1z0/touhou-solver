# G5 Auxiliary-VM Bounded Visible Retry Stage-5 Result

Date: 2026-07-28

Status: **accepted for default-off trace-only auxiliary-VM observation
delivery**. The schema-v3 bounded retry physically exercised four
frame-boundary failures and selected a coherent second complete v2 attempt
for all four. All 123 due transactions succeeded within two of the fixed
three attempts, and every timing, cadence, hard no-Bomb, route, session, and
cleanup gate passed.

This result corrects CE-0165's rejected no-retry composition. It grants no
runtime-ECL identity, source-completeness, future-hazard, geometry, planner,
feasibility, publication, cadence, or live-action authority.

The governing contract is
`notes/research/g5/G5_AUXILIARY_VM_BOUNDED_VISIBLE_RETRY_CONTRACT_20260728.md`. The physical
workload is `lunatic_route2_stage5_unattended_20260728_200739`.

## Decision

Retain schema v3 and the at-most-three-attempt composition as the accepted
delivery boundary for this default-off observer:

- every attempt is one complete native-owned v2 transaction with its own
  four-frame evidence;
- retryability is a closed whitelist of frame-boundary and accompanying
  owner/context-churn bits;
- every failed attempt summary remains visible;
- only the coherent successful v2 observation is selected;
- terminal failure or three-attempt exhaustion publishes no state;
- there is no sleep, polling, game pause, action change, or Python
  owner/frame read; and
- all attempt reads and native/materialization time are charged to the one
  due transaction.

The strict analyzer independently recomputes retryability and validates
attempt order, stop conditions, selected-summary/observation equality,
record-status histograms, read sums, timing sums, and hard read bounds.

The accepted correction does not mean an asynchronous read is atomic.
CE-0165 remains the durable witness disproving that assumption. It means the
observer now handles the observed boundary uncertainty explicitly, with a
bounded and fail-closed transaction that passed its precommitted physical
gate.

## Implementation And Independent Validation

No native ABI or recurrence changed. The Python trace service composes the
unchanged `touhou_trace_auxiliary_vm_batch_process_v2` call at most three
times and emits schema v3. Each attempt records:

- selected, owner-close, context-open, and final manager frames;
- success, batch status, and independently auditable retry classification;
- owner/record/non-null/usable counts and record-status histogram;
- process reads, owner bytes, state bytes; and
- native-call and Python materialization time.

Focused tests cover first- and second-retry success, exhaustion, terminal
stop, cadence/context reset, no Python owner/frame reads, all allowed batch
and record bit classes, forbidden semantic/read/capacity/unknown bits, forged
retryability, hidden attempts, selected-state mismatch, and timing sums.

Validation completed before the physical run:

- focused Ruff: pass;
- focused auxiliary-VM discovery: 24 tests pass;
- complete Linux discovery: 942 tests pass;
- complete Windows UNC discovery: 942 tests pass with three existing
  platform skips; and
- the unchanged v2 Linux/Windows native builds, parity, and benchmark
  evidence remain those retained by the preceding checkpoint.

## Physical Stage-5 Gate

The explicit action-neutral run completed:

- frames `2..43163`;
- 13,097 decisions;
- ten hits at
  `[4184, 11206, 11665, 12314, 12786, 23566, 25065, 32057, 36515, 42417]`;
- hard no-Bomb;
- `route_complete`;
- accepted supervisor/session and transition behavior;
- exact key release and identity-scoped cleanup; and
- no residual game, controller, or supervisor process.

The action policy did not consume the observer output. Ten hits versus eight
in the compatible baseline and twenty in the preceding v2 run are
descriptive RNG/workload outcomes, not causal survival improvement or
regression.

The strict spell-107 audit observes:

- 123 schema-v3 due transactions and 123 selected successes;
- 119 one-attempt successes;
- four two-attempt successes;
- zero three-attempt transaction, exhaustion, terminal rejection, exception,
  selected batch/record failure, or validation error;
- 3,214 selected usable depth-0 contexts;
- 6,162 selected explicit null rows;
- 1,058 unique selected active-VM hashes;
- non-null/usable contexts p50/p95/p99/max `30/32/34/34`; and
- summed process reads p50/p95/p99/max
  `117/133.9/136.56/142`.

All four retry witnesses are owner-close crossings:

| Trigger decision | Attempt 0 | Attempt 1 |
| ---: | --- | --- |
| 30878 | selected 30878, owner close 30879, status 64 | coherent 30879 |
| 31444 | selected 31444, owner close 31445, status 64 | coherent 31445 |
| 31807 | selected 31807, owner close 31808, status 64 | coherent 31808 |
| 32050 | selected 32050, owner close 32051, status 64 | coherent 32051 |

The failed attempts perform exactly three reads and publish no context state.
The immediate complete retry selects the later physical version; no failed
state is mixed into it.

Per-transaction summed native-call p50/p95/p99/max is
`0.325/0.487/0.536/0.848 ms`, below the fixed `2/4/12 ms` limits.
Materialization p50/p95/p99/max is
`0.543/0.969/1.335/1.361 ms`; total service time is
`1.087/1.618/2.169/2.248 ms`. Decision-frame delta remains p50/p95/p99
`2/4/4`, equal at p95/p99 to the compatible no-batch baseline.

Every fixed gate passes. The strict report digest is
`faf5009c326fa65d18aae331221a6fc3ce0652e313de3c1d41d27b5f916748f6`.

## Evidence Provenance And Authority

The physical run executed from parent checkpoint `789d4ca` plus the exact
working-tree changes enclosed by the commit containing this note. The
enclosing commit, run ID, and digests are the checkpoint-to-physical mapping.

The tracked compact report is:

`artifacts/viability_audit/g5_auxiliary_vm_bounded_retry_stage5_20260728_200739.json`.

The replay-capable raw trace remains local and ignored:

- path:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260728_200739.jsonl`;
- bytes: `613142286`;
- SHA-256:
  `953a5c3cb4bef84a809c9d2681aedcc081f67cc7f8dc39aa942bc42f0da779e9`.

Session SHA-256 is
`1410a241f577b2ac4f8172845661395d8a2876185ccb51b7b7c4d314e2759106`;
summary SHA-256 is
`1870f63320294f72c1c46a86c1956b5e050f03887647c16ccfc5bf72dc6c8509`.
The compatible baseline raw SHA-256 remains
`de697d66bac26ac4ba59185a55c1432249e10111f275299f9c78085d363e78ec`.

The two newest compatible auxiliary-batch replay bundles are the v2
`20260728_193820` and v3 `20260728_200739` runs. No retained bundle was
deleted.

The next G5 source step is to capture and byte-compare one shipped Stage-5
runtime ECL image under immutable provenance, then contract auxiliary-VM
instruction/path lowering one event class at a time. The accepted delivery
mechanism stays trace-only until those model and coverage gates pass.
