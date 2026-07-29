# Solver Semantic Traceability

Use this reference to compare native TH08 behavior with the Python, C, and C++
solver implementation from sensing through issued action.

## Contents

1. Build a native-to-issue trace
2. Audit information preservation
3. Audit time, action, and causality
4. Audit geometry and numeric semantics
5. Audit oracle independence
6. Classify mismatch direction and authority
7. Search patterns and review checklist

## 1. Build A Native-To-Issue Trace

For every native claim, locate the concrete implementation path:

```text
native field/transition
  -> ProcessReader or retained pool blob
  -> scalar/NumPy/native decoder
  -> dataclass/packed snapshot/ABI fields
  -> projection or event lowering
  -> local hazard/corridor/simulator representation
  -> scalar/native clearance or transition
  -> certificate/beam/viability recurrence
  -> issue-time recertification and selected complete mask
```

Record exact files, symbols, offsets, and ABI parameters. A matching constant
near a decoder is not enough; prove that the value reaches every authority
consumer with its meaning intact.

For large repositories, search in this order:

1. Native address, field offset, callback index, or global name.
2. Decoder constant and model field.
3. Serialization/replay field.
4. Projection/lowering consumer.
5. C ABI declaration, wrapper, and implementation.
6. Planner/certificate call site.
7. Tests, retained artifacts, and authority notes.

## 2. Audit Information Preservation

Construct a field ledger:

| Native information | Captured | Stored | Projected | C ABI | Authority use |
| --- | --- | --- | --- | --- | --- |
| lifecycle state | | | | | |
| collision gate | | | | | |
| position/velocity | | | | | |
| full/half extents | | | | | |
| timer elapsed/fraction | | | | | |
| global scale/freeze | | | | | |
| action-dependent mode | | | | | |
| RNG state/calls | | | | | |
| future event schedule | | | | | |

Search for these high-value discrepancies:

- captured fields used only in trace serialization;
- decoder fields dropped from packed snapshots;
- packed fields never passed to the hazard kernel;
- state represented as a boolean even though future collision differs;
- motion events that omit collision-enable transitions;
- diagnostic decoder and planning decoder with different field sets;
- source models that use a constant already sensed elsewhere;
- a C++ ABI that cannot express a Python model state;
- replay formats that silently default missing fields to zero.

Treat a field as modeled only when its native effect, not merely its bytes,
reaches the relevant recurrence.

## 3. Audit Time, Action, And Causality

For each transition, answer:

1. Which physical callback writes the state?
2. Which callback reads it?
3. Does the write affect the same physical frame?
4. Does the timer advance before or after collision?
5. Is the controller observation before or after that transition?
6. Can the transition depend on the selected complete action?
7. Is the action active, held desired, newly issued, pending, or no-write?
8. Can the solver observe which hidden branch occurred before choosing again?

Explicitly separate:

- controller cadence from command pickup delay;
- manager-frame time from wall/player movement time;
- desired/last-issued input from native active input;
- root snapshot scale from future scale changes;
- velocity replacement from object lifecycle/collision state;
- same-mask no-write from a new write and new delay sample.

Reject these patterns:

- projecting a slowdown with normal-speed player actions;
- applying cadence once at the root when it recurs;
- choosing separately for hidden branches that share the same observation;
- evaluating an action-conditioned native gate as fixed geometry;
- using the later issued action to explain a collision already detected;
- dropping a disabled current hazard even though it re-enables inside horizon.

## 4. Audit Geometry And Numeric Semantics

For every geometry field, identify:

- coordinate system and origin;
- center versus corner;
- full size versus half extent;
- native expansion factor;
- rotation space;
- inclusive versus exclusive comparisons;
- player hitbox contribution;
- uncertainty and lattice sampling error;
- state/phase-dependent shape.

Never assume two geometries are equivalent because their collision tests agree
on random samples. Include boundaries:

- axis-aligned and π/4;
- flat endpoints and corners;
- zero length;
- offscreen and clamp edges;
- exact inclusive overlap;
- warmup/fade widths;
- transformed/scaled coordinates.

For numeric transitions, mark every native store:

```text
read float32 -> x87/double expression -> store float32
```

Reproduce float32 rounding at each store, not only at final output. Audit:

- timer fraction carry;
- velocity scaling;
- position accumulation;
- angle normalization;
- integer truncation and signed wrap;
- float-to-integer conversion range.

## 5. Audit Oracle Independence

Create an oracle graph:

```text
native instructions/runtime
  -> independent scalar oracle
  -> Python optimized implementation
  -> C/C++ implementation
```

The scalar oracle must not import or call the implementation it checks. Watch
for shared helpers that encode the same wrong assumption:

- Python shadow and “oracle” both call one timer helper;
- native and Python paths consume one pre-lowered wrong geometry;
- semantic differential compares two implementations after a field was
  already discarded;
- tests build expected values using the production transition.

Parity proves implementation equivalence only at the compared boundary.
Whenever parity is green, state what upstream native semantics remain outside
that boundary.

## 6. Classify Direction And Authority

For every mismatch, classify:

- **conservative**: can create false hazards or remove viable actions;
- **optimistic**: can create unreachable actions or miss native hazards;
- **mixed**: direction changes by geometry, phase, or time;
- **unknown**: insufficient proof.

Then state:

- current live workload reachability;
- acceptance-target reachability;
- static-only versus retained runtime evidence;
- current fail-closed boundary;
- effect on feasibility, losing labels, optimality, replay, or performance.

Important consequences:

- A winning witness in a strictly more conservative geometry can remain useful
  if every transition is otherwise correct.
- A losing/empty result in that geometry does not prove native physical loss.
- An optimistic transition can invalidate a hard winning certificate.
- A shadow-only omission is not automatically a live unsafe action, but it
  blocks future promotion.
- A robustness crash can be severe operationally even when its observer has
  no action authority.

## 7. Search And Review Checklist

Useful source search targets:

```text
offset constants
callback index
state_offset
callback_aux
time_scale
freeze
VelocityChange
lower_*
_build_*_frames
Packed*Snapshot
query_*hazards
reduce_*beam
certificate
issue
damageable
active_action
```

Completion checklist:

- [ ] Every native field has an end-to-end consumer trace.
- [ ] Captured-but-unused and used-but-uncaptured fields are listed.
- [ ] State, phase, and collision-enable schedules are preserved.
- [ ] Same-frame action and scheduler order are explicit.
- [ ] Float32 stores and integer ranges match native behavior.
- [ ] Python/native parity is bounded to its real comparison surface.
- [ ] Mismatch direction and authority impact are stated.
- [ ] Current and future workload reachability are not conflated.
