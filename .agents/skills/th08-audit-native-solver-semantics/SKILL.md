---
name: th08-audit-native-solver-semantics
description: Perform a comprehensive TH08 native-to-solver audit using the connected IDA Pro database as the shipped-program baseline. Use when reviewing whether inherited IDA analysis, renames, types, comments, offsets, ECL or callback semantics are accurate; whether Touhou Solver Python, C, or C++ decoders, models, projections, or planners preserve those semantics; whether important native routines or state gates were omitted; or where correctness-preserving performance improvements exist. Use read-only mode for investigation-only requests; when the user asks to fix, implement, or execute an accepted roadmap, permit evidence-backed source, note, and IDA database corrections within that scope.
---

# Audit TH08 Native-To-Solver Semantics

Use the shipped `th08.exe` instructions and dataflow as the semantic baseline.
Treat source parity, inherited IDA annotations, tests, and earlier notes as
evidence to check, never as substitutes for the native program.

## Select The Audit Mode

- For a repository-wide or subsystem-wide review, read all five references
  below completely before starting IDA or source analysis.
- For one field, function, or offset, read the IDA, evidence, and reporting
  references. Also consult `$th08-revalidate-ida-runtime-semantics` when
  available. Keep investigation-only requests read-only. For a fix,
  implementation, or accepted-roadmap execution request, use that skill's
  evidence-backed IDA, source, note, and checkpoint correction steps within
  the authorized scope.
- For one solver/model path, read the IDA, solver-traceability, evidence, and
  reporting references.
- For a native robustness or performance review, read the native-performance,
  evidence, and reporting references; read the IDA reference whenever an
  optimization depends on native semantics.

References:

- [IDA native baseline](references/ida-native-baseline.md)
- [Solver semantic traceability](references/solver-traceability.md)
- [Native robustness and performance](references/native-robustness-performance.md)
- [Evidence and falsification](references/evidence-and-falsification.md)
- [Live reporting and handoff](references/live-reporting-and-handoff.md)

## Preserve Repository And Authority Boundaries

1. Read `AGENTS.md`, `START_HERE.md`, `STRATEGY.md`, the notes named by the
   handoff, and the current daily/counterexample shards relevant to the audit.
2. Follow the repository prohibition on REA. Use IDA Pro MCP for new binary
   static analysis and retained/native probes for runtime evidence.
3. Interpret a request that only says “audit”, “review”, “investigate”, or
   “check” as read-only. Do not infer mutation authority from those words.
   Conversely, a request to fix, correct, implement, or execute an accepted
   roadmap authorizes evidence-backed IDA renames/types/comments and
   repository corrections needed by that scope; it does not independently
   authorize strategy promotion or a physical trial.
4. Preserve unrelated and concurrent worktree changes. Record the audit HEAD,
   branch, dirty-state caveat, IDB identity, executable identity, and evidence
   cutoff.
5. Keep static, offline, shadow, and live-action authority separate. Never
   promote Python/C++ parity into physical-model validity.

## Start A Live Audit Record

1. Resolve the requested report path. If none is supplied, use a clearly named
   file under `/tmp`.
2. Create the report before deep analysis. Add scope, snapshot, evidence
   labels, constraints, and an initially incomplete checklist.
3. Append or revise the report immediately after each confirmed finding,
   revalidation, falsifier, or performance conclusion. Do not defer all
   writing until the end.
4. Keep commentary updates concise while tools run. Ensure the final answer is
   self-contained and links the completed report.

Use finding prefixes consistently:

- `F-###` for defects, misleading analysis, or missing semantics;
- `V-###` for positive revalidation;
- `P-###` for performance conclusions or proposals.

## Establish The Native Baseline

1. Verify that the connected IDB and the executable named by the handoff refer
   to the same shipped build or to an exactly explained patch set.
   If IDA Pro MCP is unavailable, record the blocked native checks and do not
   describe a source-only review as a complete native-to-solver audit.
2. Record base address, file size, hashes, known patches, and raw-offset/VA
   mapping. Stop broad semantic comparison if identity cannot be reconciled.
3. Treat every inherited name, type, comment, pseudocode variable, and prior
   semantic label as a hypothesis.
4. For each claim, inspect instructions, dataflow, producers, consumers,
   callers, callees, cross-references, tables, and state transitions. Use
   assembly where decompiler types, signedness, aliasing, or calling
   conventions can change meaning.
5. Enumerate important unmodeled native programs through dispatch tables,
   callback tables, opcode reachability, indirect consumers, and lethal-event
   caller closure rather than by browsing only already named functions.

Follow the detailed procedure in the IDA reference.

## Trace Native Semantics Through The Solver

For each native fact, build an explicit chain:

```text
native producer/transition
  -> runtime observation
  -> Python/native decoder
  -> state/model object
  -> projection/lowering
  -> scalar and C/C++ kernel
  -> certificate/planner recurrence
  -> issue-time consumer
```

At every edge, ask:

1. Is the native field captured?
2. Is its state/lifetime/enable condition retained?
3. Is it transformed with the correct units, coordinate system, full/half
   extents, timing, float32 stores, and same-frame order?
4. Is it conditioned on every available action and observation without
   clairvoyance?
5. Is the C/C++ path independently checked against native semantics, or only
   against a Python implementation with the same assumption?
6. Is an omission conservative, optimistic, mixed-direction, or unknown?
7. Which current workload and authority claim can actually reach it?

Search specifically for fields that are captured but unused, fields used but
not captured, state collapsed too early, future events represented only as
velocity changes, and gates whose producer and consumer live in different
callbacks.

Follow the solver-traceability reference.

## Build Minimal Falsifiers

1. Prefer the smallest deterministic case that distinguishes the native
   behavior from the solver behavior.
2. Exercise public Python/C ABI surfaces where possible. Run native crash
   probes in a subprocess so one malformed case does not kill the audit.
3. Cover boundary states: inactive/active/fade, enable/disable transitions,
   timer threshold sides, negative and maximum integers, nonfinite and extreme
   finite floats, pool-full paths, clamp boundaries, and same-frame action
   edges.
4. Use retained runtime evidence before requesting a new physical experiment.
   Do not attribute a historical hit to a static finding without a causal
   native differential.
5. Run focused existing tests after reproducing a gap. Treat green tests as a
   coverage statement, not as refutation of a new native mismatch.

Follow the evidence reference.

## Audit Native Robustness And Performance

1. Review ABI validation, arithmetic ranges, output atomicity, cancellation,
   lifetime, concurrency, and malformed snapshots.
2. Reproduce suspected undefined behavior or crashes with independent safe
   inputs and record exact exit status.
3. Derive performance work from retained workload timings and the current
   source allocation/loop graph. State the measured boundary and workload.
4. Separate correctness fixes that reduce false hazards from pure
   optimizations.
5. Preserve numeric types, accumulation order, stable ranking, quantifiers,
   cancellation, and immutable versions in every optimization proposal.
6. Never promise an unmeasured percentage improvement.

Follow the native robustness and performance reference.

## Close The Audit

1. Re-read every finding for evidence direction, reachability, severity,
   authority scope, and internal consistency.
2. Separate current-workload defects from acceptance-target defects and
   generic robustness issues.
3. Add an executive summary, prioritized correction order, consolidated IDA
   backlog, minimal verification matrix, commands/results actually run, and
   explicit non-actions.
4. Remove “in progress” language and stale checklist items.
5. Verify the report is readable and record its size and hash when useful. In
   read-only mode, confirm no repository or IDA mutation occurred. In
   correction mode, enumerate the exact source, note, and IDA mutations and
   the evidence supporting each one.

Do not declare completion until the reporting reference’s final checklist
passes.
