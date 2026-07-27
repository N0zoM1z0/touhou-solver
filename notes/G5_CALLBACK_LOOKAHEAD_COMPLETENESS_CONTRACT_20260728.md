# G5 Callback-Lookahead Completeness Contract

Date: 2026-07-28

Status: fixed pre-implementation correction contract for CE-0147. This note
changes neither the callback recurrence nor physical input authority. It
defines which bounded lookahead results may be lowered as a complete future
schedule and which remain an observed prefix followed by `UNKNOWN`.

This refines
`TH08_FUTURE_BULLET_BIRTH_OBSERVATION_CONTRACT_20260728.md`,
`PIPELINE_ROOT_AND_HAZARD_COVERAGE_CONTRACT_20260727.md`, and the callback-12
mechanism in `DANMAKU_SYSTEM.md`.

## Physical Question

Given one capture-aligned main-ECL VM snapshot and an immutable instruction
view, has bounded literal traversal established every callback-12 event for
the declared `1..H` physical-frame horizon, or only a prefix?

The same distinction applies to the trace-only birth-intent traversal: an
empty event/intent tuple is a complete negative result only when traversal
covered the declared horizon for that source.

## Observed Counterexample

The accepted schema-v7 Stage-4A run
`lunatic_route2_stage4a_unattended_20260728_070838` contains 2,405 callback
lookaheads with `horizon_covered=false`:

| Stop reason | Rows | Rows with tagged bullets | Maximum tagged bullets |
| --- | ---: | ---: | ---: |
| `instruction_limit` | 1,350 | 0 | 0 |
| `repeated_state` | 1,055 | 975 | 1,367 |

All 2,405 rows published zero events and attached zero callback changes.
Every instruction-limit row is spell 57. The repeated-state rows demonstrate
that incompleteness is not merely a report field: existing tagged bullets can
be linearly projected after the traversal ceased.

**Observed:** the current capture path assigns `lookahead.events` to the
lowering input without checking `horizon_covered`.

**Inferred:** an empty tuple after an incomplete traversal does not establish
absence of a later callback. Linear continuation after that boundary is an
unknown-direction proxy.

**Not established:** no retained hit has yet been causally attributed to one
omitted callback.

## Result Contract

Each callback or birth-intent result declares:

```text
LookaheadCoverage {
  requested_horizon_frames: H,
  status: COMPLETE | UNKNOWN,
  covered_through_frame: c,
  unknown_from_frame: null | c + 1,
  stop_reason,
  stop_frame,
}
```

The frame support is relative to the VM snapshot:

- `COMPLETE` requires `horizon_covered=true`; `covered_through_frame=H` and
  `unknown_from_frame=null`.
- `UNKNOWN` requires `horizon_covered=false`;
  `covered_through_frame=max(0, stop_frame-1)` and
  `unknown_from_frame=covered_through_frame+1`.
- `horizon` and `terminate` are complete for the declared main-VM source.
  Termination does not cover child, auxiliary, interrupt, native, or future
  source creation.
- `instruction_limit`, `repeated_state`, unsupported control/source/state,
  invalid payload/opcode, cache miss, read failure, and exception are
  incomplete.
- Repeated state is not automatically a periodic proof. Such a proof must
  include every state component that can affect control, tag selection,
  callback parameters, timer progress, and source topology, plus the
  scheduler semantics that advance or resume the VM.

`events` and `intents` in an incomplete result are named prefix evidence.
They remain useful for trace diagnosis but do not constitute a complete
horizon schedule.

## Consumption And Fallback

The callback result exposes two separate interfaces:

1. `prefix_events` for trace/reporting; and
2. `complete_events` for lowering, which is unavailable when coverage is
   `UNKNOWN`.

No consumer may reach into a raw tuple and silently treat it as a complete
negative schedule. The compatibility helper must raise on incomplete
coverage.

The live controller may continue its pre-existing observed-snapshot proxy
only with explicit `UNKNOWN` trajectory coverage. An incomplete result:

- cannot add a hard future-event certificate;
- cannot make a G1 coverage slab authority-eligible;
- cannot support B5/B6 coverage or a survival-promotion claim;
- cannot be repaired by reducing the instruction cap; and
- cannot be converted to a nominal callback branch.

This first correction prevents partial results from masquerading as complete.
It does not by itself provide a conservative spatial envelope after
`unknown_from_frame`. A later action-authority proposal must either:

- prove a complete schedule;
- derive a conservative containing envelope for every affected tagged
  bullet; or
- mark the relevant hard certificate unavailable and use the declared
  fallback.

## State, Information, And Causality

The traversal state includes at least:

```text
(instruction pointer, timer value, relative physical frame,
 tag mask, callback angle/speed)
```

The birth-intent traversal additionally includes deferred-fire state and every
modeled emission state. Any omitted mutable component invalidates a
repeated-state completeness proof.

Only the capture-aligned snapshot and immutable instructions already
available at that decision may be used. The post-issue birth classifier
remains lookup-only and trace-only. No later runtime callback observation may
be inserted into an earlier decision.

## Horizon, Resources, And Deadline

- The declared horizon remains 80 frames for the physical G5 trace.
- Bounded traversal keeps the 256-instruction cap.
- This correction adds no RPM and performs no cold expansion on the issue
  thread.
- Coverage bookkeeping is constant-size. It must not weaken the closed B4
  `0.20/0.40/2.00 ms` observer gate.
- Missing or malformed coverage metadata fails the new trace schema/audit.

## Safety Invariants

- Survival is hard and Bomb bit `0x02` remains forbidden.
- `UNKNOWN` is not free space and is not an empty event certificate.
- Prefix events are causal evidence only inside their declared covered
  prefix.
- Source coverage and schedule coverage remain orthogonal.
- Callback completeness does not resolve future births, transform programs,
  lasers, enemy bodies, CE-0120, or the input pipeline.
- No schema migration may reinterpret old incomplete rows as complete.

## Formal Review

1. **Control-equivalent histories:** no control histories are merged by this
   correction. Lookahead results are comparable only under identical
   capture, VM, instruction-view, difficulty, horizon, and model identity.
2. **Uncertainty and causality:** incomplete traversal produces one
   `UNKNOWN` suffix, not separate controller choices for hidden callbacks.
3. **Physical answer:** a complete result answers the callback schedule only
   for the declared captured main-VM source and horizon. An incomplete result
   answers only which events were found in the visited prefix.
4. **Algorithm and falsifier:** the bounded literal scanner is exact only
   for its visited deterministic path. A callback inside a claimed complete
   interval, missing prefix event, incorrect stop support, or accepted
   incomplete lowering falsifies the implementation.
5. **Deadline and fallback:** construction remains within the existing
   capture/trace boundary. Invalid or incomplete metadata cannot delay issue
   or gain authority; complete-event lowering is unavailable.

## Ordered Gates

1. Add explicit coverage support to callback and birth-intent results.
2. Make the compatibility/lowering API reject incomplete results.
3. Preserve prefix evidence and distinguish prefix versus lowered events in
   sensing trace.
4. Bump the birth trace/audit schema and fail closed on missing or
   inconsistent coverage metadata.
5. Retain deterministic instruction-limit, unsupported-flow, terminate,
   horizon, and repeated-state fixtures.
6. Re-audit the retained schema-v7 physical trace to quantify which
   incomplete rows contain potentially affected tagged bullets.
7. Only then choose between a proved repeated-state scheduler model, a
   conservative envelope, or certificate unavailability for the unresolved
   suffix.
