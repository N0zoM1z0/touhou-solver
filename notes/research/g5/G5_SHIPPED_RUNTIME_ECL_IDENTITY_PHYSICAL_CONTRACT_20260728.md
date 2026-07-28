# G5 Shipped Runtime ECL Identity Physical Contract

Date: 2026-07-28

Status: fixed before physical integration and physically accepted by
`notes/research/g5/G5_SHIPPED_RUNTIME_ECL_IDENTITY_STAGE5_RESULT_20260728.md`. The existing
bounded normalization primitive passes synthetic independent oracles and the
shipped Stage-5 image now matches exactly. This contract grants no source
completeness, future geometry, planner, feasibility, publication, cadence, or
physical action authority.

This contract narrows Phase C of
`notes/research/g5/G5_AUXILIARY_VM_RUNTIME_IMAGE_OBSERVATION_CONTRACT_20260728.md` after the
accepted schema-v3 auxiliary-VM delivery checkpoint. All inherited IDA names,
comments, and types remain untrusted unless the underlying instructions,
dataflow, static bytes, or physical observations are independently
revalidated.

## Physical Objective And Question

The physical objective remains hard no-Bomb survival. The experiment answers
one narrower question:

> During an actual shipped-game Lunatic Stage-5 run, does the complete
> relocated ECL image selected by the live `g_ecl_file_context` normalize
> byte for byte to the decoded `ecldata5.ecl` payload extracted from the
> shipped resource archive?

Exact equality establishes only instruction-byte identity for that immutable
stage image. It does not establish that a captured VM PC executed before a
particular bullet birth, that all firing sources are observed, that operands
or geometry are complete, or that one physical action is safe.

## Fixed Shipped Inputs

The target executable identity is:

- file: `th08.exe`;
- SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`.

The physical workload is:

- Sakuya/Remilia route id `2`;
- Lunatic difficulty index `3`;
- Stage-5 route index `5`;
- no-life-decrement patch verified by the existing supervisor;
- hard no-Bomb;
- one supervised practice run with normal controller authority unchanged.

The static candidate is:

- wrapped artifact: `artifacts/extracted/ecldata5.ecl`;
- wrapped marker: `edzE`;
- wrapped length: `47228`;
- wrapped SHA-256:
  `ca42defdb8488c07f825f8d6ffdb5ea461972fe946b83186427646a059f87dba`;
- decoded artifact: `artifacts/decoded/ecldata5.ecl`;
- decoded length: `47224`;
- decoded SHA-256:
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`.

**Observed in repository evidence:** applying `decode_resource(...,
require_wrapper=True)` to the wrapped artifact produces bytes exactly equal
to the decoded artifact. Earlier Stage-5 VM-PC mapping also selected legal
instruction boundaries under this decoded image. Neither observation
substitutes for runtime-byte equality.

## One-Shot Observation Transaction

The static artifact is read and hashed before gameplay iteration begins.
After one physical input send/no-write on the first decision whose observed
route, difficulty, and stage equal the fixed workload, an action-neutral
service performs exactly one visible attempt:

1. read the two-word ECL context at `0x004ECCB8`;
2. validate a bounded 32-bit image base and second word `base + 0x48`;
3. read and validate the fixed `0x48`-byte runtime header;
4. derive a length no larger than 8 MiB from the relocated data-end sentinel;
5. read exactly that complete relocated image once;
6. require the copied header to equal the first header read;
7. reread the two-word context and require exact stability;
8. normalize only the 16 header timeline/end slots and every declared
   subroutine-table entry by subtracting the captured runtime base;
9. compare length, counts, all normalized bytes, and SHA-256 to the static
   candidate; and
10. immediately flush one immutable result row.

The transaction performs exactly four process-memory reads on success. It is
not repeated per decision and has no silent retry or candidate selection. A
capture failure, pointer churn, malformed structure, wrong physical identity,
or byte mismatch produces a visible failed row and ends the attempt for that
run. A later retry requires another explicitly identified physical run.

The capture runs after current input issue. It may affect later iteration
cadence through one-time contention, so the physical report must retain the
capture wall time and adjacent decision cadence. It cannot change the action
already issued or any action field.

## Immutable Provenance And Record

The result binds:

- trace/run identity and PID;
- expected executable SHA-256;
- observed route, difficulty, stage, gameplay epoch, decision frame, and
  manager snapshot frame;
- static repository-relative label, byte length, and SHA-256;
- runtime base, image length, subroutine/timeline counts;
- exact relocated and normalized runtime SHA-256 values;
- four-read count and capture wall time;
- exact-match status and first differing offset; and
- explicit error text when capture or comparison fails.

The normalized or relocated raw runtime image remains a local bounded
debugging artifact only if the comparison fails. An accepted exact match
retains compact digests and the independently reproducible static bytes; it
does not add a large binary to Git.

## Information, Uncertainty, And Authority

Two identity records are equivalent only when executable, route, difficulty,
stage, runtime base, length, relocated digest, normalized digest, and static
digest all agree. Matching normalized bytes with different runtime bases may
establish the same static image but remains a different runtime capture
identity.

Unknown or rejected cases include:

- no matching physical decision before termination;
- context/base churn;
- truncated or unreadable process memory;
- invalid magic, counts, table address, relocation target, or end sentinel;
- a static artifact with invalid structure;
- unequal length or counts;
- any non-relocation byte difference; and
- timeout, cancellation, or cleanup failure.

All such cases enlarge the unresolved runtime-source set. They cannot be
reinterpreted as a different file, a terminated VM, an absent event, or a
safe future.

The live fallback remains the current Boolean policy plus its fresh local
certificate. No consumer may read this identity result on the action path in
this checkpoint.

## Safety Invariants And Falsifiers

- Hard no-Bomb, complete-mask, delay, cadence, and issue/no-write semantics
  remain unchanged.
- The new option is default-off and trace-only.
- Static file I/O occurs before the gameplay loop.
- Successful capture uses four bounded RPM calls and at most 8 MiB.
- No relocation site beyond the revalidated loader sites may be normalized.
- One failed attempt remains failed; there is no hidden retry.
- Every stop/error path still releases injected keys and cleans up the exact
  process.

The gate is falsified by:

- accepting a mutated non-relocation byte;
- omitting executable/route/difficulty/stage identity;
- reading the static file or starting cold expansion on the issue path;
- performing a hidden second runtime attempt;
- emitting no row after an attempted failure;
- changing any action, Bomb, planner, or policy field; or
- leaving a game/controller/supervisor process running.

## Independent And Automated Gates

Before physical use:

1. retain the existing synthetic relocation oracle, malformed-header/count/
   sentinel/context, pointer-churn, and non-relocation mutation tests;
2. add an action-neutral service test for exact trigger identity, one attempt,
   four-read capture result propagation, failure visibility, and no retry;
3. add supervisor/agent-contract tests proving the explicit static path is
   default-off and propagated without changing ordinary commands;
4. add a deterministic offline audit that requires exactly one matching row,
   validates all immutable fields and fixed shipped identities, and emits
   strict JSON;
5. run focused Ruff plus complete Linux and Windows quick suites.

The physical Stage-5 gate requires:

- verified executable, foreground, route, Lunatic, Stage 5, patch, and hard
  no-Bomb preflight;
- exactly one runtime-identity row;
- `status=exact_match`, four reads, decoded length `47224`, and both
  normalized/static digests equal the fixed decoded SHA-256;
- zero non-relocation mismatch and no first differing offset;
- explicit one-shot capture/compare timing and adjacent decision cadence;
- accepted route completion, compact artifacts, key release, supervisor exit
  zero, and process cleanup; and
- byte-identical offline audit regeneration.

One exact match accepts runtime instruction-byte identity for this Stage-5
image only. It does not promote auxiliary instruction/path lowering.

## Next Gate

If exact identity passes, freeze a separate auxiliary instruction/path
lowering contract for one event class. That contract must retain scheduler
order, timer/time-scale behavior, call/return state, projected locals,
unresolved operands, emission/template/origin dependencies, realized
slot-generation joins, and first-hit causal witnesses. Unsupported control
flow or dependencies remain unknown; no optimistic prefix becomes complete.

If identity fails, retain the first differing offset and bounded raw images
locally, revalidate archive selection and the loader's write set from
instructions/dataflow, and do not lower runtime instructions.
