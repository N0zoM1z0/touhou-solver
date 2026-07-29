# Evidence And Falsification

Use this reference to keep the audit causal, reproducible, and honest about
what static analysis, tests, retained traces, and physical trials prove.

## Contents

1. Evidence labels
2. Evidence hierarchy
3. Minimal falsifiers
4. Retained runtime evidence
5. Physical causality and action authority
6. Test interpretation
7. Evidence checklist

## 1. Label Every Conclusion

Use the repository vocabulary:

- **Observed**: directly visible in shipped instructions/dataflow, current
  source, deterministic execution, or retained native runtime evidence.
- **Inferred**: supported by multiple observed facts but not directly proved
  at runtime.
- **Hypothesized**: plausible and useful to test, but missing a decisive fact.

Also label annotation provenance:

- inherited;
- revalidated;
- corrected;
- narrowed;
- unresolved.

Do not use “observed” for a domain name guessed from visual behavior when only
the state mutation is observed.

## 2. Use The Right Evidence Hierarchy

Prefer:

1. Exact shipped executable instructions and dataflow.
2. Native runtime traces/probes tied to the same address, frame, and build.
3. Independent scalar falsifiers.
4. Current source and C ABI behavior.
5. Retained physical dossiers and deterministic fixtures.
6. Python/C++ parity.
7. Prior notes, names, comments, and internet descriptions.

Lower-ranked evidence can reveal a question but cannot silently override
higher-ranked evidence.

Static analysis can establish formulas, branches, and reachable resource
indices. It does not prove a specific runtime state occurred. Conversely, a
runtime correlation does not by itself identify the native producer.

## 3. Design Minimal Falsifiers

For each suspected mismatch, write:

```text
Native prediction:
Solver prediction:
Smallest differentiating input/state:
Observable output:
Failure direction:
```

Examples of useful shapes:

- timer fraction just below/above carry;
- scale `1/3` or `1/12` that exposes float32 accumulation;
- full width versus half extent at an inclusive boundary;
- rotated rectangle endpoint outside a capsule/box;
- lifecycle state that becomes active in the same update;
- collision-disabled object with a future re-enable event;
- Focus edge before an action-dependent contact gate;
- pool-full versus pool-free RNG callback;
- `INT_MAX` cursor or extreme finite quantization input.

Prefer one-variable changes. Keep all unrelated bytes and state identical.

## 4. Mine Retained Runtime Evidence Correctly

Record:

- run ID and exact artifact path;
- source/raw hash;
- code and physical-code checkpoint;
- route/team/difficulty/stage/phase;
- decision/frame scope;
- model and immutable version;
- whether evidence is replay-capable;
- sample versus unique-object count;
- manager-frame and observation coherence;
- contamination, death/respawn, Power/resources, and cleanup.

Do not call 40,000 repeated samples “40,000 bullets.” Distinguish aggregate
samples, distinct slots, adjacent transitions, and per-frame population.

Use retained evidence to establish reachability:

- a state pair appears;
- a field transition co-occurs in one slot;
- a callback instruction pointer is pending;
- an action snapshot omits a later hazard;
- a latency tail exists under one workload.

Require a controlled differential before assigning causality to a hit or
claiming a performance improvement.

## 5. Preserve Physical Causality

For a hit:

1. Start with the canonical first hit of a fresh attempt.
2. Identify the native collision frame and active input then in force.
3. Separate the newly issued action if it occurs after hit detection.
4. Compare the hazard snapshot, issue-time recertification, and native object
   state at the same epoch.
5. Treat later hits as coupled through respawn, Power, position, timing, and
   damage.

For action-dependent mechanics:

- create a same-checkpoint A/B that changes only one complete mask or Focus
  edge;
- observe the state after each relevant native priority;
- retain RNG state/call count when shared RNG can couple later births;
- verify foreground and cleanup;
- never broaden authorization from a trace-only probe to live input.

## 6. Interpret Tests And Parity

Run the smallest focused tests while iterating. Use discovery as required by
the repository.

When tests pass despite a finding, state why:

- boundary value absent;
- raw state discarded before test input;
- expected values use production code;
- native and scalar paths share a helper;
- test checks serialization, not physical effect;
- workload never reaches the callback/state.

Add proposed cases to the report even in read-only mode. Do not weaken tests
or erase counterexamples.

For crashes, record the subprocess signal/exit code. For numeric mismatches,
record exact inputs and outputs. For performance, record timing boundary and
workload.

## 7. Evidence Checklist

- [ ] Every conclusion has Observed/Inferred/Hypothesized status.
- [ ] Inherited annotations are distinguished from revalidated ones.
- [ ] Binary and model versions are pinned.
- [ ] Sample counts are not confused with unique objects.
- [ ] Static reachability is not called physical occurrence.
- [ ] A physical correlation is not called causality without a control.
- [ ] Python/C++ parity is not called native correctness.
- [ ] Green tests are explained when they miss the finding.
- [ ] Approximation direction and authority impact are explicit.
- [ ] No new physical trial was run without authorization.
