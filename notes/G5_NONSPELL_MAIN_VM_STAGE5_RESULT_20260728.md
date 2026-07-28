# G5 Nonspell Main-VM Stage-5 Result

Date: 2026-07-28

Status: phase-A physical observation and offline source-availability join
complete. The inventory is retained as useful opt-in research
instrumentation. Ordinary main and auxiliary ECL VMs are strong static source
candidates, but exact runtime instruction identity, operand lowering,
realized geometry, hit-causal coverage, and live authority remain open.

The governing contract is
`G5_NONSPELL_MAIN_VM_SOURCE_SHADOW_CONTRACT_20260728.md`. The retained
physical workload is
`lunatic_route2_stage5_unattended_20260728_155426`.

## Decision

Retain the first-64 main-VM inventory and its modular offline analyzer. Do not
promote it to a future hazard, planner input, or action source yet.

The physical signal is material enough that a small performance miss is not a
reason to discard it:

- 64/64 observed runtime PCs map to legal decoded Stage-5 ECL instruction
  boundaries under one unique complete affine base;
- 20/20 exact captured direct-fire advances have one compatible realized
  activation batch each, totalling 260 bullets;
- 81/81 exact captured auxiliary-start advances have compatible activation
  support, covering 105 unique batches and 1,520 bullets; and
- IDA shows that opcode `0x87` delegates execution into four heap auxiliary
  contexts, explaining why main-PC-only observation is structurally
  incomplete.

The next source-topology gate is therefore auxiliary contexts rooted at
`enemy+0x3384`, together with exact runtime ECL-image identity. Expanding past
the first 64 enemy records, callbacks, and native non-ECL sources comes after
this demonstrated path unless a retained hit witness falsifies that order.

## Implementation Boundary

The implementation is opt-in through `--trace-nonspell-main-vms` and schema
11. It performs no additional enemy-pool process read. The existing
manager-frame-bracketed contiguous first-64 enemy blob is decoded once by
`scripts/th08_live/enemy_ecl_inventory.py`.

The offline analyzer is split under
`scripts/analysis/main_vm_source_join/`:

- `trace.py` strictly streams schema-11 decisions, inventory rows, and
  activation support;
- `mapping.py` indexes decoded ECL instructions and infers the affine runtime
  base without claiming byte identity;
- `advance.py` detects exact captured instruction-to-sequential-successor
  transitions; and
- `join.py` owns observation-support intersection and one-to-one accounting;
- `auxiliary.py` owns opcode-`0x87` target and auxiliary source reporting; and
- `report.py` composes direct fire, auxiliary availability, evidence labels,
  and authority gates without reimplementing those mechanisms.

The retained report is
`artifacts/viability_audit/g5_nonspell_main_vm_source_join_stage5_20260728_155426.json`.
After the CE-0163 active/restorable/physical-slot revalidation, its internal
digest is
`077a9c7655a44db3228ebd86a3a2e03988c9286ed10233f6476275461ebaf691`.
The corrected pretty retained file has SHA-256
`10cd5bcc31badeed2b6d617125665cf168bdf1b44916e3f56677b8c774c1af5f`.
Prior digests remain identifiable in Git history but describe superseded
reports with incomplete auxiliary-frame semantics.

## Offline Performance

The deterministic 64-slot fixture contains 16 active records, of which 14
have valid VMs and two are explicitly invalid.

Linux, 20,000 iterations:

| Boundary | p50 | p95 | p99 | p99.9 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Body baseline | 0.0476 ms | 0.0567 ms | 0.0717 ms | 0.0982 ms | 0.3956 ms |
| VM inventory increment | 0.0788 ms | 0.0947 ms | 0.1152 ms | 0.1692 ms | 0.4309 ms |
| Combined decode | 0.1268 ms | 0.1507 ms | 0.1743 ms | 0.2512 ms | 0.5069 ms |
| Canonical JSON build | 0.0339 ms | 0.0408 ms | 0.0535 ms | 0.0862 ms | 0.3562 ms |

Windows, 20,000 iterations:

| Boundary | p50 | p95 | p99 | p99.9 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| VM inventory increment | 0.0931 ms | 0.1109 ms | 0.1485 ms | 0.2088 ms | 0.5592 ms |
| Combined decode | 0.1510 ms | 0.1795 ms | 0.2361 ms | 0.3457 ms | 0.6255 ms |
| Canonical JSON build | 0.0416 ms | 0.0503 ms | 0.0732 ms | 0.1076 ms | 0.4652 ms |

The canonical record is 2,715 bytes with SHA-256
`aa8d425a2264396e8e10de93283539667e84cbde67c09a802a0a25079f9cdd70`.

## Physical Workload

The retained Lunatic Stage-5 practice run completed frames `1..41612` over
11,891 decisions with `route_complete`, 11 native hit edges, hard no-Bomb,
exact key release, and no residual game/controller/supervisor process. The
raw trace is local and ignored:

- bytes: `550904051`;
- lines: `23874`; and
- SHA-256:
  `8569d64d3ce50ced529bdcf4b48e8f0daa00bfbfa8d8cec9695665f04d0283a7`.

The hit frames are
`[2390, 4436, 12368, 12919, 23153, 24643, 27470, 29835, 30268, 37507, 40084]`.
All eleven follow global viability exhaustion. The canonical first hit is a
nonspell modeled committed-prefix collision at frame 2,390. This experiment
did not join source candidates through realized slot generations to those
hits, so hit-causal coverage is explicitly `not_measured`.

All 11,891 schema-11 rows validate. There are 11,890 stable prefix brackets,
one capture-spanned bracket, 138,255 VM observation rows, and zero invalid
active VMs. Active valid VM count has p50/p95/p99/max `12/31/39/44`.

Physical inventory decode p50/p95/p99/p99.9/max is
`0.1068/0.2384/0.3136/0.4464/0.5379 ms`. Total prefix capture is
`1.8383/3.6666/5.4101/11.6524/23.5940 ms`.

The combined birth observer p50/p95/p99/p99.9/max is
`0.1032/0.2029/0.3238/0.5339/1.7937 ms`. It passes p99 and maximum but misses
the fixed `0.20 ms` p95 limit by about `0.0029 ms`. This is a real performance
counterexample, not a veto on the source class. The path remains opt-in and
action-free while decode fusion, delta serialization, and movement of
post-issue reporting off the issue boundary are evaluated.

## Direct Main-VM Evidence

The decoded file `ecldata5.ecl` has SHA-256
`3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`.
Across 64 unique physical PCs, the unique best affine mapping is:

```text
runtime_pc = 0x0B1D0048 + decoded_file_offset
```

It maps 64/64 unique PCs and all 138,255 PC observations. The runner-up maps
only 40 unique PCs. This is strong address correlation, but CE-0157 forbids
treating it as runtime byte identity.

The only directly observed fire PC is `0x0B1D02F8`, mapping to file offset
`0x2B0`, subroutine 0, opcode `0x60`, time 50, size 44. It appears in 432 VM
rows. IDA **observes** that `enemy_ecl_vm_step` reads the saved PC as the
current instruction, dispatches it, advances by the instruction size, and
writes the successor PC back at function end.

The offline join therefore requires the same slot and pointer, stable
consecutive brackets, bounded monotone timer progress, unchanged
epoch/stage/spell scope, and the exact static sequential successor. Twenty
transitions pass. Every execution-support interval intersects exactly one
activation batch, and every matched batch has exactly one event. The 20
batches contain 260 age-zero bullets.

This is **inferred** direct-source availability. Runtime instruction bytes,
evaluated operands, origin, template, and slot geometry are not yet proved.
An unobserved destroy/reuse cycle between captures is also not excluded.

## Auxiliary-VM Evidence

The following is **observed statically** in IDA:

- opcode `0x87` is handled at `0x0041CDF3..0x0041CF81`;
- the first argument selects one of four pointers at `enemy+0x3384`;
- an existing context is freed, then a `0x24B0`-byte context is allocated and
  zeroed when the subroutine argument is non-negative;
- `ecl_start_subroutine` initializes the auxiliary VM at context `+0x08`;
- selected local state is copied into the context; and
- `0x0041EBB6..0x0041EC7C` schedules every non-null context after the main VM,
  selecting the active `0x228`-byte VM at `+0x08` and the saved-call-frame
  area at `+0x230`.

Later evaluator/call-path review corrected the original `+0x230` label:
`ecl_eval_int` and `ecl_resolve_int_lvalue` read live locals from the active
VM at `+0x18..+0x64`; `ecl_call_subroutine` copies the complete `0x228`-byte
VM to the `+0x230` area at a `0x228` stride. Context `+0x06` is signed
16-bit call depth, which saturates at 15. The allocation contains 16 physical
slots, but ordinary returns restore at most slots `0..14`; a saturated call
may write slot 15 before the next return restores slot 14. This area is not a
live-local base. The correction changes no retained PC/timer/local bits and
had no action authority.

The Stage-5 trace observes five mapped opcode-`0x87` PCs 1,129 times. Their
static arguments select auxiliary subroutines 30, 32, 54, 57, and 65. Every
one of those subroutines contains at least one time-zero fire instruction.

Eighty-one exact `0x87 -> sequential successor` transitions pass the same
capture restrictions:

- target 30: 37;
- target 32: 28;
- target 54: 4;
- target 57: 0 completed transitions; and
- target 65: 12.

All 81 immediate-fire availability windows intersect realized activation
support. Because one start may launch multiple fire instructions and multiple
enemies may start in one support interval, this is not one-to-one: the union
contains 105 activation batches and 1,520 bullets.

This result **infers** that auxiliary VM topology is a high-value missing
source. It does not prove the target subroutine's reachable path, exact
difficulty branch, runtime bytes, evaluated parameter-mask operands, or
geometry.

## Next Gates

1. Add the four auxiliary-context pointer values to the existing first-64
   blob decoder. This is free with respect to enemy-pool RPM and measures
   active-context density before any scatter reads.
2. Contract a bounded post-issue auxiliary-context capture. Prefer a native
   compact batch or a background immutable-version service; never issue
   unbounded cold reads from the decision path.
3. Retain exact runtime instruction bytes or an immutable runtime ECL image
   digest/base key. Static-file correlation alone remains insufficient.
4. Independently lower opcode `0x87` and fire opcodes `0x60..0x68`, including
   difficulty masks, parameter masks, copied locals, binary32 behavior,
   origin, template, counts, RNG, and transformations. Unsupported branches
   stay `UNKNOWN`.
5. Join predicted emission descriptors to realized slot generations and then
   to hit witnesses. Report source feasibility separately from hit causality.
6. Fuse inventory decoding with the existing enemy-body pass and move compact
   serialization off the issue boundary before any always-on physical gate.
7. Repeat a focused Stage-5 source run only after exact auxiliary/runtime-image
   coverage exists; then transfer to Stage 6 if the retained Stage-5 target
   waves and timing gates pass.

Focused Ruff passes. Complete discovery passes 904 tests on Linux and 904 on
Windows; Windows retains three existing skips. Repo-wide Ruff remains blocked
by 33 pre-existing findings outside this checkpoint, while every touched
source and new analyzer module passes its focused lint boundary.
