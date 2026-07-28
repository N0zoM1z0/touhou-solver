# G5 Auxiliary Literal Fire-Cycle Offline Gate

Date: 2026-07-28

Status: accepted offline implementation and timing checkpoint; no live
guidance, future-geometry, collision, planner, or action authority

## Result

The first contracted auxiliary-ECL event class now has a bounded production
lowerer, a structurally independent raw-byte oracle, exact shipped-image
tests, compact retained evidence, and passing Linux/Windows deadline gates.

This accepts only an unresolved **direct-fire intent schedule** for literal
transform/fire/jump cycles. It does not claim that a requested bullet was
realized, identify its owner or source lifetime, resolve dynamic descriptor
parameters, apply shared transform state, allocate a pool slot, produce
geometry, or prove future-hazard containment.

## Provenance And Exact Workload

The code was developed from parent checkpoint `14fb180` plus the exact
working-tree changes enclosed by the commit containing this note.

The immutable Stage-5 ECL fixture is:

- `artifacts/decoded/ecldata5.ecl`;
- 47,224 bytes;
- SHA-256
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`;
- observed auxiliary targets 69, 72, and 73; and
- literal cycle periods 8, 8, and 30 integer ECL timer ticks.

The fixed maximum-density benchmark contains 34 requests in the observed
target ratio `69:8`, `72:9`, `73:17`, with two cycle periods covered per
request. Its immutable workload identity digest is
`eb0a22d974dd2e9855f3558d35f600e77da70a3322b1dd803f976f0aa635f453`.
This is a deterministic target-mix workload, not a claim that all physical
34-context batches contain only three distinct PC/timer states.

## Implementation Boundary

`scripts/th08_ecl_auxiliary.py` is now a 40-line stable compatibility facade.
The implementation is split under `scripts/th08_ecl_auxiliary_core/`:

- `model.py`: immutable capture state, intent, transform, and result records;
- `image.py`: exact normalized runtime-instruction indexing;
- `timer.py`: native-compatible float32 timer stepping;
- `descriptor.py`: transform/direct-fire decoding and residual dependencies;
- `lowerer.py`: bounded fail-closed instruction traversal; and
- `batch.py`: request-local intent-equivalence canonicalization and compact
  result mapping.

The independent byte walker and inventory/report code live under
`scripts/analysis/auxiliary_ecl_event/`. Benchmark workload and timing
ownership live under `scripts/benchmarks/auxiliary_ecl_event/`. None of this
logic was added to `th08_live/controller.py`.

Batch canonicalization is intentionally narrow. Its key contains instruction
pointer, integer/fractional timer state, horizon, and the defensively retained
previous-timer field even though the current lowerer does not read it.
Difficulty, time scale, instruction image, and resource bounds are common
arguments. Owner identity, scheduler marker, and VM locals are not resolved by
this event class and remain later dependencies. The batch preserves one result
index for every input request and tests reject merging a different timer
state.

## Semantics And Fail-Closed Coverage

**Observed/revalidated native semantics:**

- dispatch compares the instruction time with integer elapsed;
- a literal `0x04` jump writes integer elapsed, preserves timer fraction, and
  applies its signed relative PC in the same update;
- positive time scale above the native threshold advances integer time
  directly, while slower scale accumulates float32 fraction;
- literal `0x6F` defines transform state;
- `0x60..0x68` are direct-fire descriptor operations; and
- `0x01` is an exact terminal state with no future event on that VM path.

**Implemented finite result:**

- exact timer-domain intent offsets on the accepted literal path;
- optional physical-frame offsets only with a positive finite time scale;
- exact difficulty eligibility;
- exact terminal and horizon completion;
- explicit stop reasons for nonliteral jump/transform, unsupported control,
  malformed/unavailable instructions, past timers, repeated state,
  instruction budget, invalid time scale, and physical-step exhaustion; and
- every unresolved emission/source/geometry dependency retained in the
  intent record.

Physical timing exhaustion does not erase exact timer-domain events. Any
unsupported control or descriptor path remains `UNKNOWN`; timeout and
instruction exhaustion never become a completed empty schedule.

## Independent And Retained Evidence

The independent oracle interprets raw instruction and VM bytes without
importing production transition, timer, descriptor, or result code. Tests
cover:

- literal fire cycles and exact subroutines 69/72/73;
- native-direct and slow fractional time;
- fraction preservation across jump;
- physical-step exhaustion;
- difficulty skip;
- terminal completion;
- nonliteral transform/jump;
- malformed and unavailable instructions;
- unsupported opcodes `0x05`, `0x28`, `0x34`, and `0x35`;
- instruction time before current elapsed;
- zero-tick repeated state;
- instruction budget;
- invalid time scale;
- exact image identity and byte mutation; and
- batch equivalence and non-equivalent timer separation.

The retained Stage-5 spell-107 inventory is:

- `artifacts/viability_audit/g5_auxiliary_ecl_event_inventory_stage5_20260728_200739.json`;
- file SHA-256
  `03782866ebdd06a8a95cc8ce341ebe0ac7713056e6e5457852d8dc091662a1f8`;
- internal report digest
  `28e0626f71aa30fe813c8dacc9ff46749f70a512313ec69164a1b7e5849ff66b`;
- 123 successful schema-v3 batches and 3,214 usable depth-zero contexts; and
- target counts `69:789`, `72:818`, `73:1607`.

Two independent regenerations are byte-identical. The old trace retains
active-VM hashes rather than raw PC/timer/locals, so its event replay status
correctly remains `unavailable_hash_only`.

## Performance Gate

Accepted reports use 2,000 measured iterations after 200 warmups and include
lower, compact serialization, and lower-plus-serialize p50/p95/p99/max.
Immutable request records are constructed once outside the measured
recurrence; production lowering and result/record allocation remain inside.
The final runner also attributes sample overlap with cyclic GC.

| Platform | 34-context lower+serialize p50 | p95 | p99 | max | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Linux CPython 3.13.5 | 0.1906 ms | 0.2426 ms | 0.2996 ms | 0.4708 ms | pass |
| Windows CPython 3.12.10 | 0.2110 ms | 0.2394 ms | 0.2544 ms | 0.5030 ms | pass |
| Windows adjacent repeat | 0.2175 ms | 0.2324 ms | 0.2479 ms | 0.5215 ms | pass |

The fixed limits are p95 at most 0.50 ms, p99 at most 1.00 ms, and maximum
at most 3.00 ms. Reports:

- `artifacts/benchmarks/auxiliary_ecl_event_linux_20260728.json`, SHA-256
  `c5e879466f291c2711e6b712fca55f5ac6760ba258f3c76f57ba59b043be6ec3`;
- `artifacts/benchmarks/auxiliary_ecl_event_windows_20260728.json`, SHA-256
  `3f16a9e4cd3c664615fd92353edab7bde2277983d2ee55788cad7894658eccd0`;
- `artifacts/benchmarks/auxiliary_ecl_event_windows_repeat_20260728.json`,
  SHA-256
  `a2ea06d441819ab1b86c1a901ba861dd36e3f3aa6a4ca31300bff3ad67fd69e1`.

CE-0166 retains two incompatible Windows failures rather than hiding them:
one pre-correction report failed p95 at `0.6451 ms`, and one report after
prebuilding requests failed only maximum at `15.6743 ms`. The two accepted
adjacent reports have zero combined-phase cyclic-GC overlap, so the long tail
must not be labeled GC; host scheduling/contention remains inferred rather
than observed. Failed reports:

- `artifacts/benchmarks/auxiliary_ecl_event_windows_request_allocation_failure_20260728.json`,
  SHA-256
  `2ffc27fae966c2965c3878685347c1052f0ea51de2d8f0db43e0fcb7716ab46d`;
- `artifacts/benchmarks/auxiliary_ecl_event_windows_prebuilt_max_failure_20260728.json`,
  SHA-256
  `792ec224d2780cc33693aacad9dc9fa8545bc82a4735834b5ae48dbb4750f30f`.

The adjacent passes accept the isolated offline checkpoint, not stable live
maximum authority. This does not include native capture, runtime image
selection, trace queueing/flushing, live contention, or issue cadence.

## Verification

- focused lowerer/oracle suite: 16 tests passed;
- focused auxiliary report/benchmark suite: 5 tests passed;
- focused ECL family: 90 tests passed;
- focused auxiliary family: 32 tests passed;
- focused runtime-ECL family: 12 tests passed;
- Linux quick suite: 997 tests passed in 11.366 seconds; and
- Windows quick suite: 997 tests passed in 18.153 seconds with three existing
  platform skips.

Ruff passes over all added production, analysis, benchmark, and test files.
No physical run was required because this checkpoint changes no live path.

## Authority And Next Gate

The lowerer remains offline/default-off. It must not feed a hazard envelope,
viability recurrence, planner, publication service, or actuator.

The next ordered gate is one narrow post-capture runtime service:

1. consume the already coherent auxiliary active-VM bytes without adding RPM;
2. require exact immutable runtime-ECL identity and version;
3. retain replay-capable structural/raw state plus the derived compact result;
4. fail closed on identity miss, unsupported control, deadline, or any
   unresolved result;
5. benchmark capture plus lowering plus record delivery under live
   contention; and
6. run a focused default-off Lunatic Stage-5 spell-107 physical gate with an
   independent offline replay audit.

Only after repeated clean delivery may one separately contract resolution of
owner/source lifetime, dynamic parameters, transforms, realized births, and
geometry.

Lunatic Stage 3 is now an explicit later independent physical workload because
historical attempts had many deaths. It first needs its own fresh baseline,
phase/hit attribution, Power-0 route/resource profile, and event/source
coverage inventory. Stage-5 subroutine identities, target mix, nonspell
strategy, or timing results must not be generalized to Stage 3.
