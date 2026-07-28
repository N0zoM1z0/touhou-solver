# G5 Nonspell Main-VM Source Shadow Contract

Date: 2026-07-28

Status: phase-A implementation, cross-platform benchmark, focused Stage-5
physical observation, and offline source-availability join complete. The
shadow has no live guidance, hazard, feasibility, or publication authority.
Results and the ordered next gate are retained in
`G5_NONSPELL_MAIN_VM_STAGE5_RESULT_20260728.md`.

This contract follows
`G5_CAPTURE_ALIGNED_VM_LOCAL_SHADOW_CONTRACT_20260728.md` and the physically
rejected ready-derived-parent checkpoint recorded by CE-0161. The rejected
checkpoint found no ready derived parent for the observed Stage-5 age-one and
age-two waves. It did not falsify direct ECL emission by ordinary enemies.

## Physical Objective And Authority

The physical objective remains hard no-Bomb survival. The immediate research
question is narrower:

> Before a newly active bullet wave appears, was a main ECL VM belonging to an
> active ordinary enemy observed in a state that can causally explain that
> wave?

Phase A inventories capture-time VM state only. It changes no controller
action, command cadence, delay support, planner recurrence, clearance,
fallback, route profile, or issue semantics. It may not create predicted
bullets or change a `COMPLETE`, `UNKNOWN`, viable, or safe-action result.

Phase B may later interpret a declared fail-closed ECL subset offline. It may
not reach live lowering until an independent oracle, retained physical joins,
deadline evidence, and the existing finite-model authority gates all pass.

## Observed Shipped-Game Evidence

The following is **observed statically** in the connected shipped TH08 IDA
database:

- the ordinary enemy record's active main ECL context is rooted at
  `enemy+0x07F8`;
- `enemy_ecl_vm_step` contains a direct call to
  `bullet_emitter_spawn_pattern` at `0x0041B8E7`;
- `enemy_ecl_emit_bullets` at `0x00422720` handles ECL fire opcodes
  `0x60..0x68`, evaluates the instruction's type, color, two counts, two
  speeds, two angles, and transformation flags, then calls
  `bullet_emitter_spawn_pattern` at `0x00422B6D`; and
- `bullet_emitter_spawn_pattern` at `0x00430E10` expands the two count loops
  into individual bullets. Its other observed caller at `0x0043077E` is the
  already investigated bullet-transform path.

The following is **observed in repository code**:

- each local decision already reads the first 64 ordinary enemy records as
  one manager-frame-bracketed contiguous blob;
- each record is `0x53D0` bytes, so the already-paid blob contains
  `enemy+0x07F8..+0x085F`;
- the current decoder extracts bodies and discards the raw blob;
- current one-enemy ECL prediction is spell-owner-only; and
- cold `EclInstructionCache.instruction` misses issue target-process reads,
  while `cached_instruction` is lookup-only and fails closed on a miss.

It is therefore **inferred** that phase-A inventory can reuse the existing
enemy-prefix RPM without another enemy-pool read. It is only
**hypothesized** that the Stage-5 unexplained waves have a relevant source in
the first 64 ordinary slots.

## Phase-A Observation

For every active slot in the captured 64-record prefix, decode an immutable
compact observation from the same blob:

- slot index and exact enemy pointer;
- active enemy flags;
- current main-VM instruction pointer;
- raw float32 bits of timer fraction and signed integer timer elapsed;
- integer locals `10000..10007`;
- raw float32 bits for float locals `10016..10023`; and
- scratch integers `10036..10039`.

The layout reuses
`th08-ecl-vm-local-projection-v1`. Raw bits are retained instead of JSON
floating-point values. An active slot whose VM pointer is null or otherwise
invalid remains an explicit invalid slot; it must not silently disappear.

The inventory records:

- manager-frame bracket and stability;
- scanned prefix size;
- active slot count;
- valid VM count;
- invalid active slot indices;
- compact fixed-position VM rows; and
- decode wall time inside the already-existing prefix-capture boundary.

Phase A performs no instruction-memory read and no time-scale read. Those
values are unnecessary to establish exact capture-time PC/timer/local
identity. The omission is explicit and forbids physical-frame lookahead.

## Information, State Equivalence, And Causality

Two phase-A observations are identical only when their manager-frame support,
slot/pointer identity, flags, PC, timer bits, and complete projected locals
agree. This does not make the corresponding physical histories
control-equivalent:

- the scan omits ordinary slots `64..479`;
- spell owners outside the ordinary pool are observed by a different path;
- auxiliary VMs, call frames, interrupts, deferred emitters, RNG, dynamic
  player/enemy values, and native non-ECL sources are not represented; and
- a PC identifies an instruction address but not its bytes unless an
  exact-runtime instruction observation exists.

The phase-A record is made after the already-bracketed prefix capture. Offline
analysis must use the recorded frame support and may not align a VM row to a
later bullet birth by row order, wall time, or nearest-neighbour convenience.
Observation-compatible hidden branches stay merged as unresolved.

## Phase-B Interpretation Boundary

The first eligible phase-B experiment is lookup-only:

1. use only exact runtime instructions already present in the warm immutable
   cache;
2. evaluate only the previously contracted fail-closed opcode and local-state
   subset;
3. stop before every cache miss, call/return, interrupt, unobserved dynamic
   dependency, unsupported write, or unknown branch;
4. retain the source enemy pointer and emission descriptor; and
5. join the candidate to later realized slot births offline with explicit
   capture-frame support.

The issue thread must not cold-expand ordinary enemy ECL. A later prewarm
service would require an immutable runtime-image/version key, cooperative
cancellation, newest-version-first work, and lookup-only consumers.

An exact instruction cache hit is not by itself a source proof. Direct source
authority requires an interpreted fire opcode, exact operands, exact emission
origin/template semantics, and an observation-compatible realized-birth join.

## Uncertainty, Horizon, And Resources

- The observation horizon is one captured prefix snapshot.
- A later interpretation horizon must be declared in manager-frame units and
  include time scale before mapping ECL timer to physical frames.
- The action set and controller resource constraints are unchanged.
- Missing slots and missing instructions enlarge the unresolved-source set;
  they do not become losing, safe, or absent.
- Timeout and budget exhaustion preserve all completed observations and leave
  unvisited sources unresolved.

## Safety Invariants And Fallback

- Hard no-Bomb remains unchanged.
- Inventory data is trace-only and cannot alter issued input.
- No invalid VM may be synthesized into a null or terminating instruction.
- No static-file instruction may be treated as the live runtime instruction
  without exact image/address identity.
- Unstable manager-frame brackets remain unstable evidence.
- Errors flush promptly and leave current live Boolean policy plus fresh local
  hard certification unchanged.

## Independent Oracle And Falsifiers

The independent Python scalar oracle must construct raw enemy records without
calling the production decoder. Required deterministic cases are:

1. inactive records never produce VM rows;
2. active initialized records preserve pointer, flags, PC, timer bits, and
   every projected local exactly;
3. active null/invalid PCs remain explicit invalid slots;
4. records outside the declared prefix are omitted and counted as outside
   scope;
5. body and VM decoding from the same blob retain one identical frame bracket;
6. old callers that do not request inventory retain identical bodies and
   perform identical reads; and
7. trace serialization is compact, deterministic, and schema/version
   validated.

Phase A is falsified by any added enemy-pool RPM, body parity change, missing
active slot, bit mismatch, unstable observation labelled stable, or live
policy change.

The direct-source hypothesis is falsified for a retained target wave if all
observation-compatible relevant first-64 main VMs are excluded by exact
runtime instruction evidence. Failure to find an instruction or a source
outside the prefix is unresolved, not falsification.

## Performance And Value Gates

Performance is one part of the decision, not an isolated veto.

- Hard phase-A gates: no additional enemy-pool RPM; unchanged non-opt-in
  behavior; deterministic compact output; bounded work over 64 records; no
  control-path authority.
- Report decode-only and total prefix-capture p50/p95/p99/p99.9/max on Linux,
  Windows, and a relevant physical workload.
- Report trace bytes per decision and active/valid/invalid VM counts.
- Compare the combined birth-observer and trace boundary with the retained B4
  limits, but interpret a regression together with physical source coverage,
  causal hit coverage, fusion opportunities, and deadline slack.
- A small or controllable regression may be accepted when it resolves a
  material hit cause or expands exact safe authority.
- Zero physical signal, unbounded cold I/O, missed issue deadlines, or loss of
  fail-closed behavior cannot be justified by isolated functionality.
- If signal is useful but overhead is too high, retain the evidence and
  optimize by fusing decode into the existing enemy-prefix pass, compacting
  deltas, moving post-issue serialization off the issue boundary, or adding a
  versioned prewarm service. Do not discard useful source information merely
  because the first implementation is not final.

## Formal Review

1. **Control-equivalent histories:** phase A distinguishes exact observed
   first-64 main-VM states but explicitly declines equivalence outside that
   projection.
2. **Uncertainty and causality:** only capture-time fields are recorded;
   hidden instructions and omitted VMs are never maximized separately or
   guessed.
3. **Physical versus proxy:** phase A answers source-state availability, not
   future bullet feasibility. Phase B remains a proxy until exact realized
   birth joins and source coverage are established.
4. **Algorithm and falsifier:** bounded deterministic decode is checked by an
   independent raw-layout oracle; any bit/read/body mismatch falsifies it.
5. **Deadline and fallback:** opt-in trace work is bounded, performs no cold
   instruction reads, has no live authority, and falls back by omission.

## Ordered Checkpoints

1. Implement the compact first-64 inventory behind a narrow module and prove
   one-blob body/VM parity with deterministic tests.
2. Benchmark Linux and Windows decode/serialization overhead before a
   physical trial.
3. Add an explicit trace opt-in; ordinary birth tracing must remain unchanged.
4. Run one focused hard no-Bomb Stage-5 workload because CE-0161 retained the
   unexplained two-age waves there.
5. Join inventory PC/timer histories to realized birth waves offline and
   report source availability separately from source proof.
6. Only if physical signal exists, design cached-only instruction
   interpretation or a bounded prewarm service and contract its deadline
   separately.

## Phase-A Outcome

The physical signal exists. The retained Stage-5 trace maps 64/64 unique PCs
to legal decoded ECL instruction boundaries under one unique affine base.
Twenty exact captured opcode-`0x60` advances align one-to-one with 20
activation batches containing 260 bullets. IDA and the same trace additionally
identify opcode `0x87` delegation into four heap auxiliary VM contexts:
81 exact starts align with 105 activation batches containing 1,520 bullets.

These are static source-availability results, not runtime-byte or source
proof. The next contract must cover exact runtime ECL image identity and
bounded auxiliary-context observation. Main-PC-only interpretation is
structurally incomplete and must not be promoted as complete source coverage.
