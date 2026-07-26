# Exact-Version Asynchronous Supplemental Publication

Date: 2026-07-26

Status: implemented for offline contention evaluation; proposal/shadow only

## Trigger And Decision

The complete native synchronous lane passed finite parity and made its own
rollout fast (`0.876/1.365/1.942 ms` median/p95/max under four workers), but
the fixed end-to-end Windows gate still failed at
`1.249/7.054/53.721 ms` paired median/p95/max with one new hybrid deadline
miss.  Completion and previous-action-change retention were both 100%, and
completed native/Python and fallback mismatch counts were zero.  The fixed
contract therefore requires exact-version asynchronous publication rather
than another synchronous threshold adjustment.

The asynchronous lane submits the complete native query to one dedicated
newest-wins worker.  Historical planning and historical terminal evaluation
remain authoritative and continue immediately.  The consumer performs one
nonblocking exact-identity lookup; a miss, stale identity, timeout,
cancellation, error, or unfinished query keeps the historical endpoint.

## Physical Problem Contract

### Objective

Retain useful completed width-four proposals without putting optional rollout
latency on the current issue critical path.  Hard no-Bomb survival and the
historical action remain authoritative.

### State and immutable identity

One identity contains the caller-supplied immutable physical/policy version,
the explicit local pipeline root, float-exact projected player state, previous
input state, delay support, hold/horizon/width/mode, route target/deadline,
effective allowed actions, and same-query repair/recovery/safety/survival
attributes.  The caller-supplied version must uniquely bind the already
projected bullet, laser and body snapshot.  A caller that cannot establish
that binding may not enable asynchronous publication.

The worker job owns references to the immutable projected arrays used by that
identity.  Publication is a pair `(exact identity, complete endpoint tuple)`.
Lookup compares the complete identity; it never returns “nearest”, older, or
shape-compatible work.

### Actions, recurrence, uncertainty and resources

The native recurrence, action alphabet, hazard semantics, horizon, width,
admission filters and omitted physical uncertainties are unchanged from
`NATIVE_SUPPLEMENTAL_ROLLOUT_DEADLINE_CONTRACT_20260726.md`.  Asynchrony
changes delivery only.  It does not grant the proposal proof authority.

There is one background worker and one persistent native workspace.  Submit
replaces any pending job.  If an older query is active, its workspace is
cooperatively cancelled.  The worker discards every result whose revision is
no longer newest.  Thus current work is not queued behind a stale FIFO.

### Publication deadline and fallback

The job retains the fixed 5.000-ms absolute budget beginning at submit-side
packing.  The consumer never waits for that deadline.  It evaluates the
historical terminal continuation, then performs lookup only:

- exact complete hit: the supplemental endpoints may enter the unchanged
  terminal/admission comparison;
- miss/stale/timeout/cancel/error: zero supplemental endpoints and historical
  action;
- partial endpoint: impossible by the native all-or-nothing ABI and treated
  as an implementation failure if observed.

One scheduler yield after submit lets the dedicated worker start; it is not a
completion wait.  Submit, lookup and yield overhead are measured on the issue
thread.  Background compute time is reported separately only for consumed
hits.

## Safety Invariants

- Historical beam construction, endpoint and terminal labels are computed
  without waiting for optional work.
- Publication cannot overwrite or mutate the historical beam.
- Exact identity and newest revision are both required.
- Timeout/cancellation/error paths cannot publish partial nodes.
- A miss never starts cold expansion on the consumer lookup.
- Closing the service cancels and joins the active native call before
  destroying its workspace.
- Existing global-membership, componentwise-hard, route, continuation,
  issue-recertification and no-Bomb checks remain mandatory.

## Five Formal Review Questions

1. **Which histories merge?**  Only histories already merged by the finite
   local model and explicitly bound by one immutable version.  Different
   versions, roots, float states, targets, delay supports or action attributes
   cannot share a publication.  Unmodeled cadence, future births and clock
   freezes remain outside the claim.
2. **Is the recurrence causal?**  Yes relative to the supplied projection.
   The worker receives no later observation.  Lookup is for the same
   decision identity, not a future replay label.
3. **What does an exact result answer?**  The same bounded supplemental
   proposal problem as the synchronous implementation, not unrestricted
   physical survival or global optimality.
4. **What is solved or bounded?**  Completed native work exactly matches the
   independent Python bounded recurrence.  Width/quantization remain
   unknown-direction.  Wrong-identity publication, stale revision
   publication, a partial result, or a nonhistorical miss fallback falsifies
   the delivery claim.
5. **Can it be consumed in time?**  Lookup never waits.  Only a result already
   complete after overlapping historical work is consumable; otherwise the
   historical action is already available.  The same Windows direct-root
   contention gate, augmented with hit/retention/parity/fallback counts,
   decides whether the overlap is useful and side-effect-free.

## Observed Iterations

The first implementation submitted only after the historical beam and
therefore overlapped too little work: four-worker completion was `14.5%` and
reference action-change retention `21.4%`.  Moving submission before the
historical beam raised both to 100%, but the paired p95 increment remained
`8.018 ms`.  Moving supplemental terminal labeling into the optional worker
made completion and retention worse (`90.95%/88.10%`) and was reverted.

The compact iteration reports are retained rather than treating only the
final variant as evidence:

- late submit:
  `artifacts/benchmarks/hard_supplemental_exact_async_direct_root_contention_windows_20260726.json`,
  SHA-256
  `aa29b8ccba50917ba66e07ed01acbc0fefc1ee47ff0571708f332988d36de8e8`;
- early submit:
  `artifacts/benchmarks/hard_supplemental_exact_async_early_submit_direct_root_contention_windows_20260726.json`,
  SHA-256
  `855fa036e2952ab4481897dc01662a20dcc6b4357fe6913d446f7f4c23d0f6a3`;
- native terminal experiment:
  `artifacts/benchmarks/hard_supplemental_exact_async_native_terminal_direct_root_contention_windows_20260726.json`,
  SHA-256
  `f1b4e96f7f076d311d96c0356b3737ff50dbb53c361c0b94903d5c39860d0c72`.

The retained implementation submits before the historical beam, publishes
native endpoints only, evaluates the historical terminal score on the issue
thread, performs lookup without waiting, and runs the optional Windows worker
below normal priority.  Service telemetry distinguishes submitted, published,
deadline, cancellation, stale discard and error outcomes.

## Final Identical Windows Gate

**Observed:** the final 253-root, three-round, four-global-worker gate had:

- zero historical, global-membership, componentwise-hard, route,
  continuation, Bomb, supplemental-failure, issue-transaction or
  issue-global violations;
- 728/729 eligible completed publications (`99.863%`);
- 294/294 retained reference action changes;
- zero completed native/Python and historical-fallback mismatches;
- paired incremental latency `2.240/8.139/12.214 ms`
  median/p95/max; and
- global solve-p95/throughput ratios `0.990x/1.021x`.

It failed the fixed `5 ms` p95 delivery limit and created one new hybrid
deadline-proxy miss.  The canonical witness is Hard Stage-4A `212756`,
epoch 0 frame 969: physical `observe_to_input=39.634 ms`, support budget
`50.000 ms`, paired increment `11.023 ms`, and hybrid estimate
`50.658 ms`.  All compared actions were `stay`.  Async submit/lookup timing
was only `0.078 ms`; most of the increment appeared in historical
`choose_action` and recertification while optional native work ran
concurrently.

**Inferred:** exact identity and nonblocking lookup solve stale/publication
correctness, but same-issue optional work still perturbs shared CPU/cache and
scheduler delivery.  This inference is supported by component timings, not a
hardware-counter attribution.

**Decision:** CE-0131 rejects this same-issue delivery boundary.  Keep the
service and native recurrence as offline/shadow infrastructure, default-off
and without physical action authority.  Do not reduce the four authoritative
global workers to obtain a pass.  Retained final artifact:
`artifacts/benchmarks/hard_supplemental_exact_async_final_direct_root_contention_windows_20260726.json`
(SHA-256
`de34b6acd382278647d8d0421e4070010794b2b712afc789a0f5cd186411bdd9`).
