# G5 Auxiliary-Pointer Stage-5 Result

Date: 2026-07-28

Status: phase-A auxiliary-pointer observation, cross-platform microbenchmark,
physical Stage-5 density/churn measurement, and Phase-B delivery selection
complete. The runtime-image identity primitive passes independent synthetic
tests, but a shipped-runtime Stage-5 image has not yet been captured and
compared. No live guidance, future geometry, feasibility, or action authority
is added.

The governing contract is
`G5_AUXILIARY_VM_RUNTIME_IMAGE_OBSERVATION_CONTRACT_20260728.md`.
The retained physical workload is
`lunatic_route2_stage5_unattended_20260728_171633`.

## Decision

Retain schema 12 as explicit opt-in, zero-extra-RPM pointer instrumentation.
Implement Phase B as one bounded native compact batch, not one Python process
read per non-null context and not a full `0x24B0` copy of every context.

The batch must:

1. validate at most 64 ordinary-enemy owners and four context pointers each;
2. capture only the active `0x228`-byte VM fields needed for the exact
   104-byte projection, plus call depth and the exact required saved frames;
3. recheck owner identity and all four pointer values after copying;
4. publish one immutable frame/version-bracketed compact result; and
5. publish nothing on churn, unreadable memory, overflow, deadline, or
   version mismatch.

The current pointer inventory and runtime-image code remain research-only.

## Code And Evidence Provenance

The physical run executed from parent checkpoint
`3adad090a77c583e389a9e78b863f0def299e606` plus the exact working-tree
changes enclosed by the commit that contains this note. The enclosing commit,
this run ID, and the raw/report digests below are the authoritative
checkpoint-to-physical mapping.

The raw trace remains local and replay-capable:

- path:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260728_171633.jsonl`;
- bytes: `553193476`;
- SHA-256:
  `de697d66bac26ac4ba59185a55c1432249e10111f275299f9c78085d363e78ec`.

The two newest compatible raw Stage-5 bundles are retained locally; no prior
bundle was deleted in this checkpoint.

## Implementation

### Schema-12 pointer inventory

`EnemyMainEclVmInventory` now has an explicit v2 layout. For every active
owner in the first 64 ordinary-enemy records it decodes the four
`enemy+0x3384` pointers from the already-paid contiguous enemy-prefix blob.
It performs zero additional process reads. Schema 11 remains strict and
byte-compatible when pointer decoding is disabled.

The strict birth audit and modular main-VM trace reader accept schema 11 or
12 only when the trace schema and inventory layout agree. Schema 12 retains
owner rows, pointer counts, invalid-address evidence, and exact joined
decision scope.

### Modular density and churn analyzer

The new `scripts/analysis/auxiliary_pointer_inventory/` package separates:

- immutable observation-level dynamics;
- pointer/owner transition analysis;
- censored dwell-run construction; and
- deterministic authority-scoped reporting.

The analyzer never treats a slot address or heap pointer as an enemy
incarnation. It resets across epoch/stage discontinuities and labels dwell as
consecutive observation agreement, not exact allocation lifetime.

### Runtime-image identity primitive

`scripts/th08_live/runtime_ecl_image.py` implements a four-read, one-shot
capture:

1. context base/table;
2. fixed `0x48` header;
3. exactly the relocated data-end length; and
4. context recheck.

It reverses only the 16 timeline/end relocations and declared subroutine-table
relocations observed in `ecl_load_file`. Runtime and static magic, counts,
length, timeline offsets, subroutine offsets, context stability, and every
non-relocation byte fail closed. This is tested implementation evidence only;
the exact shipped Stage-5 runtime/static byte comparison remains pending.

## Cross-Platform Microbenchmark

Both 20,000-iteration fixtures scan 64 records with 16 active owners, 40
non-null contexts, 14 valid main VMs, and two explicit invalid main VMs.
The v1 canonical record remains 2,715 bytes with cross-platform digest
`aa8d425a2264396e8e10de93283539667e84cbde67c09a802a0a25079f9cdd70`.
The schema-v2 record is 3,620 bytes with digest
`3763f94d367379997682ffb88b8da3c195fbb162e4c72e4410004cdb022b5675`.

Linux pointer-only paired decode p50/p95/p99/p99.9/max is
`0.0195/0.0316/0.0514/0.0823/0.3469 ms`; paired JSON delta is
`0.0144/0.0212/0.0324/0.0588/0.3144 ms`. Windows is
`0.0198/0.0242/0.0360/0.0749/0.3468 ms` and
`0.0163/0.0196/0.0269/0.0543/0.6581 ms`.

Pointer-inclusive inventory p95 is `0.1101 ms` on Linux and `0.1167 ms` on
Windows. Combined body/inventory p95 is `0.1651/0.1762 ms`. The capability is
small but nonzero work; its value and physical boundary matter more than
declaring any single microbenchmark delta free.

Retained artifacts:

- Linux SHA-256:
  `1bfe8ee8caf9485828e69162e5c64732656875a6e22fc00efe59217b9fdd32eb`;
- Windows SHA-256:
  `3899b06076dbcbbba36356c958e5fa86fa51eefa989564715b0cff6a7212b109`.

## Physical Stage-5 Observation

The run completed frames `2..41630` over 12,032 decisions with eight native
hit edges:

`[12324, 14116, 24615, 25486, 30504, 33449, 36710, 40462]`.

It passed hard no-Bomb verification across all decisions, automatic route
acceptance, exact key release, supervisor exit zero, and residual-process
cleanup. The first hit at frame 12,324 is the canonical fresh-attempt causal
witness; later contacts are discovery evidence.

Eight hits and a first hit at frame 12,324 are better than the preceding
schema-11 workload's 11 hits and first hit at frame 2,390. This checkpoint
changed no live action path, and TH08 RNG/phase timing differs, so the
difference is an observed run outcome, not a causal survival improvement.

All 12,032 rows are schema 12 with stable enemy-prefix brackets. There are
zero invalid main VMs and zero invalid auxiliary pointers. Physical
main/pointer inventory decode p50/p95/p99/p99.9/max is
`0.1193/0.2789/0.3690/0.5551/0.6620 ms`.

The unchanged native birth observation boundary still passes its fixed gate:
p50/p95/p99/p99.9/max is
`0.0980/0.1970/0.3359/0.5110/0.6995 ms`, below
`0.20/0.40/2.00 ms` at p95/p99/max. Inventory decode is reported separately
because this trace-only research work is not the birth-observation authority
boundary.

## Density, Churn, And Identity

Across all 12,032 captures:

- active first-64 owners per capture p50/p95/p99/max:
  `10/29/38/42`;
- non-null auxiliary contexts per capture p50/p95/p99/max:
  `4/26/32/34`;
- non-null contexts per active owner p50/p95/p99/max:
  `1/2/2/2`;
- comparable capture pairs: `12031`;
- continuing-pointer observations: `83006`;
- observed null-to-non-null / non-null-to-null transitions:
  `242/40`;
- observed direct non-null pointer replacements: `0`; and
- observed non-null runs: `544`, of which `512` are bounded on both sides.

Spell 107 is the densest retained phase at p50/p95/max
`30/32/34` contexts per capture. Spell 103 has no ordinary auxiliary
contexts in this run. These are workload observations, not stage identities
or promotion profiles.

Only 57 unique non-null heap addresses occur, and 56 are seen at more than one
`(slot, auxiliary-index)` over the route. This is observed allocator reuse
across time. It proves that pointer value alone is not a stable source
identity and makes the before/after owner-pointer bracket mandatory.

At the observed density, a 104-byte active-VM projection has payload
p50/p95/p99/max `416/2704/3328/3536` bytes per capture. Copying every full
`0x24B0` allocation would instead cost
`37568/244192/300544/319328` bytes and include state that the current
contract does not need.

The deterministic density/churn report has:

- internal digest:
  `43f98f713158d60e20edd37b0ebfed76fedd4790450e3c5a23957faeabaa7c5c`;
- retained pretty-file SHA-256:
  `0845f258c26c42bff76944a5d14fe86c2571fabaea3d9a25e964fd25cf737fb3`.

## Corrected IDA Provenance

The earlier inherited IDA label for context `+0x230` was wrong. Revalidation
of `ecl_eval_int`, the lvalue resolver, and `ecl_call_subroutine` establishes:

- active VM: context `+0x08`;
- live locals: active VM `+0x18..+0x64`; and
- saved call frames: context `+0x230 + depth * 0x228`.

The IDA comment at `0x0041EBE9` and every retained source of truth were
corrected. CE-0163 records why inherited IDA names, types, comments, and
pseudocode labels must never receive authority without independent
revalidation.

## Validation

- focused auxiliary-pointer dynamics/report tests: 4 pass;
- focused main-VM source-join tests: 11 pass;
- focused runtime-image identity tests: 6 pass;
- focused Ruff over all changed Python paths: pass;
- complete Linux discovery: 918 pass;
- complete Windows UNC discovery: 918 pass, 3 existing platform skips.

## Next Gate

1. Freeze the native compact-batch ABI and exact call-depth/saved-frame
   offsets from independently revalidated IDA/dataflow evidence.
2. Implement scalar and native decoders with adversarial pointer churn,
   owner reuse, unreadable context, maximum density, and bounded-output tests.
3. Measure Windows batch wall/cycle time, bytes, freshness, cancellation, and
   issue-path isolation.
4. Capture and compare one exact shipped Stage-5 runtime ECL image outside the
   issue boundary.
5. Run a focused action-neutral Stage-5 spell-107 physical gate, because it is
   the densest observed phase.
6. Only then interpret a fail-closed auxiliary fire subset and join it to
   realized slot generations and first-hit witnesses.

Viability preservation under CE-0158, hard-stage performance, and wider
Stage-4/5/6 mechanics research continue in parallel; this source contract is
not a ceiling.
