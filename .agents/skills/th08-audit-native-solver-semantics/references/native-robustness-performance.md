# Native Robustness And Performance

Use this reference to inspect C/C++ ABI safety and identify performance work
without changing solver semantics or authority.

## Contents

1. ABI validation
2. Arithmetic and malformed-input hazards
3. Crash-safe reproduction
4. Concurrency and cancellation
5. Performance evidence
6. Allocation and loop analysis
7. Optimization order and verification

## 1. Audit Every ABI Boundary

For each exported function and Python wrapper, verify:

- null pointers;
- nonnegative counts and positive strides;
- output capacity;
- field offset plus width;
- record count times stride overflow;
- program length times record size overflow;
- pointer arithmetic range;
- peer-array length and dtype;
- finite numeric inputs;
- representable float-to-integer conversions;
- output count initialization and atomicity on error;
- cancellation/stop polling;
- behavior for zero records and empty classes.

Do not accept “the Python caller validates this” without checking whether:

1. the C ABI is also used by tests, tools, or another wrapper;
2. a torn/corrupt process blob can supply the value;
3. the wrapper checks the same range the C++ operation needs;
4. partial outputs survive a nonzero return code.

## 2. Search For Arithmetic Hazards

Inspect:

- `signed_value + 1` in range checks;
- negation of minimum signed integers;
- signed multiplication/addition before bounds checks;
- float-to-`int32`/`int64` casts after checking only `isfinite`;
- `round`, `floor`, or quantization outside integer range;
- `count * stride` performed before widening;
- length minus one when length may be zero;
- index conversion between signed and unsigned;
- `abs(INT_MIN)`;
- NaN comparisons that bypass min/max checks;
- infinity produced by multiplying two finite values.

Use adversarial values:

```text
INT32_MIN, -1, 0, last-valid, first-invalid, INT32_MAX
0, 1, capacity-1, capacity, capacity+1
-0.0, smallest normal/subnormal, large finite, DBL_MAX, NaN, ±Inf
```

If normal live inputs make the defect unreachable, record that boundary. Keep
the finding as ABI robustness rather than inflating it into a live action bug.

## 3. Reproduce Native Failures Safely

Run crash or UB candidates in a subprocess:

1. Construct the smallest valid blob/arrays except for the targeted field.
2. Run the scalar path and record its result.
3. Run the native path in a separate process.
4. Record stdout/stderr, exit code/signal, build flags, and library identity.
5. Vary only the targeted boundary.

Prefer a deterministic mismatch or signal over a speculative language-lawyer
claim. If sanitizers are available and building a temporary diagnostic is
within scope, use ASan/UBSan without replacing the shipped/native semantic
baseline.

Never run a deliberate crash probe inside a live controller or game process.

## 4. Audit Concurrency And Cancellation

Check:

- global or thread-local scratch ownership;
- simultaneous planner and issue-time calls;
- background worker cancellation frequency;
- stale-version publication;
- output visibility before completion;
- buffer growth and lifetime;
- Python GIL held/released mode;
- exceptions versus signals across the C ABI;
- key-release/supervisor behavior if a native call kills the controller.

An optimization using one global workspace is unsafe unless ownership and
concurrent callers are proved. Prefer request-local or explicitly thread-local
storage with bounded capacity and cancellation behavior.

## 5. Anchor Performance In Retained Evidence

Before proposing work, extract:

- workload identity and immutable version;
- platform and build;
- decision count;
- p50/p95/p99/max, not only mean;
- exact timing boundary;
- hazard/object density;
- controller cadence and snapshot age;
- background worker/contention state;
- whether decode, lowering, packing, induction, issue, and tracing are inside
  the measurement.

Separate:

- microbenchmark;
- retained replay/direct-root benchmark;
- Windows live pipeline timing;
- physical outcome.

Never compare phase-only rows with an all-stage baseline as if they were
control-equivalent.

## 6. Build An Allocation And Loop Graph

For a hot path, count per decision and per horizon step:

- Python lists and tuples;
- NumPy `fromiter`, `empty`, `asarray`, and dtype-conversion buffers;
- duplicate float32/float64 representations;
- C++ vectors/maps and their lifetime scope;
- ABI output arrays;
- repeated packing of invariant enemy/laser/action fields;
- hazard-by-candidate pair work;
- repeated trigonometry, projection, or `hypot`;
- `ReadProcessMemory` calls and bytes;
- object reconstruction after native reduction.

Distinguish allocations that are explicit from possible copies avoided by
contiguous views. State the counting assumptions.

Look for low-risk reuse:

- invariant half extents packed once per request;
- one scratch vector reused sequentially by hazard class;
- request-local SoA capacity reused across horizon steps;
- one native call replacing duplicate marshaling;
- exact collision masks removing known nonlethal objects;
- exact geometry that also avoids expensive approximate math.

Do not assume a smaller scratch allocation will dominate runtime. Measure it.

## 7. Optimize In This Order

1. Fix physical semantic errors and freeze the immutable model version.
2. Remove provably nonlethal/disabled work with time-indexed masks.
3. Reuse invariant packed fields.
4. Reuse request-local buffers.
5. Fuse native stages only after their individual parity boundaries are
   independently understood.
6. Change algorithmic search/pruning only under the formal recurrence and
   proof/authority contract.

For a fused native beam step, preserve:

- float32 hazard geometry and float64 rank fields where currently required;
- stable tie ordering;
- first-action partitions;
- no-write/action semantics;
- certificate and viability gates;
- quantifiers and observation merging;
- cancellation polling;
- exact-version publication.

Verification matrix:

- exact retained indices and selected actions;
- hard collision/clearance labels;
- bounded numeric differences where accumulation order changes;
- scalar/native adversarial cases;
- p50/p95/max on retained direct roots;
- complete Windows `before_trace` or issue boundary;
- no new deadline or contention regression.

Report performance proposals as **observed source opportunity** plus
**hypothesized benefit** until measured. Never invent a percentage.
