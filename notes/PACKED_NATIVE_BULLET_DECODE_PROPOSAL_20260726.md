# Packed Native Bullet Decode Proposal

Date: 2026-07-26

Status: accepted live implementation optimization for planning captures.
The native packed path is the default at 16 or more active slots; sparse
captures and diagnostic transform-runtime traces retain the Python decoder.
This does not change planner or model authority.

## Problem Contract

### Physical objective

Lower the synchronous observe-to-issue latency of local collision avoidance
without changing which native bullet slots are active, their geometry,
velocity, transform uncertainty, projected positions, collision labels, or
hard no-Bomb authority. The physical success metric is lower decode/project
latency and no new deadline miss; one easier no-hit run is not a Lunatic or
Extra survival proof.

### State and observations

The input is one stable-size raw TH08 bullet-pool capture read between the
existing manager-frame boundary samples. For every nonzero slot state, the
planning decoder observes:

- slot index;
- position and velocity;
- native collision width and height;
- active and original transform flags;
- speed and angle when finite; and
- callback phase and auxiliary state.

Diagnostic transform-program, queue, and stop/repeat state remain in the
existing Python object decoder when explicitly requested. They are not
silently dropped from a diagnostic capture.

The proposed planning output is a packed structure-of-arrays snapshot. Its
arrays own their storage for that observation, so an asynchronous corridor
submission cannot alias the persistent raw pool buffer after the next
`ReadProcessMemory`.

### Actions, uncertainty, and transition

The decoder chooses no action and advances no physical state. It only gathers
the same fields as the current planning decoder in increasing slot order,
rejects the same non-finite geometry/position/velocity records, and computes
the same `abs(native_size) * 0.5` half extents.

The local bullet projector consumes the packed arrays directly. Active
transform flags, callback-derived velocity changes, and trajectory
uncertainty retain their existing meaning. When a rare tagged ECL velocity
event must be attached, the first implementation may materialize immutable
`Bullet` objects and use the existing event oracle; this is conservative for
performance only and does not change the transition.

### Horizon, resources, safety, and fallback

The local horizon, snapshot lag, transform-growth uncertainty, bullet
relevance mask, player radius, delay support, beam, and certificate remain
unchanged. No Bomb or gameplay resource is introduced.

The independent Python object decoder remains the semantic oracle and
explicit rollback. A missing symbol, invalid native count, field mismatch,
projected-frame mismatch, or native error blocks the packed backend rather
than granting a new hard label.

## Five Formal Questions

1. **Which histories merge?** None. One packed row corresponds to one active,
   finite native slot in the same increasing slot order as Python. The packed
   representation does not merge equal geometry or transform state.
2. **Are uncertainty and causality preserved?** Yes for this boundary. Decode
   and projection use only the current raw capture and already available ECL
   events. There is no hidden-state controller maximization. Future births
   and the frozen-manager clock remain outside this optimization.
3. **Does exact decoding answer the physical decision?** No. It reproduces the
   current bullet observation and finite projection proxy. It does not prove
   capture stability, future-birth completeness, recursive viability, or
   physical survival.
4. **What is exact and what falsifies it?** Native output must match the
   independent Python decoder for slot order and every planning field,
   including malformed signed dimensions and finite filtering. Direct packed
   projection must match object projection at every retained frame. Any
   field, event, collision, robust-clearance sign, or selected-action
   mismatch falsifies implementation equivalence.
5. **Can it arrive before issue?** This is established only by paired Windows
   raw-pool and complete `choose_action` timing plus a physical full-chain
   trace. The native library is preloaded before gameplay; runtime compilation
   or cold background expansion is forbidden.

## Approximation Direction

No intentional model approximation is added. Native float loads and
`abs(size) * 0.5` are expected to be bit-equivalent to the Python/NumPy
planning fields after float32 storage, but C++/Python finite handling and
materialization can differ. The error direction was therefore unknown before
adversarial parity; the declared planning fields and projected frames now
pass that gate, while unmodeled future births and physical observation
validity remain outside it.

The first packed projector keeps callback-derived piecewise events in the
existing Python representation. Object materialization on those rare event
rows is a performance fallback, not a semantic approximation.

## Evidence Before Implementation

Windows synthetic planning-object decode currently costs:

- 400 bullets: `2.422 ms` median;
- 800 bullets: `4.626 ms`;
- 1,200 bullets: `6.846 ms`;
- 1,536 bullets: `8.039 ms`.

Complete Hard Stage-1 physical run
`hard_route2_stage1_unattended_20260726_175049` retained 7,099 decisions,
zero hits, zero Bomb, and zero deadline miss. It measured:

- bullet pool read `1.027/2.382 ms` median/p95;
- bullet decode `1.092/3.836 ms`;
- local bullet projection `0.196/0.513 ms`;
- native beam `7.549/13.430 ms`; and
- observe-to-input `22.265/33.234 ms`.

That run reached about 525 simultaneous bullets, so denser retained
Stage-4A/Stage-6B pools and synthetic full-pool cases remain required.

## Implementation And Retained Evidence

The C ABI scans the fixed 1,536-slot pool in slot order, uses unaligned
`memcpy` loads, applies the same nonzero-state and finite-field filters, and
returns owned structure-of-arrays storage. The projector consumes those
arrays directly. Tagged velocity events retain the existing Python
attachment path. `--bullet-decode-backend python` is the explicit rollback;
`--trace-transform-runtime` always selects the diagnostic Python decoder.

The deterministic differential covers 48 random pools plus densities
`0, 1, 7, 64, 511, 512, 800, 1536`, malformed NaN/Inf records, signed
dimensions, flags/callback fields, persistent-buffer reuse, exact planning
field parity, and exact 17-frame projection parity. Linux and Windows focused
tests pass.

Final Windows synthetic data used 100 samples at 13 densities. Field and
projection parity were exact at every density. The measured live hybrid p95
end-to-end decode-plus-projection was:

- 16 bullets: `0.130 ms`, versus Python `0.167 ms`;
- 32 bullets: `0.129 ms`, versus `0.253 ms`;
- 400 bullets: `0.155 ms`, versus `2.623 ms`;
- 800 bullets: `0.175 ms`, versus `5.150 ms`; and
- 1,536 bullets: `0.197 ms`, versus `9.263 ms`.

Below 16 active slots the Python path avoids the native fixed-call overhead.
The crossover is an implementation choice, not a model approximation.

Retained artifact:
`artifacts/benchmarks/native_packed_bullet_decode_windows_20260726.json`.
