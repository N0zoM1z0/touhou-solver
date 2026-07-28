# G5 Materialization-Tail Attribution Contract

Date: 2026-07-28

Status: fixed pre-implementation trace-only attribution contract for CE-0152.
It changes no hostile-bullet recurrence, callback model, planner, worker
configuration, process read, input, Bomb rule, or physical action authority.

This follows the accepted schema-v8 Stage-4A run
`lunatic_route2_stage4a_unattended_20260728_075455`. Callback completeness
validation passed, but one GIL-held native birth observation took
`8.9834 ms` against the unchanged `2.00 ms` maximum. Its native call took
`0.0335 ms`; Python materialization took `8.9333 ms`.

## Physical Question

During a materialization wall tail, did the issue-thread actually execute an
abnormally large amount of work, or did wall time advance while that thread
was descheduled?

If the latter, was one of the controller's known background futures definitely
in flight across the observer interval? Future overlap is contention evidence,
not proof that the overlapping worker caused the deschedule.

## Observed Trigger

Run `20260728_075455` retained 14,903 native observations:

- total p50/p95/p99/p99.9/max was
  `0.0636/0.1448/0.2007/0.3858/8.9834 ms`;
- exactly one row exceeded `2.00 ms`;
- frame 15,809 had 24 evidence rows and phase wall times
  `0.0019/0.0335/8.9333/0.0147 ms` for
  prepare/native-call/materialize/controller-residual;
- all completed cyclic-GC counters were zero;
- adjacent 24-row materializations were
  `0.0741/0.0575/0.0527/0.0707 ms`; and
- the next-highest 20–28-row materialization was `0.2658 ms`.

**Observed:** output count alone does not explain the tail.

**Hypothesized:** OS descheduling or background native-worker contention
interrupted a normally short materialization.

**Not observed:** existing Windows `time.thread_time()` samples are quantized
at about 15.625 ms and cannot distinguish the alternatives.

## Unchanged Physical And Model Contract

The observer state, input blob, previous slot state/age, scan order, status
codes, output columns, capture support, history update, and atomic failure
behavior remain those in
`G5_NATIVE_BULLET_BIRTH_EXTRACTION_CONTRACT_20260728.md`.

The callback `COMPLETE`/`UNKNOWN` boundary remains
`G5_CALLBACK_LOOKAHEAD_COMPLETENESS_CONTRACT_20260728.md`. This experiment
does not alter the 256-instruction callback traversal or repair its unknown
suffix.

No histories are merged or split for control. Telemetry is retrospective and
cannot enter the current or later live action.

## Current-Thread Cycle Observation

On Windows, the issue thread samples `QueryThreadCycleTime` on its current
thread pseudo-handle at the same four boundaries already used for wall
attribution:

```text
c0 = observer entry
c1 = immediately before native call
c2 = immediately after native call
c3 = after immutable observation materialization
```

The reported unsigned deltas are:

```text
prepare_cycles     = c1 - c0
native_call_cycles = c2 - c1
materialize_cycles = c3 - c2
```

A local Windows runtime probe on 2026-07-28 observed
`QueryThreadCycleTime(GetCurrentThread())` succeeding with error zero.

Cycle counts are not milliseconds. CPU migration, frequency, and platform
implementation prevent a fixed conversion. They are compared only with the
same phase and evidence-count bucket in the same run. A high wall sample with
ordinary cycle count supports descheduling; a proportional cycle increase
supports executed-work investigation. Neither result identifies which
external thread or process caused it.

The implementation must:

- cache the Windows function signatures and pseudo-handle;
- call the Windows API through a GIL-held `PyDLL` boundary so telemetry does
  not reintroduce the released-GIL intervention rejected by CE-0149;
- allocate no per-row ctypes object after construction;
- return an explicit unsupported/query-failed source instead of fabricating
  zero cycles;
- reject a decreasing boundary or mixed available/unavailable boundaries;
- retain raw integer deltas without converting them to time; and
- keep the existing wall intervals authoritative for B4.

Linux may report `unavailable_non_windows`. Windows physical attribution
requires `windows_query_thread_cycle_time` and three valid deltas.

## Background-Future Overlap

The controller samples `Future.done()` immediately before and after the native
birth observer for the futures it already owns:

- rolling corridor solve;
- post-published survival solve; and
- background enemy-pool capture.

Each future records one of `absent`, `done`, or `inflight` at both endpoints.
`inflight` at both endpoints is definite interval overlap. A state transition
is partial/endpoint-ambiguous overlap. `Future.done()` is lookup-only; this
diagnostic may not wait, cancel, submit, reprioritize, or consume a result.

Candidate, supplemental, or prewarm services that are not represented by
these three futures remain explicit omitted contention sources. The game,
Windows scheduler, other processes, native internal workers after an
ambiguous endpoint, page faults, and allocator behavior also remain omitted.

## Trace Schema And Audit

Birth trace schema v9 adds:

```text
observation_diagnostics.thread_cycles {
  source,
  prepare,
  native_call,
  materialize
}

observer_contention {
  corridor_future: {before, after},
  survival_future: {before, after},
  enemy_future: {before, after},
  omitted_sources
}
```

Residual-audit v7 must fail closed when a successful schema-v9 native row:

- omits the cycle object or any required key;
- publishes a Windows source with a non-integer, negative, or missing delta;
- publishes integer deltas for an unavailable source;
- omits a future state or uses a value outside
  `absent|done|inflight`; or
- changes existing segment/GC reconciliation or provenance rules.

Schemas v1 through v8 retain their original semantics. Python-backend rows
must not fabricate native cycle attribution.

The compact report adds:

- phase-cycle distributions;
- phase cycles by evidence-count bucket;
- wall/cycle values and future endpoints for every over-budget sample;
- counts by definite/ambiguous/no-known-future overlap; and
- a separate `cycle_attribution_available` gate.

Audit `passed` still requires the fixed observer wall limits. Cycle evidence
may explain a wall failure but never convert it to a pass.

## Deadline And Perturbation Boundary

This is post-issue trace-only work inside the existing observer interval. It
adds no RPM and no new background task. The telemetry overhead is real and
must remain inside reported wall time.

Before physical use:

- exact Python/native observation parity remains unchanged;
- production native ABI remains exactly 46 symbols;
- four boundary reads must be allocation-stable after construction;
- all fixed Linux/Windows observer profiles still pass
  `0.20/0.40/2.00 ms`;
- ABBA decode p95 ratio remains at most `1.05`;
- focused and complete Linux/Windows suites pass; and
- missing Windows cycle attribution makes the physical experiment
  ineligible.

The controller stays unpinned and normal priority. GC stays enabled. No
worker priority, affinity, count, cadence, publication rule, or fallback is
changed by this contract.

## Decision Rule

For a materialization-dominant sample above `2.00 ms`:

1. Compare its materialization cycles with the same-run 17–32-evidence cycle
   distribution.
2. Ordinary cycles plus exceptional wall time supports descheduling.
3. Exceptional cycles supports executed materialization work and a separate
   copy/allocator investigation.
4. Definite future overlap narrows the contention candidates but is not
   causal proof.
5. No known overlap keeps OS/game/omitted-source scheduling open.
6. Mixed or unavailable evidence remains unresolved.

No intervention is authorized by this contract. A later correction must be
fixed separately:

- executed-work evidence may justify packed-copy/materialization changes with
  exact record parity;
- descheduling correlated with a known worker may justify an isolated
  priority/worker-count/contention experiment with publication-age and
  survival effects measured; and
- absent correlation may require ETW or another scheduler-native probe.

Repeating physical runs until one has a passing maximum is rejected.

## Formal Review

1. **Control-equivalent histories:** telemetry-only differences map to the
   same controller state and action. No timing or overlap field is consumed.
2. **Uncertainty and causality:** future states are sampled, not chosen.
   Endpoint overlap does not assign cause or let the controller condition on
   hidden scheduling.
3. **Physical answer:** cycle deltas can separate executed-thread work from
   wall absence under the shipped Windows runtime. They cannot identify the
   scheduler cause by themselves.
4. **Algorithm and falsifier:** decreasing/missing cycles, invalid future
   states, output mismatch, excessive observer overhead, or any action
   dependence falsifies implementation eligibility.
5. **Deadline and fallback:** all overhead remains inside post-issue wall
   timing. Missing telemetry fails the attribution gate; live fallback and
   hard no-Bomb issue semantics are unchanged.

## Ordered Gates

1. Add an allocation-stable current-thread cycle sampler with deterministic
   injected-counter tests.
2. Add phase cycle deltas without changing observer output.
3. Capture future endpoint states around the observer without waiting or
   mutation.
4. Add schema-v9/audit-v7 fail-closed validation and deterministic reports.
5. Pass focused, complete Linux/Windows, ABI, observer, and ABBA gates.
6. Run one explicit GIL-held schema-v9 Stage-4A attribution trial.
7. Fix a separate intervention contract from the observed classification;
   require two consecutive passing physical regressions before B4 recloses.
