# G5 Native Birth GIL-Boundary Experiment

Date: 2026-07-28

Status: offline implementation and Linux/Windows gates complete. One first
explicit `gil-held` Stage-4A diagnostic is eligible; no physical pass is
assumed.

This contract follows the schema-v6 physical attribution retained in
`G5_NATIVE_BIRTH_TAIL_ATTRIBUTION_CONTRACT_20260728.md`. Run
`lunatic_route2_stage4a_unattended_20260728_062321` observed 17 samples above
the fixed `2.00 ms` limit. Every sample was dominated by the C ABI call
interval, no completed cyclic-GC collection overlapped any phase, and normal
native-call p50/p95/p99 was only `0.0365/0.0603/0.1125 ms`.

## Physical Question

Does retaining the Python GIL across the exact trace-only native
bullet-birth call remove the collection-free multi-millisecond call-wall
tail without changing:

- the hostile-pool observation and recurrence;
- output count, order, bits, validation, or atomic error behavior;
- the production 46-symbol planner ABI;
- current input issue or hard no-Bomb behavior;
- controller affinity, priority, GC state, or the fixed wall limits; or
- future-hazard and physical action authority?

Python 3.11's local `ctypes` runtime documents and implements two relevant
call boundaries:

- `ctypes.CDLL`: releases the GIL during a foreign call and reacquires it
  afterward;
- `ctypes.PyDLL`: uses the same C calling convention but does not release the
  GIL.

The experiment names these modes `gil-released` and `gil-held`. Loading and
calling the existing trace DLL through `PyDLL` is the only intervention.
There is no C++ or exported-symbol change.

## State, Observation, And Histories

The finite observer state remains:

- all 1,536 current slot states and signed native ages;
- previous slot states and ages;
- previous and current capture-frame support; and
- the fixed maximum bootstrap age.

The native recurrence, ascending-slot scan, status codes, geometry columns,
transform flags, finite flags, history update, and failure atomicity remain
exactly those in
`G5_NATIVE_BULLET_BIRTH_EXTRACTION_CONTRACT_20260728.md`.

Call mode is provenance, not model state. Two physical histories differing
only in call mode map to the same retrospective observation when their input
pool blobs and prior observer states agree. Exact record equality is required
across Python, `gil-released`, and `gil-held` trackers.

## Information, Actuation, And Contention

- Construction remains default-off and requires
  `--trace-bullet-births --bullet-birth-backend native`.
- A separate `--bullet-birth-native-call-mode` explicitly selects
  `gil-released` or `gil-held`; the default remains `gil-released`.
- Observation remains after current input dispatch. No call-mode or timing
  result is available to the action already issued.
- The trace consumer is offline. Neither mode changes planner state, scoring,
  fallback, policy publication, or input.
- Holding the GIL can delay other Python threads for the duration of the
  native scan. This is a real contention intervention, not a semantically
  invisible refactor. Physical cadence, plan timing, policy age, next-input
  visibility, and trace durability remain acceptance measurements.
- The controller remains unpinned and normal priority. Cyclic GC remains
  enabled. No collection is forced outside the measured boundary.
- Bomb bit `0x02` remains forbidden.

## Provenance And Fail-Closed Schema

Trace schema v7 adds `native_call_mode`:

- a native row must contain exactly `gil-released` or `gil-held`;
- a Python row must contain `null`;
- successful native rows still require reconciled segment and GC telemetry;
- a failed native row retains its explicit call mode but no fabricated
  diagnostics; and
- schemas v1 through v6 retain their original audit semantics.

Residual-audit schema v5 reports the call-mode distribution. A schema-v7
trace with a missing, invalid, mixed, or backend-incompatible mode fails
validation. Session metadata and the benchmark report also retain the exact
mode.

## Offline Gates

Before a physical run:

1. boundary/nonfinite and 16-generation full-pool output must be bit-exact
   among the independent Python scalar observer and both native modes;
2. reset, validation, capacity failure, history atomicity, and GC telemetry
   tests must pass in both native modes;
3. loader tests must prove `gil-released` uses `CDLL`, `gil-held` uses
   `PyDLL`, and mode-specific function ownership cannot alias accidentally;
4. trace/audit tests must reject absent, invalid, mixed, or fabricated mode
   provenance while retaining schemas v1 through v6;
5. the fixed Linux and Windows observer profiles must pass
   `0.20/0.40/2.00 ms` separately for both modes;
6. ABBA decode nonregression remains at p95 ratio `<= 1.05`; and
7. the exact production ABI and complete Linux/Windows quick suites must
   pass.

Affinity results are inadmissible for this gate.

## Physical Decision Rule

The first explicit `gil-held` Stage-4A run is diagnostic:

- if any observation exceeds `2.00 ms`, retain its segmented witness and
  reject GIL handoff as a sufficient correction;
- if p95/p99/max pass, retain it as one candidate correction pass, not a
  closed B4 result;
- only two consecutive complete `gil-held` Stage-4A runs that each pass
  validation, timed intent, `0.20/0.40/2.00 ms`, hard no-Bomb, durability,
  cadence, supervisor, and cleanup gates may close this specific B4 tail;
- a later regression reopens the counterexample; and
- hit count is reported but is not compared causally across RNG-distinct
  attempts.

Stage 5/6 remain closed until this performance gate and CE-0147's explicit
incomplete callback handling both pass. Closing this tail alone does not
narrow first-successor `UNKNOWN` or authorize future geometry.

## Formal Questions

1. **Control-equivalent histories:** call mode is retrospective
   instrumentation provenance. Equal pool/prior-state histories must produce
   bit-identical observer records. Holding the GIL may change scheduling, so
   cadence and delivery are measured rather than assumed equivalent.
2. **Uncertainty and causality:** the observer remains post-issue and
   trace-only. No hidden branch, future value, or timing result selects an
   action.
3. **Physical answer:** two consecutive complete physical passes can reject
   the previously frequent tail under the declared runtime boundary. They do
   not prove the absence of every possible OS preemption or improve the
   future-hazard model.
4. **Algorithm and falsifier:** there is no recurrence approximation. Any
   output mismatch falsifies semantic equivalence. Any retained
   `gil-held` native-call tail above `2.00 ms` falsifies GIL handoff as a
   sufficient performance correction.
5. **Deadline and fallback:** the work remains after current issue.
   Invalid/missing provenance fails the audit; over-budget work keeps B4
   failed. Live action always remains the existing Boolean policy plus fresh
   local certificate.

## Offline Gate Result

The mode-specific loader now owns separate library/function caches:
`gil-released` loads through `ctypes.CDLL` and `gil-held` through
`ctypes.PyDLL`. Each tracker retains its exact function object and publishes
its immutable mode. The native DLL and production 46-symbol ABI are
unchanged.

Trace schema v7 and residual-audit v5 retain and validate
`native_call_mode`. Native rows require one valid mode, Python rows require
`null`, and a trace mixing native modes fails closed. Schemas v1 through v6
remain accepted under their original semantics. Practice/full-route session
metadata and every launch layer preserve the explicit mode.

Eight native focused tests pass. Both call modes match the independent Python
observer across 16 randomized full-pool generations, boundary/nonfinite
values, reset, validation, capacity failure, and history updates. Loader
tests independently prove `CDLL`/`PyDLL` selection and distinct function
ownership. Trace, audit, CLI, and provenance tests pass.

The unpinned fixed observer gate reports:

| Platform/mode | Full p95 ms | 592-birth p95 ms | Full/592 max ms | Decode ratio |
| --- | ---: | ---: | ---: | ---: |
| Linux `gil-released` | `0.0119` | `0.0598` | `0.0426/0.1341` | `1.0166` |
| Linux `gil-held` | `0.0109` | `0.0588` | `0.0563/0.1408` | `1.0293` |
| Windows `gil-released` | `0.0118` | `0.0465` | `0.0273/0.1840` | `1.0382` |
| Windows `gil-held` | `0.0098` | `0.0452` | `0.0251/0.1177` | `1.0181` |

All eight observer profiles in all four reports pass
`0.20/0.40/2.00 ms`; all ABBA decode ratios pass `1.05`. Canonical LF report
SHA-256 values in table order are:

- `a3c0501054340cbc09c57562d3ae5ee7a18b4e91360ad15ce52c779e8d6e6a6e`;
- `a1ed1c4b32d5c9022e2e7dba5947b187e89e65a6aa566fc41a328450eb20e3cc`;
- `76448d054a7c160589ed61b880ef1d54daf6e3cad13ed75fc4dce671ad8bd5bc`;
- `305cdbc199cf62f8f22addd7e625b715112c67bd7b7b9e2713bbc4cfcb9b11ac`.

Complete Linux/Windows quick suites pass `801/801` in `8.900/15.699 s`,
with three existing Windows skips. The first unpinned, GC-enabled,
explicit-`gil-held` Stage-4A diagnostic is eligible. B4, CE-0147,
future-event coverage, hit-reduction claims, and physical action authority
remain unchanged.
