# G5 Auxiliary-VM And Runtime-Image Observation Contract

Date: 2026-07-28

Status: fixed before implementation; phase-A pointer inventory,
cross-platform benchmark, physical Stage-5 density/churn gate, and bounded
Phase-B delivery are complete. The runtime-image primitive passes synthetic
oracles; shipped-runtime image identity remains pending under
`notes/research/g5/G5_SHIPPED_RUNTIME_ECL_IDENTITY_PHYSICAL_CONTRACT_20260728.md`. This work has
no live guidance, future hazard, feasibility, publication, or action
authority. Phase-A and Phase-B results are retained in their Stage-5 result
notes.

This contract follows
`notes/research/g5/G5_NONSPELL_MAIN_VM_SOURCE_SHADOW_CONTRACT_20260728.md` and its retained
Stage-5 result. That checkpoint established that ordinary main-VM PCs carry
useful source signal, but also showed that main-PC-only coverage is
structurally incomplete: opcode `0x87` creates one of four auxiliary ECL
contexts, and the enemy scheduler executes those contexts after the main VM.

## Physical Objective And Research Questions

The physical objective remains hard no-Bomb survival. The immediate
observation questions are:

1. Which active first-64 ordinary enemies have non-null auxiliary ECL
   contexts at a capture?
2. Can a later bounded capture identify each auxiliary VM's exact PC, timer,
   and projected locals without unbounded issue-thread process reads?
3. Do the instructions at observed main and auxiliary PCs belong byte for
   byte to the decoded stage ECL image used by the shipped process?

This checkpoint changes no controller action, cadence, command pickup delay,
planner recurrence, uncertainty set, clearance field, fallback, route
profile, or issue semantics. It may not create a predicted bullet or change a
`COMPLETE`, `UNKNOWN`, viable, or safe-action result.

## Observed Shipped-Game Evidence

The following is **observed statically** in the connected shipped TH08 IDA
database:

- opcode `0x87` is handled at `0x0041CDF3..0x0041CF81`;
- its first argument selects one of four pointers rooted at
  `enemy+0x3384`;
- the selected old context is freed; a non-negative target allocates and
  zeros `0x24B0` bytes, starts an ECL VM at context `+0x08`, and copies local
  state;
- `enemy_ecl_vm_step` at `0x0041EBB6..0x0041EC7C` iterates the same four
  pointers after the main VM and selects the active VM at context `+0x08`;
- `ecl_eval_int` and `ecl_resolve_int_lvalue` read live locals from active VM
  offsets `+0x18..+0x64`;
- `ecl_call_subroutine` saves the complete `0x228`-byte active VM at context
  `+0x230 + depth * 0x228`; context `+0x230` is the saved-call-frame area,
  not the live-local base;
- context `+0x06` is signed 16-bit call depth, saturating at 15; the
  `0x24B0` allocation contains 16 physical saved slots, ordinary returns
  restore at most slots `0..14`, and saturated calls can write slot 15;
- `g_ecl_file_context` is rooted at `0x004ECCB8`;
- `ecl_load_file` at `0x00418330` loads the decoded ECL resource, requires
  magic `0x800`, relocates all 16 header timeline/end slots in place, points
  the context's second word at image `+0x48`, and relocates every subroutine
  table entry in place; and
- the header slot indexed by `timeline_count` is the relocated data-end
  sentinel.

The following is **observed in retained Stage-5 evidence**:

- five high-frequency main-VM opcode-`0x87` PCs map to decoded Stage-5 ECL
  instruction boundaries;
- 81 exact captured `0x87`-to-successor advances align with 105 immediate
  activation batches containing 1,520 bullets; and
- the target subroutines contain time-zero fire opcodes.

These observations prove that auxiliary contexts are available source
topology. They do not prove which auxiliary instruction emitted a realized
bullet, exact operands or geometry, or hit-causal coverage.

## Phase A: Zero-Read Pointer Inventory

The existing first-64 contiguous enemy blob already contains
`enemy+0x3384..+0x3393`. Phase A decodes four raw context pointers for every
active slot from that same blob:

- slot index, exact enemy pointer, and active flags;
- four fixed-position raw context pointer values;
- total non-null pointer count; and
- explicit invalid non-null pointer count under the same bounded 32-bit
  process-address check used for main ECL PCs.

Pointer inventory is a separate fixed-position row set from main-VM rows.
The existing main row layout is not silently extended. New traces receive a
new schema and inventory layout version; old schema-11 traces remain accepted
with auxiliary pointer coverage explicitly absent.

Phase A performs no additional process-memory read. A non-null pointer proves
only that one context address was present inside the manager-frame-bracketed
enemy record; it is not a coherent snapshot of the pointed-to heap context.

## Phase B: Bounded Auxiliary Context Capture

Phase B is not authorized by pointer presence alone. The retained Stage-5
density/churn report selects one bounded native compact batch under an
explicit process/frame bracket. A background immutable-version service
remains a fallback transport only if native batch timing or contention fails;
one Python process read per non-null pointer is rejected.

The selection is based on **observed physical evidence**: non-null contexts
per capture are p50/p95/p99/max `4/26/32/34`; 56 of 57 unique pointer values
are reused at more than one `(slot, auxiliary-index)` over the route; and the
104-byte active-VM projection payload is only
`416/2704/3328/3536` bytes at p50/p95/p99/max. Full `0x24B0` context copies
would cost `37568/244192/300544/319328` bytes and are not selected.

The capture budget must declare maximum enemies, contexts, bytes, reads, wall
time, freshness, and behavior on pointer churn. It must recheck the owning
enemy slot identity and all four pointers after capture. Changed, freed,
reused, unreadable, or out-of-range contexts remain unstable or unresolved;
they may not be synthesized as terminated VMs.

The minimum exact auxiliary observation is:

- owner slot and enemy pointer;
- auxiliary index and context pointer;
- VM PC at context `+0x08`;
- raw timer bits and the same complete projected live-local layout within the
  active VM used by the main inventory;
- signed call depth and, for interpretation crossing call/return, the exact
  restorable `0x228`-byte saved frames `[0, depth)` from the `+0x230` area;
  physical slot 15 remains distinct from the maximum 15 restorable frames;
  and
- before/after owner-pointer evidence sufficient to reject context reuse.

No per-context cold read may be added to the live issue path merely because a
pointer is non-null.

## Phase C: Exact Runtime ECL Image Identity

Runtime instruction identity is observed once per immutable stage image, not
guessed from PC alignment:

1. read the `g_ecl_file_context` image base and validate it as a bounded
   32-bit process address;
2. read the fixed `0x48`-byte runtime header;
3. require magic `0x800`, bounded signed counts, the second context word equal
   to image base `+0x48`, and a relocated data-end sentinel inside a declared
   maximum image size;
4. read exactly the declared image length once;
5. reread the context base and reject pointer churn;
6. preserve a SHA-256 digest of the exact relocated runtime bytes;
7. normalize only the relocation sites observed in `ecl_load_file` by
   subtracting the captured image base from all 16 header slots and all
   `subroutine_count` table entries; and
8. compare the normalized bytes and SHA-256 digest byte for byte with the
   decoded static ECL artifact.

No other byte may be normalized. A mismatch reports its first differing
offset and remains unresolved runtime identity. File name, stage index,
matching PC boundaries, or an affine base are insufficient substitutes.

The immutable image version includes executable identity, route/stage
identity, runtime base, image length, relocated digest, normalized digest, and
the compared file digest. Consumers require exact-version equality.

## Information, Equivalence, And Causality

Two phase-A states are identical only when their manager-frame support,
owner slot/pointer/flags, four raw auxiliary pointers, and main-VM inventory
agree. They are not control-equivalent because pointed-to VM state, ordinary
slots `64..479`, callbacks, RNG, transforms, native emitters, and future
pointer allocation remain hidden.

Two phase-B states additionally require exact captured auxiliary VM state and
stable owner-pointer evidence. Even then they are not source-equivalent until
the interpreted instruction, operands, origin/template state, RNG branch, and
realized slot-generation join agree.

Runtime-image equality establishes instruction-byte identity only. It does
not establish that a captured PC executed before a particular birth or that
an instruction produced the realized geometry.

Offline joins use recorded frame support. Hidden branches that produce the
same observation remain merged and unresolved; the controller may not choose
separately after learning an unobserved source.

## Uncertainty, Horizon, Resources, And Deadline

- Phase A's horizon is one first-64 manager-frame-bracketed enemy snapshot.
- Phase C's horizon is one immutable stage resource load.
- A later source interpretation horizon is declared in physical manager-frame
  support and includes time scale, scheduler order, and all supported control
  flow.
- Missing slots, null pointers, unreadable contexts, image mismatch, timeout,
  and cancellation enlarge the unresolved-source set.
- Phase A is bounded by 64 records and four pointer decodes per active record.
- Phase C is bounded by one fixed header, one declared maximum image, and two
  context-base observations. It is not repeated per decision.
- Phase B receives no issue-time authority until its bounded design passes
  Windows timing and physical freshness tests.

The live fallback remains the current Boolean policy plus a fresh local hard
certificate. Research observation failure cannot delay or weaken fallback.

## Safety Invariants And Falsifiers

- Hard no-Bomb and complete-mask semantics remain unchanged.
- All new data is trace-only and cannot alter issued input.
- Existing non-opt-in traces and enemy-body results remain byte/behavior
  compatible.
- Phase A must issue zero additional enemy-pool RPM.
- Old schema-11 traces remain parseable and explicitly lack auxiliary pointer
  coverage.
- A pointer is not a VM snapshot and cannot be interpreted as one.
- Static ECL bytes cannot receive runtime authority without successful exact
  normalization and byte comparison.
- Only the relocation sites observed in `ecl_load_file` may differ during
  normalization.
- An unstable owner, pointer set, stage image, or manager-frame bracket
  remains unstable evidence.

Phase A is falsified by any body/main-row parity change, added RPM, missing
active owner, wrong pointer bits, schema ambiguity, or live policy change.
Phase C is falsified by accepting malformed counts, an out-of-range sentinel,
pointer churn, a non-relocation mismatch, or a file whose bytes differ after
normalization.

## Independent Oracles And Tests

The independent scalar tests construct raw blobs and runtime images without
calling production encoders. They must cover:

1. inactive owners produce no pointer rows;
2. active owners preserve all four pointer bits and owner identity;
3. null pointers are valid absence while invalid non-null pointers are
   counted explicitly;
4. pointer decoding leaves every existing main row unchanged;
5. capture uses the same one-blob manager-frame bracket and read count;
6. schema-11 and the new schema both parse with explicit coverage;
7. a synthetic relocated ECL image normalizes byte for byte to its static
   source;
8. malformed magic/counts/end sentinel/context word and pointer churn fail
   closed; and
9. a one-byte non-relocation mutation cannot receive exact-image identity.

## Performance And Value Gates

- Report pointer-decode and serialization deltas separately from the retained
  main-inventory baseline on Linux and Windows.
- Retain p50/p95/p99/p99.9/max and bytes per active owner/decision.
- Phase A has a hard zero-extra-RPM gate.
- Phase C reports total one-shot bytes, reads, wall time, and normalized
  comparison cost outside the issue boundary.
- A small bounded regression is weighed against exact source coverage and
  deadline slack; it is not an automatic veto.
- Unbounded cold I/O, hidden per-context issue reads, ambiguous schema, or
  action-path coupling fail regardless of signal.
- If Phase A signal is dense and valuable but serialization is costly, prefer
  delta encoding or post-issue reporting. If Phase B reads are costly, prefer
  one native batch or background immutable-version capture.

## Formal Review

1. **Control-equivalent histories:** pointer-only, auxiliary-state, and
   exact-image projections are separated; none claims equivalence for omitted
   source state.
2. **Uncertainty and causality:** pointer churn, context reuse, missing slots,
   scheduler timing, and unobserved operands remain explicit unresolved
   branches.
3. **Physical versus proxy:** image equality answers byte identity; auxiliary
   capture answers source-state availability; neither alone answers physical
   bullet causation or survival.
4. **Algorithm and falsifier:** bounded deterministic decoders and exact byte
   normalization are checked against independent synthetic oracles and reject
   every undeclared difference.
5. **Deadline and fallback:** pointer decode reuses paid bytes; image identity
   is one-shot; auxiliary heap capture remains outside issue authority until a
   separately measured bounded delivery exists.

## Ordered Checkpoints

1. **Complete:** Add phase-A auxiliary pointer rows from the existing blob
   with explicit schema evolution and deterministic tests.
2. **Complete:** Benchmark decode and serialization deltas on Linux and
   Windows.
3. **Complete in synthetic evidence:** Implement the bounded runtime-image
   identity primitive and independent normalization oracle.
4. **Partially complete:** Retain one focused physical pointer-density trace
   without changing action authority. The shipped-runtime stage-image capture
   remains pending.
5. **Complete:** Select native compact batch using measured density, payload,
   pointer reuse, read-count risk, and deadline slack.
6. **Complete:** Revalidate call-depth/saved-frame offsets, freeze the native
   batch ABI/budget, implement scalar/native parity, and pass adversarial,
   Windows timing, and bounded visible-retry physical delivery gates.
7. **Next under a separate fixed physical contract:** Capture and
   byte-compare one exact shipped Stage-5 runtime image.
8. Only after exact auxiliary state exists, lower a fail-closed fire/control
   subset and join emission descriptors to realized slot generations and
   first-hit causal witnesses.
