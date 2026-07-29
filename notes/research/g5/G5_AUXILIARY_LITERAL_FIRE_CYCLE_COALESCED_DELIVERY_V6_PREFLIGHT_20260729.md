# G5 Auxiliary Literal Fire-Cycle Coalesced Delivery V6 Preflight

Date: 2026-07-29

Status: isolated Linux/Windows gate passed; physical combined publication and
survival pending

Contract:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_COALESCED_DELIVERY_V6_CONTRACT_20260729.md`

## Implementation Boundary

Production packing is isolated in
`scripts/th08_live/auxiliary_vm/coalesced_envelope.py`. It canonicalizes one
complete schema-v8 V5 row, forces `timing_ms.previous_emit = null`, applies
zlib level 6 plus strict base64-sized output, and records exact compressed and
uncompressed lengths and SHA-256.

The live controller now stages at most one envelope and attaches it to the
decision built later in the same iteration. The former standalone auxiliary
`TraceSink.emit` and its `previous_auxiliary_vm_batch_emit_ms` state are
removed. The existing decision emit remains synchronous and `flush=True`.
No sensing, native capture, process-read, ECL recurrence, cache, planner,
action, Focus, or Bomb code changed.

The independent implementation is split into:

- `coalesced_replay_v6.py`: strict bounded decode, canonical equality, and
  parent/inner binding;
- `coalesced_trace_v6.py`: source digest, sequence/order, standalone-row
  rejection, and next-decision causal timing pairing; and
- `physical_report_v6.py`: unchanged V5 byte/cache oracle plus V6 packing,
  combined decision emit, cadence, completion, and survival gates.

The common physical report now accepts a version-neutral `DeliveryTraceData`
view. Historical top-level delivery remains its default and regenerates
unchanged; only V6 supplies the coalesced view and omits the inapplicable V5
standalone-emit metric.

## Independent Retained-Trace Gate

Five repeats of all 154 physical V5 rows from run `20260729_120859` pass on
Linux and Windows. Each platform independently reconstructs the exact
canonical inner objects and reuses the V5 byte oracle for 21,190 requests with
zero unknown:

- first-repeat cache misses: 46;
- persistent hits: 1,970;
- request-local hits: 2,222; and
- evictions: zero.

All values below are milliseconds:

| Platform/component | p50 | p95 | p99 | max |
| --- | ---: | ---: | ---: | ---: |
| Linux pack | 0.367 | 0.468 | 0.557 | 0.803 |
| Linux independent decode | 0.316 | 0.406 | 0.496 | 0.794 |
| Windows pack | 0.486 | 0.667 | 0.833 | 1.580 |
| Windows independent decode | 0.412 | 0.552 | 0.745 | 1.290 |

The fixed pack boundary is p95/p99/max `0.750/1.250/3.000 ms`. Both
platforms pass without changing it.

Representation is deterministic on both platforms:

| Representation | p50 | p95 | p99 | max bytes |
| --- | ---: | ---: | ---: | ---: |
| canonical inner | 13,047 | 13,939 | 14,018 | 14,448 |
| compressed | 5,010.5 | 5,278 | 5,348 | 5,397 |
| base64 payload | 6,682 | 7,040 | 7,132 | 7,196 |

The fixed maxima are 24,576/9,216/12,288 bytes respectively.

Retained reports:

- Linux:
  `artifacts/benchmarks/auxiliary_ecl_event_coalesced_delivery_v6_linux_20260729.json`,
  SHA-256
  `03ff75554e6dd57ac165990809ff4e3596c592014c98e923e64828d17433597e`;
- Windows, LF-normalized:
  `artifacts/benchmarks/auxiliary_ecl_event_coalesced_delivery_v6_windows_20260729.json`,
  SHA-256
  `7055a40a2e1edb295ffbf19397e27bcd020d17d9cf1ee7595361964742450097`.

## Falsifiers And Regression Protection

Focused tests prove:

- exact inner object round trip without mutating the source row;
- producer frame/epoch/snapshot/stage and size rejection;
- strict envelope key/version/type/length/hash checks;
- base64 corruption, zlib trailing streams, noncanonical JSON, parent
  mismatch, and duplicate/gapped sequence rejection;
- standalone batch and missing next-decision publication timing rejection;
- unchanged V5 byte/cache replay after decode; and
- combined decision emit and eleven-hit regression gates fail when injected.

Ruff passes. Complete Linux discovery passes 1,052 tests in 13.634 seconds.
Complete Windows UNC discovery passes the same 1,052 tests in 30.143 seconds
with three existing platform skips.

The report-core refactor preserves immutable evidence exactly:

- failed V1 report SHA-256 remains
  `780b8f62dee8eb1c179caf0d54964b090095a99e59634c1654fa7d0cc5aebb3e`;
- failed physical V4 report SHA-256 remains
  `2d5ebcf862cb5ce9fc3af1b3c858ae95c7444727deaa959d188f94ed7d33ed29`;
- failed physical V5 report SHA-256 remains
  `1c3018c4831063bd645594856c7e5dc3384e4fd50a54f35b06f5da764d922d6e`.

## Remaining Gate

This preflight has no actual V6-bearing decision rows, no Windows/UNC
combined decision publication timings, and no fresh survival sample. It is
therefore not physical delivery authority.

Commit this action-neutral checkpoint, then run one fresh hard no-Bomb
Lunatic Stage-5 gate with the same V5 observer flags. The strict V6 report
must find zero standalone batches, exact canonical replay, complete
next-decision timing, bounded pack plus evidence time, bounded V6-bearing and
all-decision emit regression, cadence, accepted completion, cleanup, and at
most ten hits.

Retain every outcome. Do not combine the first V6 delivery run with
unfocused-Sakuya, targeting, Power, or planner changes. Handoff still requires
two consecutive corrected Stage-5 runs at no more than ten hits plus Stage-3,
cross-stage, and full-route evidence.
