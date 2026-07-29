---
name: th08-revalidate-ida-runtime-semantics
description: Revalidate TH08 native fields, offsets, functions, ECL behavior, bullet or enemy pools, and calling conventions with IDA Pro MCP plus bounded runtime probes. Use before relying on inherited IDA names, types, comments, pseudocode labels, or prior reverse-engineering conclusions in a model or live decision.
---

# Revalidate TH08 Runtime Semantics

Treat every inherited database annotation as a hypothesis until the shipped
instructions, dataflow, callers, and available runtime evidence support it.

This skill is correction-capable when the user asks to fix, implement, or
execute an accepted roadmap. In that mode, evidence-backed IDA
renames/types/comments within scope need no separate IDB permission.
Investigation-only requests remain read-only, and physical trials still
require their own authorization.

## Establish The Question

1. Read `AGENTS.md`, `START_HERE.md`, the affected formal/design note, and the
   current daily research shard.
2. Define the exact semantic claim, address/build identity, structure field or
   control-flow behavior, intended model consumer, and evidence needed to
   falsify it.
3. Mark existing names, types, comments, and decompiler variable labels as
   inherited hypotheses. Do not transfer their certainty into a contract.

## Revalidate In IDA

1. Use the connected IDA Pro MCP. Never use REA in this repository.
2. Inspect native instructions and dataflow around the producer and every
   relevant consumer.
3. Inspect callers, callees, cross-references, allocation/lifetime paths,
   indexing/stride behavior, sentinel checks, and state transitions.
4. Compare pseudocode with assembly where types, signedness, aliasing, or
   calling conventions affect meaning.
5. Search for counterexamples: alternate call paths, reused storage,
   transformed coordinates, frozen clocks, pooled lifetimes, or fields whose
   interpretation changes by state.

## Add Bounded Runtime Evidence

1. Design the smallest native trace or probe that distinguishes remaining
   interpretations. Keep it trace-only/default-off unless a separate contract
   grants more authority.
2. Fix executable identity, addresses, capture timing, coherence boundary,
   and fail-closed behavior. Static evidence alone is not runtime proof.
3. Correlate probe observations with the exact native producer/consumer and
   physical frame. Preserve raw evidence locally and retain a compact,
   reproducible summary.

## Record The Result

1. Label the claim inherited, revalidated, corrected, or unresolved, and mark
   each conclusion observed, inferred, or hypothesized.
2. Rename/retype/comment strong conclusions in IDA; remove or correct
   misleading annotations. Record material database changes in the current
   daily shard.
3. Update every affected source-of-truth note, field layout, test fixture,
   parser, and formal contract in the same checkpoint.
4. Grant no model or action authority until the required runtime evidence and
   parity/adversarial tests pass. Preserve unknown-direction approximations
   outside hard safety authority.
