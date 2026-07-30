---
name: th08-audit-native-solver-semantics
description: Perform a scoped TH08 native-to-solver semantic audit using shipped-program evidence, retained native traces, and the connected IDA Pro database when needed. Use when checking inherited IDA analysis, fields, offsets, ECL or callback behavior, solver/model correspondence, omitted native gates, or correctness-preserving performance work. Default to the smallest focused investigation that answers the request and reuse compatible retained evidence; perform a comprehensive, repository-wide, or exhaustive subsystem audit only when the user explicitly requests that scope. Keep investigation-only work read-only; when the user asks to fix, implement, or execute an accepted roadmap, permit evidence-backed source, note, and IDA corrections only within the requested scope.
---

# Audit TH08 Native-To-Solver Semantics

Use the shipped `th08.exe` instructions and dataflow as the semantic baseline.
Treat source parity, inherited IDA annotations, tests, and earlier notes as
evidence to check, never as substitutes for the native program.

## Bound The Scope First

1. Translate the request into the smallest concrete audit unit: a claim,
   field, function, event class, model path, retained root, mismatch, or
   measured performance boundary.
2. State the in-scope question and material exclusions before deep analysis.
   If the request is broad but not explicitly exhaustive, choose the smallest
   useful slice and identify that assumption.
3. Do not infer a comprehensive audit merely because this skill triggered,
   IDA is available, the repository targets NMNB, or the user said “audit,”
   “review,” “investigate,” “look at,” or “check.”
4. Expand the scope only when a concrete dependency is necessary to answer the
   question. State the expansion and its reason; do not opportunistically
   inventory unrelated routines, models, notes, tests, or old findings.
5. Reuse retained evidence when executable/IDB identity, root, model version,
   and relevant semantics are compatible and no newer observation contradicts
   it. Cite its provenance instead of repeating the entire audit or probe.

## Select The Audit Mode

- **Focused audit is the default.** Stop after the scoped question is answered,
  falsified, or reduced to an explicit `UNKNOWN`. Do not produce a
  repository-wide completeness claim, enumerate unrelated omissions, create a
  durable report, or run broad test gates unless the request or discovered
  dependency requires it.
- **Comprehensive audit is opt-in.** Use it only when the user explicitly asks
  for a full/comprehensive/repository-wide audit, exhaustive coverage of a
  named subsystem, or a complete audit deliverable. Read all five references
  below completely before starting IDA or source analysis.
- For one field, function, or offset, read the IDA, evidence, and reporting
  references only if a durable report is requested; otherwise read the IDA and
  evidence references. Also consult
  `$th08-revalidate-ida-runtime-semantics` when new native reliance requires
  it. Keep investigation-only requests read-only. For a fix, implementation,
  or accepted-roadmap execution request, use evidence-backed IDA, source,
  note, and checkpoint correction steps within the authorized scope.
- For one solver/model path, read the IDA, solver-traceability, and evidence
  references. Read the reporting reference only for a requested durable
  report or comprehensive audit.
- For a native robustness or performance review, read the native-performance,
  and evidence references; read the IDA reference whenever an optimization
  depends on native semantics, and the reporting reference only when needed.

Read every reference selected for the active mode completely, but do not load
unselected references “just in case.” Reference procedures do not expand the
active scope; use their exhaustive inventories and completion checklists only
in comprehensive mode.

References:

- [IDA native baseline](references/ida-native-baseline.md)
- [Solver semantic traceability](references/solver-traceability.md)
- [Native robustness and performance](references/native-robustness-performance.md)
- [Evidence and falsification](references/evidence-and-falsification.md)
- [Live reporting and handoff](references/live-reporting-and-handoff.md)

## Preserve Repository And Authority Boundaries

1. Read `AGENTS.md` and `START_HERE.md`. Read `STRATEGY.md` before changing an
   objective or promotion status, or when the scoped conclusion depends on
   current strategy authority. Read only the handoff notes and
   daily/counterexample shards directly relevant to the scoped question.
2. Follow the repository prohibition on REA. Use IDA Pro MCP for new binary
   static analysis and retained/native probes for runtime evidence.
3. Interpret a request that only says “audit”, “review”, “investigate”, or
   “check” as read-only. Do not infer mutation authority from those words.
   Conversely, a request to fix, correct, implement, or execute an accepted
   roadmap authorizes evidence-backed IDA renames/types/comments and
   repository corrections needed by that scope; it does not independently
   authorize strategy promotion or a physical trial.
4. Preserve unrelated and concurrent worktree changes. Record HEAD, branch,
   dirty-state caveat, IDB/executable identity, and evidence cutoff in a
   durable or comprehensive report; in a focused answer, record only identity
   details that materially support the conclusion.
5. Keep static, offline, shadow, and live-action authority separate. Never
   promote Python/C++ parity into physical-model validity.

## Create A Report Only When Needed

Create a live report only when the user requests one, the audit is explicitly
comprehensive, the work will produce several durable findings, or another
agent needs a retained handoff artifact. Do not create a `/tmp` or repository
report merely because this skill triggered.

When a report is required:

1. Resolve the requested report path. If none is supplied for an
   investigation-only report, use a clearly named file under `/tmp`.
2. Create it before deep analysis. Add scope, exclusions, snapshot, evidence
   labels, constraints, and an initially incomplete checklist.
3. Append or revise it after each confirmed finding, revalidation, falsifier,
   or performance conclusion.
4. Follow the reporting reference at the scale selected there.

For a focused audit without a report, keep a small task-local checklist and
deliver the evidence, conclusion, remaining `UNKNOWN`, and material
out-of-scope items directly in the final answer.

When a report uses numbered entries, use finding prefixes consistently:

- `F-###` for defects, misleading analysis, or missing semantics;
- `V-###` for positive revalidation;
- `P-###` for performance conclusions or proposals.

## Establish The Native Baseline

1. Before making a new native semantic claim, verify or reuse current retained
   evidence that the connected IDB and executable refer to the same shipped
   build or to an exactly explained patch set. Do not open IDA for a
   source-architecture or research discussion that makes no new native claim.
   If IDA Pro MCP is unavailable, record the blocked native checks and do not
   describe a source-only review as a complete native-to-solver audit.
2. In focused mode, record only the identity fields needed by the claim. In
   comprehensive mode, record base address, file size, hashes, known patches,
   and raw-offset/VA mapping. Stop semantic comparison if required identity
   cannot be reconciled.
3. Treat every inherited name, type, comment, pseudocode variable, and prior
   semantic label as a hypothesis.
4. For each scoped claim, inspect the minimum instructions, dataflow,
   producers, consumers, callers/callees, tables, and transitions needed to
   distinguish the competing interpretations. Use assembly where decompiler
   types, signedness, aliasing, or calling conventions can change meaning.
5. Enumerate dispatch tables, callback tables, opcode reachability, indirect
   consumers, or lethal-event caller closure only when omission/completeness
   is in scope or the concrete claim depends on them.

Apply the relevant IDA procedure to the scoped claim. Use its complete
inventory procedure only in comprehensive mode.

## Trace Native Semantics Through The Solver

For each native fact in scope, build an explicit chain:

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

Within the scoped path, search for fields that are captured but unused, fields
used but not captured, state collapsed too early, future events represented
only as velocity changes, and gates whose producer and consumer live in
different callbacks. Do not turn this into an unrelated repository-wide
search in focused mode.

Apply the solver-traceability reference only to the scoped path.

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

Apply the evidence reference at the active scope.

## Audit Native Robustness And Performance

Enter this section only when robustness or performance is part of the scoped
request or a necessary dependency of its answer.

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

Apply the native robustness and performance reference at the active scope.

## Close The Audit

For a focused audit:

1. Answer the scoped question directly.
2. Label material conclusions observed, inferred, or hypothesized.
3. State the minimal evidence and validation actually used.
4. Identify remaining `UNKNOWN` and material exclusions without converting
   them into a new backlog.
5. Stop when the task-specific exit condition is met. Do not require an
   executive summary, consolidated IDA backlog, full verification matrix,
   report hash, or broad test suite.

For a comprehensive audit:

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

Do not declare a comprehensive audit complete until the reporting reference’s
final checklist passes. A focused audit makes no completeness claim outside
its stated scope.
