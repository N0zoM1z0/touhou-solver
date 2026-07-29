# IDA Native Baseline

Use this reference to establish executable identity, recover native semantics,
and find important routines that existing annotations or solver code may have
missed.

## Contents

1. Identity and patch reconciliation
2. Function-level semantic revalidation
3. Tables, callbacks, and overlooked programs
4. Structures, types, and decompiler failure modes
5. Native ordering and lifecycle
6. IDA annotation recommendations
7. Completion checklist

## 1. Reconcile Identity Before Semantics

Collect from the connected IDA database:

- input path and module name;
- image base and architecture;
- file size;
- IDB input MD5/SHA-256 when exposed;
- entry point and relevant segment ranges;
- known patched bytes or database patches.

Collect from the executable named by `START_HERE.md`:

- absolute path, file size, MD5/SHA-256;
- PE section layout needed to map raw offsets to virtual addresses;
- documented runtime patches and their intended effects.

If hashes differ:

1. Compare sizes and PE layout.
2. Compute exact byte differences without modifying either file.
3. Map each raw difference to a VA and enclosing function/data object.
4. Reconstruct documented patches in a temporary copy and verify whether the
   resulting complete hash equals the IDB input hash.
5. State which functions may safely use the IDB and which patched region needs
   separate clean/patched interpretation.

Do not continue with broad address-level claims when version drift remains
unexplained.

## 2. Revalidate One Native Claim

Write the claim before inspecting source:

```text
Claim:
Address/build:
Inherited annotation:
Physical meaning:
Solver consumer:
What would falsify it:
```

Then inspect:

1. The exact load/store instructions and operand widths.
2. Signedness, casts, bit tests, comparisons, and branch direction.
3. The producer that initializes or mutates the field.
4. Every material consumer, not only the best-named one.
5. Callers and callees that establish argument order and calling convention.
6. Allocation, reset, deactivation, reuse, and pool stride.
7. State-dependent reinterpretation of the same storage.
8. Same-frame callback/scheduler order.
9. Global scales, freeze flags, timers, and transformed coordinate systems.
10. Float32 write boundaries versus x87/decompiler double expressions.

Use pseudocode to navigate. Use instructions as authority whenever a wrong
prototype, alias, union, or decompiler simplification could change meaning.

Classify the inherited annotation:

- **revalidated**: instructions/dataflow support it;
- **corrected**: a stronger or different interpretation is established;
- **narrowed**: valid only for specific state/workload/caller;
- **unresolved**: static evidence cannot distinguish alternatives.

## 3. Find Overlooked Native Programs

Do not search only functions already named by the team. Enumerate:

- ECL/opcode dispatch cases and shared basic blocks;
- callback installation and invocation tables;
- SHT callback tables and resource-reachable indices;
- indirect function-pointer tables;
- global writers for time scale, freeze, phase, input, and RNG;
- direct callers of collision, damage, death, spawn, and deactivation helpers;
- fields with multiple writers but one documented producer;
- all xrefs to solver-critical globals;
- table entries that have addresses but no semantic catalog entry.

For each table:

1. Recover length, element type, null entries, and common prototype.
2. Map every non-null entry to an address and current name.
3. Search shipped resource/corpus reachability by index.
4. Decompile reachable unnamed entries.
5. Classify each as physical transition, hazard birth, lethal geometry,
   clock/input change, RNG consumer, resource/damage change, presentation, or
   unresolved.
6. Keep inferred domain nouns separate from observed mechanics.

For lethal behavior, build a caller closure:

```text
death/miss handler
  <- direct collision helpers
  <- every native source family that calls those helpers
```

Record both the number of direct helpers and the number of upstream source
families. Do not confuse one helper shared by lasers and custom rectangles
with one physical source class.

## 4. Repair Type Understanding Before Trusting Pseudocode

Audit IDA local types for the structures most used by solver semantics:

- enemy partial layout;
- active ECL VM and saved VM frames;
- auxiliary context and context selector;
- bullet/laser lifecycle records;
- player input/movement/collision fields;
- callback and SHT record prototypes;
- timer elapsed/fraction pairs.

Prefer small `Partial` structures containing only revalidated fields. Avoid
filling unknown gaps with speculative names.

Common decompiler hazards:

- array indexing created from an untyped `this` pointer;
- a function-pointer call shown with phantom x87 arguments;
- signed `int16` depth rendered as unsigned;
- one shared basic block labeled as only one opcode;
- comments attached to the instruction after the branch they describe;
- full width mislabeled as radius/half extent;
- a byte named “auxiliary” whose consumer is a collision gate;
- local variable names inherited from an earlier, wrong prototype;
- x87 intermediate precision hiding float32 stores.

When suggesting a type change, specify:

- function/address;
- exact prototype or partial field;
- instruction/dataflow evidence;
- callers that must be re-decompiled afterward;
- any still unknown fields.

## 5. Recover Ordering And Lifecycle

Write the physical update order that matters to the claim:

```text
observation -> player/input -> shot/RNG -> enemy/ECL -> bullet/laser ->
collision -> timer advance -> publication
```

Replace this schematic order with the actual registered priorities and
same-priority order observed in the binary.

For each object lifecycle:

- enumerate every native state value;
- identify states that can fall through into another state in the same update;
- locate collision enable/disable gates;
- distinguish animation completion from elapsed timer;
- identify freeze behavior and whether collision still runs;
- identify deactivation and offscreen handling;
- record whether a future callback changes motion, collision, or both.

Do not project “nonzero state” as “lethal” without following the native switch.
Do not filter a currently nonlethal object for an entire horizon if a future
event can make it lethal.

## 6. Recommend IDA Changes Without Overclaiming

In read-only audit mode, record proposed changes instead of applying them.
For each proposal include:

```text
Address/table:
Current annotation:
Proposed name/type/comment:
Evidence status:
Why the current annotation is dangerous:
Required caller re-decompile:
```

Prefer mechanical names such as `set_*`, `test_*`, `advance_*`,
`collision_suppressed_*`, or `spawn_*` until the domain identity is observed.

If writes are authorized later:

1. Apply only strong conclusions.
2. Re-decompile affected callers/callees.
3. Record material database changes in the current daily research shard.
4. Update every affected source-of-truth note and source catalog in the same
   checkpoint.

## 7. IDA Completion Checklist

- [ ] IDB/executable identity is exact or differences are fully explained.
- [ ] Each audited field has a producer and consumer chain.
- [ ] Assembly was checked where types or numeric precision matter.
- [ ] Relevant callers, callees, xrefs, tables, and resource reachability were
      enumerated.
- [ ] Native state and same-frame ordering were recorded.
- [ ] Missing important routines were classified.
- [ ] Suggested names/types/comments distinguish observed mechanics from
      inferred domain names.
- [ ] Static findings are not presented as runtime proof.
