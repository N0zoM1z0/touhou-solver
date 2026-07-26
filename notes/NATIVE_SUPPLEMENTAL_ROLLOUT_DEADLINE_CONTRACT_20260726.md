# Native Supplemental Rollout And Deadline Contract

Date: 2026-07-26

Status: implemented and evaluated; synchronous delivery rejected by CE-0131

## Decision

The immutable supplemental continuation lane keeps width four and moves its
complete rollout, per-frame hazard queries, canonicalization, and reduction
behind one persistent native C++ workspace.  Crossing Python once per rollout
replaces the current per-step Python draft construction, array allocation,
hazard call, and reducer call.

This is an implementation change to the already-declared finite proposal
lane.  It does not enlarge its physical authority.  The historical lane is
computed first and remains the only result on native unavailability,
validation failure, version mismatch, timeout, cancellation, exception, or
empty completed output.

## Physical Problem Contract

### Objective

Minimize the optional lane's current-issue latency and tail under four native
global-planner workers without changing its completed finite result or
delaying the historical action past issue time.  Hard no-Bomb survival remains
the physical objective.

### State and observations

One query owns an immutable snapshot containing:

- initial projected player/node state and previous direction/focus;
- the complete action table and the effective allowed root actions;
- local hold, delay, horizon, width, target and boundary parameters;
- complete same-query certificate, survival, safety, recovery and repair
  arrays; and
- frame-major, already-projected bullet and laser arrays plus the enemy-body
  snapshot used by the Python lane.

The native call may consume only this snapshot.  It may not read the game,
wait for later observations, use a later global publication, or mutate the
historical beam.

### Actions and transitions

The action alphabet, clamped motion, action-hold recurrence, step-one allowed
set, transition risk, float32 hazard positions, uncertainty, collision,
clearance, risk accumulation, quantized canonicalization, stable tie order,
and fourteen-column lexicographic reduction are identical to
`search_supplemental_local_beam`.

The complete endpoint list is published only after every requested horizon
step completes.  No partial beam is a valid answer.

### Uncertainty and horizon

The change carries exactly the uncertainty already present in the projected
hazard frames and action attributes.  It does not repair future births,
unmodeled transforms, recursive cadence, input-pipeline beliefs, or the open
frozen-manager-clock boundary.  Width four and the caller's local horizon
remain bounded, unknown-direction proposal approximations.

### Safety invariants

- The historical lane and its final candidate remain byte-for-byte outside
  the native supplemental workspace.
- A completed native endpoint vector must match the independent Python lane
  in endpoint fields and order, subject only to stated floating tolerances.
- Deadline/cancellation/error paths publish no endpoint and select the
  historical action.
- A stale or mismatched immutable query identity is not reusable.
- Existing global-membership, componentwise-hard, route-gate, repair/reserve,
  fresh issue recertification and no-Bomb admission checks remain mandatory.
- Four global viability workers remain configured; the optional lane may not
  lower their worker limit to manufacture a pass.

## Deadline And Cancellation Semantics

The Python caller creates one absolute `perf_counter_ns` deadline before
packing/calling the native query.  If packing reaches it, native code is not
entered.  The native ABI receives the remaining nanoseconds once and converts
them immediately to one `steady_clock` deadline.  The deadline never slides or
renews at a beam step.

The fixed synchronous supplemental budget for the Windows gate is **5.000
ms**, measured from Python packing start through completed endpoint decoding.
Native code checks cancellation/deadline between rollout expansions and at
bounded intervals while scanning hazards.  Status values distinguish
complete, cancelled, deadline, and invalid input.  Cancellation is
generation-scoped: cancelling a running query cannot be erased by a new query
reset, and a workspace is not destroyed until its active call exits.

Any non-complete status causes immediate historical fallback.  Telemetry
records backend, elapsed time, status, completed/not-completed, and whether
the historical action was used.  Timeout is not logged as a finite-model
failure; returning or selecting a partial beam is.

## Fixed Validation And Promotion Gate

### Correctness

1. Deterministic edge cases and randomized generated cases compare independent
   Python and complete-native endpoint vectors, including order, first/last
   action, collisions, risk, minimum and immediate clearance.
2. Native full-boundary, current native-reducer, and pure-Python modes must
   produce the same final decision and hard/admission fields on all retained
   direct roots where the full native call completes.
3. Forced timeout and cross-thread cancellation must return no partial output;
   `choose_action` must retain the historical action and expose the status.
4. Disabled-path behavior remains unchanged.

### Same Windows direct-root contention gate

The retained root set, three rounds, four variants, global viability problem,
normal process priority, and four global workers from
`SUPPLEMENTAL_DIRECT_ROOT_WINDOWS_CONTENTION_GATE_20260726.md` stay fixed.
The previous latency, background-throughput, finite-contract and zero-new-miss
limits stay fixed.

To prevent an apparent pass obtained by always timing out:

- at least **95%** of supplemental-eligible worker-four queries must complete
  inside the 5.000-ms end-to-end supplemental budget;
- at least **90%** of the action changes made by the previous completed
  width-four implementation on the same roots must be retained;
- every timeout/cancellation/mismatch must return the paired historical
  action; and
- completed full-native results must have zero Python endpoint/final-decision
  mismatch.

These thresholds were fixed before seeing full-native results.  Failure moves
the lane to exact-version asynchronous publication; it does not justify
loosening the synchronous deadline.

## Five Formal Review Questions

1. **Which histories merge?**  Exactly those already merged by the immutable
   supplemental-lane snapshot.  Native packing adds no observation.  Hidden
   pipeline, cadence, future-birth and clock-freeze histories remain outside
   the claim and are not known control-equivalent.
2. **Is the recurrence causal?**  Yes relative to the supplied finite
   projection: root choice precedes every modeled step and no later replay row
   is read.  Omitted physical uncertainty remains omitted, not silently
   resolved.
3. **What would an exact solve answer?**  Only the bounded supplemental
   endpoint proposal problem.  It would not prove unrestricted physical
   survival or global optimality.
4. **What is solved or bounded?**  The C++ routine must exactly implement the
   Python bounded recurrence.  Width truncation and quantized merging remain
   unknown-direction.  Any endpoint/order/decision mismatch, partial timeout
   publication, or historical-fallback violation falsifies the implementation
   claim.
5. **Can the result be consumed in time?**  Only a complete result before the
   fixed absolute deadline and with exact immutable identity may enter final
   admission.  Otherwise the already-computed historical action is consumed.
   The unchanged Windows contention gate decides whether synchronous use is
   viable.

## Observed Implementation And Gate Result

The implementation adds one persistent native workspace and one C ABI query
covering draft expansion, frame-major bullet/laser hazard evaluation, moving
enemy bodies, transition risk, quantized canonicalization, reduction and
complete endpoint publication.  The ABI distinguishes complete, cancelled,
deadline and invalid status.  Cancellation is generation-scoped, and
workspace destruction waits for an active call to exit.

Deterministic and randomized comparisons found zero completed endpoint/order
or final-decision mismatch against the independent Python recurrence.
Cross-thread cancellation and forced deadlines exposed no partial result.
Linux and Windows native libraries built successfully.

**Observed Windows result:** on the unchanged 253-root, three-round,
four-global-worker gate, 729/729 eligible queries completed and retained all
294 reference action changes.  Completed native/Python mismatch and
historical-fallback mismatch counts were zero.  The native boundary itself
cost `0.876/1.365/1.942 ms` median/p95/max.

The fixed delivery gate nevertheless failed.  Paired complete
supplemental-minus-historical latency was `1.249/7.054/53.721 ms`, above both
the `5.000 ms` p95 and one-frame maximum limits, and one hybrid deadline proxy
became a new miss.  This triggered the predeclared exact-version asynchronous
follow-up; it does not permit a looser synchronous threshold.  Retained
artifact:
`artifacts/benchmarks/hard_supplemental_full_native_direct_root_contention_windows_20260726.json`
(SHA-256
`c3a2af979ae4a969aebaace85f0a725ce50c1d597c700a1e2db394d0095f5ed7`).
