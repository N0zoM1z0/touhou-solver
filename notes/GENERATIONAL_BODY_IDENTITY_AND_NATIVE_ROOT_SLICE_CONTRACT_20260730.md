# Generational Body Identity And Native Root Slice Contract

Date: 2026-07-30 (Asia/Singapore)

Status: **Offline boundary implemented / no live or predictive authority**

Scope: the first producer-boundary slice after
`notes/CAUSAL_ACTION_CONDITIONED_FUTURE_BODY_PRODUCER_CONTRACT_20260730.md`.
It defines ordinary-enemy lifetime identity, a non-mutating native-root byte
capture envelope, and the exact failure boundary before allocation/initial-VM
execution is connected.

## 1. Native evidence and correction

Observed, revalidated in the connected TH08 IDA database:

- `enemy_spawn_from_timeline` at `0x0042A4E0` scans the 480 ordinary slots in
  ascending order. The test at `0x0042A54E` selects the first slot whose
  `+0x3324` active bit 0 is clear.
- The selected slot receives the `0x53D0`-byte template copy before its main
  ECL VM is started and executed once immediately.
- If that initial `enemy_ecl_vm_step` returns `-1`, `0x0042A5F5` clears active
  bit 0 inside the same timeline spawn call.
- A later timeline record in the same manager update may therefore select the
  same slot again. Frame-boundary active snapshots can miss the complete
  allocation/retirement lifetime.

The IDA comments at `0x0042A54E` and `0x0042A5F5` now record this producer
identity boundary.

Inferred from that observed order:

- pointer or slot equality is not lifetime equality;
- inactive-to-active snapshot edges are insufficient to count allocations;
- exact generation must advance on ordered native allocation events, including
  allocate/retire/reallocate sequences inside one physical update.

Hypothesized and not yet granted authority:

- every body-affecting allocation path has been inventoried;
- the current solver can emit all retirement events in exact native order; or
- a complete captured root can yet be executed beyond root+0.

## 2. Formal problem contract

### Physical objective

Preserve distinct enemy-body lifetimes while constructing an
action-conditioned future body/flag/geometry schedule for hard collision
viability. The ultimate physical objective remains Sakuya/Remilia Lunatic
NMNB, including Stage 3, Stage 4A, Stage 5, Final B, then a full Power-0 route.

### State and observations

The identity state for each of 480 ordinary slots contains:

```text
(active, seen_lifetime_since_root, allocation_generation)
```

The producer root contains the physical root update, immutable root and clock
versions, exact captured native component bytes, and the root-relative slot
ledger. The controller may observe only the body/geometry set exposed at its
next decision; hidden allocation history remains nature state.

Generation is root-relative:

- a slot active at the producer root is generation 0;
- the first post-root allocation of a root-inactive slot is generation 0;
- every later allocation after retirement increments the slot generation.

The schedule interface receives the injective integer
`(generation << 32) | slot`. Generation zero therefore preserves existing
retrospective slot IDs `0..479`, while producer output cannot merge a reused
slot lifetime with its predecessor.

### Actions and issue semantics

This slice issues no gameplay input. Future producer branches remain
conditioned on exact asynchronous active-mask histories under the existing
ordered transaction recurrence. Allocation and retirement events are nature/
native-transition outputs, not controller choices.

### Uncertainty and transitions

For one contiguous physical update, a complete event tuple has sequences
`0..n-1`. Each event is either:

```text
allocate(slot, native source)
retire(slot, native source)
```

Allocation of an active slot and retirement of an inactive slot fail closed.
The endpoint active-slot snapshot may only reconcile the event result. It may
not synthesize a missing event. Non-contiguous physical updates and event
sequences fail closed.

The recurrence is:

```text
allocate inactive unseen slot:
    seen := true; generation unchanged; active := true

allocate inactive seen slot:
    generation := generation + 1; active := true

retire active slot:
    active := false
```

Generation overflow is rejected rather than wrapped.

### Horizon and resources

The ledger is finite over 480 slots and one declared event batch per physical
update. No horizon may skip an update unless an independent exact event log
covers the skipped interval. Power, damage, lives, Bombs, player shot state,
and shared RNG remain required producer-root resources; they are not scalar
preferences.

### Safety invariants

- survival remains hard and Bomb bit `0x02` remains forbidden;
- pointer/slot alone never identifies a producer body across time;
- endpoint active bits never infer hidden lifetimes;
- a native-root capture is immutable, content-addressed, frame-bracketed, and
  explicit about missing requirements;
- inherited or hypothesized layouts do not satisfy a revalidated root
  requirement; and
- even a coherent byte-complete root has no predictive authority until the
  exact executor covers every required event class or conservatively envelopes
  it.

### Deadline and fallback

The current capture helper is diagnostic/offline and issues no input. A
crossed manager-frame bracket retries a bounded number of times and otherwise
returns an explicitly incoherent slice. Missing requirements or executor
coverage remain `UNKNOWN`; the live Boolean policy and fresh local hard
certificate remain the only permitted fallback.

## 3. Implemented boundary

`scripts/th08_future_body_identity.py` adds:

- `Route2BodyGenerationIdentity`;
- an immutable root-relative 480-slot ledger;
- ordered allocation/retirement events;
- exact same-update generation advancement;
- endpoint reconciliation without inference; and
- content-addressed ledger records.

`lower_route2_generation_identity_to_future_body_sample` is the only new
lowering entry point. Existing generation-zero retrospective fixtures,
schedule source, and retained digests are unchanged.

`scripts/th08_native_future_body_root.py` adds:

- canonical native component specifications with revalidated/inherited/
  hypothesized evidence labels;
- exact byte captures and SHA-256 component identity;
- bounded manager-frame bracketing;
- a full-pool native bit-0 decoder for root active slots;
- the ten minimum semantic root requirements; and
- explicit `partial_native_root_inventory`,
  `incoherent_native_root_slice`, or
  `complete_root_bytes_without_executor_authority` status.

The root-slice schema intentionally always publishes
`physical_predictive_authority: false`.

## 4. CE-0198 and differential evidence

CE-0198 rejects snapshot-edge generation inference. The deterministic
`scripts/analysis/th08_future_body_generation_differential.py` report contains
four event-order cases. The implementation matches a structurally independent
dictionary/list oracle in all four. The boundary-only foil misidentifies three
cases, including:

```text
root inactive slot 7
allocate generation 0
retire generation 0
allocate generation 1
endpoint active slot 7
```

The endpoint-only foil reports generation 0 even though the surviving native
lifetime is generation 1.

Retained report:
`artifacts/runtime_reports/th08_future_body_generation_differential_20260730.json`

SHA-256:
`701f1ca778e6e20c94996061afec3cea68bf4233ba920af80de0fa63b4930334`

Linux and Windows render LF-normalized-identical output. Schema v2 adds an
explicit `complete_requirement_coverage` bit so a revalidated pointer cell
cannot claim complete pointee coverage.
Twenty-two focused tests cover identity encoding, native-order lifecycle
updates, endpoint reconciliation, root capture/retry/coverage, full-pool
active decoding, independent differential parity, and retained-report
identity. Complete Linux/Windows discovery passes 1,288/1,288 in
14.102/31.159 seconds, with the three existing Windows skips.

## 5. Required design questions

1. **Which histories map to one model state?** Histories merge only when their
   active generational identities and every other next observation agree.
   Same slot/geometry with different generation remains distinct producer
   state even if a later controller observation hides that distinction.
2. **Are all uncertainty branches causal?** The ledger consumes one complete
   native-order event history. It never maximizes per hidden allocation after
   observation and never reconstructs events from an endpoint.
3. **Does an exact solve answer the physical question?** Not yet. This slice
   answers only lifetime identity and root-byte provenance. Allocation source
   coverage, initial VM, body-affecting ECL/callbacks, damage/RNG, scheduler,
   final geometry, collision, and delivery remain open.
4. **What falsifies the result?** Any native allocation that does not enter the
   ordered event stream, any mismatched endpoint active set, a non-injective
   encoding, or an IDA/runtime witness showing different native slot-selection
   or immediate-end order falsifies it.
5. **Can it be consumed before issue time?** No live consumer is connected.
   Capture timing and full component layout have not passed a physical stage
   gate, so this version cannot change cadence, sensing, or action.

## 6. Next exact gate

1. Revalidate and version the concrete byte layouts for the ten root
   requirements, preferring one coherent full-pool/root transaction.
2. Connect timeline allocation plus initial-VM termination to ordered
   `allocate`/`retire` events and compare the product executor with an
   independent scalar oracle.
3. Add child-birth allocation paths and every lifecycle clear in native order.
4. Only after component inventory and executor coverage are exact or
   conservative, add a default-off non-aborting whole-stage observer. The
   physical unit remains an original-game stage; no THPRAC or exact-spell
   switch is permitted.
5. Retain native replay only when the original game naturally produces one,
   then repeat the Stage 3/4A/5/Final-B promotion ring before the Power-0 full
   route.

## 7. 2026-07-30 allocation/root-layout update

The timeline allocation boundary is now connected to the ledger. The
integrated simulator performs the native first-inactive scan for each ordered
timeline request, invokes an explicit initial-main-VM executor, emits
immediate retirement for exact return `-1`, and permits later same-update
reuse. Four independent scalar/product cases agree at retained payload
SHA-256
`d5db9e32cf029249b17f3e99cf8b7782856bbdb128acf52e5f7538f827c2ac17`.

The concrete native layout inventory is also versioned. Revalidated fixed
addresses no longer imply complete requirement coverage: runtime ECL images,
auxiliary/callback heaps, and the run-state resource pointee remain outside
their pointer cells. Only template/pool, slot motion/flags/lifecycle, and
shared RNG currently satisfy a whole minimum root requirement. See
`notes/architecture/NATIVE_PRODUCER_ROOT_LAYOUT_AND_TIMELINE_SPAWN_LIFECYCLE_20260730.md`.

This completes former gate 2 only for an explicitly supplied initial-VM
result. The complete initial ECL VM and its dynamic root remain open, followed
by child allocation, all other retirement paths, callbacks, motion/flags,
damage/resources, and joint RNG/scheduler execution.
