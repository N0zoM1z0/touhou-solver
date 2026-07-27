# G5 Native Bullet-Birth Extraction Contract

Date: 2026-07-28

Status: offline implementation and Linux/Windows gates complete; an
explicitly selected Stage-4A trace gate is proposed. This contract authorizes
a separate native extraction library, binding, differential oracle,
benchmark, and that focused physical repeat. It adds no planner field,
future-hazard coverage, Bomb, issue, strategy, or physical action authority.

This contract refines the B4 performance boundary in
`TH08_FUTURE_BULLET_BIRTH_OBSERVATION_CONTRACT_20260728.md` after four failed
physical gates retained in `G5_BULLET_BIRTH_PHYSICAL_GATE_20260728.md`.

## Physical Question

Can the already captured 1,536-slot hostile-bullet pool be scanned once,
after current input issue, to produce exactly the same retrospective
birth/anomaly evidence as the independent Python observer while meeting the
unchanged physical wall-time gate?

The experiment does not predict a bullet, lower an ECL intent to geometry, or
make a movement decision. Its only physical objective is to reduce optional
trace overhead so later future-event research can run without materially
changing controller cadence.

## State, Observation, And Output

At one observation the extractor receives:

- the exact persistent pool blob already captured by the sensor;
- record count, stride, and TH08 field offsets supplied by the adapter;
- whether a previous accepted observation exists;
- the previous compact state and age for every slot;
- the fixed maximum bootstrap age; and
- capture-frame provenance retained by the Python wrapper.

For slots in native ascending order it reads:

- state;
- native timer age;
- position, velocity, and size only for evidence candidates; and
- transform flags only for evidence candidates.

It returns:

- active-slot count;
- ordered evidence slot;
- transition code;
- current and previous state/age;
- six raw float32 geometry values;
- transform flags;
- per-row finite-geometry flag; and
- updated full-slot previous state/age for the next observation.

The Python wrapper owns capture support and constructs the existing
`BulletBirthObservation` and read-only `BulletBirthEvidenceBatch`. Trace
observation/residual semantics do not change; schema v5 adds mandatory
backend provenance.

## Exact Recurrence

For slot \(i\), current state \(s_i\), age \(a_i\), previous state
\(\bar{s}_i\), previous age \(\bar{a}_i\), and bootstrap limit \(B\):

1. \(s_i = 0\): no evidence.
2. \(s_i \ne 0\) and \(a_i < 0\): `invalid_timer`.
3. No previous observation, \(s_i \ne 0\), and \(0 \le a_i \le B\):
   `bootstrap_recent`.
4. Previous observation exists, \(s_i \ne 0\), \(a_i \ge 0\), and
   \(\bar{s}_i = 0\): `activation_edge`.
5. Previous observation exists, both states are active, \(a_i \ge 0\), and
   \(a_i < \bar{a}_i\): `timer_regression`.
6. Otherwise: no evidence.

The cases are ordered as written. Invalid age dominates bootstrap,
activation, and regression. Activation dominates regression because a
previous inactive slot has no active-age continuation. Output order is
strictly increasing slot order.

On any validation or capacity failure the call returns an error and must not
partially update the previous-state arrays. The live wrapper resets the
observer and emits an explicit trace error under the existing fail-closed
path.

## Information And Actuation Boundary

- The extractor runs only after the current action transaction.
- It receives no desired input, route objective, action mask, policy, or
  planner state.
- It performs no process-memory read and issues no input.
- It may condition only on the current captured blob and the preceding
  accepted blob summary.
- Capture-frame uncertainty remains the wrapper's
  `[previous_frame_before, frame_after]` support. Native speed does not turn
  that interval into an exact birth frame.
- Same-mask no-write, pickup delay, recursive cadence, manager-frame freeze,
  and all live fallback semantics remain unchanged.

## Library And Ownership Boundary

The experiment uses a separate optional trace library:

- Linux: `libtouhou_bullet_birth_trace.so`;
- Windows: `touhou_bullet_birth_trace.dll`.

It does not add or change a symbol in the production viability library and
does not change `native/abi_symbols_v1.txt`. The C++ implementation lives
under a dedicated trace module; the TH08 offsets remain in the Python TH08
adapter/binding.

The wrapper may fall back only when the caller explicitly selected the
Python backend. Selecting the native backend with a missing library or symbol
is an error; silently changing the measured backend would invalidate the
gate.

## Approximation And Authority

The native algorithm is intended to be exact for the finite retrospective
recurrence above. It is not an approximation to future birth geometry.

What remains omitted:

- births not visible in either captured pool generation;
- exact within-interval activation time;
- ECL sources and source ownership;
- pool-capacity competition before allocation;
- template, origin, aim, RNG, rank, and transform dependencies;
- stop/resume, redirect/reversal, lasers, and future callbacks; and
- all successor hazard coverage.

These omissions leave future coverage `UNKNOWN` from the first successor.
Even exact native/Python parity proves implementation parity only.

## Differential And Adversarial Gate

The native backend must match the independent Python observer on:

- empty and full pools;
- first-observation bootstrap boundaries;
- activation, release, slot reuse, and timer regression;
- negative, zero, and extreme int32 ages;
- all uint16 nonzero states;
- finite, NaN, and infinite geometry;
- transform flags;
- capture-frame spans and resets;
- ascending evidence order;
- mixed candidates across every one of the 1,536 slots; and
- deterministic randomized multi-generation sequences.

Parity compares both scalar witnesses and canonical columnar records,
including float32 bit patterns before JSON non-finite normalization. The
Python oracle remains independent and must not call the native binding.

A single mismatch falsifies exactness. The smallest failing generation pair
must be retained in `notes/COUNTEREXAMPLES.md`; the native backend remains
outside the physical gate.

## Performance And Publication Gate

Fixed isolated Linux and Windows profiles measure:

- zero, 1, 8, 32, 33, 592, and 1,536 evidence candidates;
- sparse and dense active pools;
- cold/warm ordering interleaved with the Python observer and planning decode;
- p50/p95/p99/p99.9/max wall time;
- canonical record-plus-JSON time separately; and
- decode/control-path nonregression.

The physical B4 limits remain:

- observer p95 at most `0.20 ms`;
- observer p99 at most `0.40 ms`;
- observer maximum at most `2.00 ms`;
- no added RPM;
- hard no-Bomb;
- no worse accepted decision-cadence boundary; and
- same-iteration trace durability with explicit errors flushed immediately.

Thread CPU time is not an acceptance signal. Schema-v4 showed 15.625-ms
Windows accounting quanta and cannot resolve the required interval.

The backend may be proposed for another focused Stage-4A trace only after
Linux/Windows parity, adversarial cases, fixed benchmarks, complete quick
suites, and explicit backend provenance pass. Stage 5/6 remains closed until
Stage-4A semantics and the physical wall gate pass.

## Falsifiers

The claim is falsified by any:

- Python/native evidence mismatch;
- changed trace schema or residual result from the same fixture;
- partial previous-state mutation on error;
- extra pool read;
- missing explicit backend provenance;
- production ABI change;
- current-issue work before input dispatch;
- wall-limit failure;
- cadence regression;
- unexpected Bomb/input bit `0x02`;
- stale or cross-epoch previous state; or
- attempt to use the result as future-hazard or action authority.

## Offline Gate Result

The separate library and binding now implement this contract. Production
planner exports remain unchanged. Trace schema v5 records
`observation_backend`, and residual-audit schema v3 rejects a v5 row without
`python` or `native` provenance.

Observed validation:

- four Linux and four Windows focused tests pass;
- 16 deterministic randomized generations cover all 1,536 slots and match
  the independent Python observer exactly;
- bootstrap, activation, release/reactivation, regression, negative/extreme
  age, uint16 state, transform flags, NaN/Inf geometry, reset, interval
  validation, canonical records, float32 values, and atomic capacity failure
  pass;
- C++ compiles with `-Wall -Wextra -Werror`;
- complete Linux/Windows quick suites pass `792/792` in
  `8.826/15.449 s`, with three existing Windows skips.

The first native wrapper allocated ctypes views, pointers, and count objects
on every observation. On Windows a 5,000-call probe retained a repeatable
`5.409 ms` tail at call 1,741. Disabling cyclic GC reduced maximum to
`0.286 ms`, but disabling GC was rejected as the correction. CPU-11 affinity
still failed at `4.8275 ms`. Reusing the persistent blob view, every output
pointer, and count storage reduces the same GC-enabled probe maximum to
`0.0988 ms`.

Final unpinned fixed profiles:

| Platform | Full p95/p99/max ms | 592-birth p95/p99/max ms | Decode ratio |
| --- | --- | --- | ---: |
| Linux | `0.0120/0.0202/0.3080` | `0.0570/0.0904/0.1344` | `0.931` |
| Windows | `0.0109/0.0124/0.0250` | `0.0452/0.0639/0.1433` | `0.930` |

All eight density/burst profiles pass the fixed
`0.20/0.40/2.00 ms` limits. Retained final report SHA-256 values are
`bfb106b6970f98610c2537cd40113a81d1cd6ef0a7ac1b751ec9c943b71dc667`
for Linux and
`1f73455491c8ccb83d1a53ab7a8c2c0f1792ebf2844f91faa4920de5adebcd63`
for Windows.

Same-version Python reference reports are retained rather than comparing
against an older benchmark schema. Linux/Windows full-density p95 is
`0.0153/0.0222 ms`, and 592-birth p95 is `0.1185/0.1295 ms`. The Linux
reference's observer profiles pass, but its noisy decode-interleaving ratio
is `1.097`, so its combined benchmark gate is false; the Windows reference
passes at `1.045`. Their SHA-256 values are
`343e623c03db8a7fb43f0db4388c52ee472d0d7906551e805b60ecc0bc3c228a`
and
`fb27dfde363a4581b94f3cfe01b27611fe4f4ec6b31a264bee97d58a249224df`.
These isolated comparisons are diagnostic, not physical cadence evidence.

This is isolated eligibility only. B4 remains physically failed until an
accepted Stage-4A run uses `--trace-bullet-births
--bullet-birth-backend native` and passes wall time, cadence, hard no-Bomb,
durability, supervisor completion, and cleanup.
