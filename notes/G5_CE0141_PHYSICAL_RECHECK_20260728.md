# G5 CE-0141 Physical Recheck

Date: 2026-07-28

Status: physical trace-root correction accepted; future-event coverage and
physical action authority remain open

## Fixed Scope

The supervised diagnostic run
`lunatic_route2_stage4a_unattended_20260728_020910` repeated the pre-fix G5
workload with the shipped TH08 executable, required SHA-256, no-life-decrement
patch, Sakuya/Remilia Route 2, Lunatic Stage 4A, native runtime sensing and
local kernels, hard no-Bomb, and the explicit `--viability-audit` option.
No stationary-witness service, candidate verifier, prewarm shadow, input-clock
shadow, or new action consumer ran beside the live controller.

The physical question was deliberately narrow: after checkpoint `d5866c4`,
does every serialized hazard-coverage root equal the canonical query root
used by the complete-mask identity in a fresh shipped-game trace?

## Physical Result

**Observed:** the run completed with `route_complete`, supervisor exit zero,
accepted compact artifacts, post-stage no-save selection, identity-scoped
game termination, and no remaining game or supervisor process.

| Measurement | Result |
| --- | ---: |
| controlled frames | `2..45659` |
| decisions | 15,260 |
| hit edges | 14 |
| Bomb-bit issue masks | `0 / 15260` |
| retained capsules | 1,954 |
| capsule bytes | 84,362,548 |
| missing capsule references | 0 |
| unreadable capsules | 0 |

The hit frames were:

```text
1099, 1720, 4247, 9001, 10939, 11913, 13365,
13933, 19017, 22350, 22978, 32272, 39520, 40376
```

The frame-1,099 contact is the canonical fresh-attempt causal witness. This
was an audit-I/O run with a different RNG, death history, Power trajectory,
and stage length from the ten-hit pre-fix run. The 14-hit result is therefore
not evidence that the trace correction changed survival; the correction is
trace-only and cannot change input.

The raw trace is 471,113,243 bytes with SHA-256:

```text
6473e6706f8378b62dc02e870beffaf026716f98c0f6ea424e7de1c39cd82cd8
```

The local replay bundle audit passed. Its compact report is:

```text
artifacts/viability_audit/lunatic_stage4a_20260728_020910_bundle_audit.json
file SHA-256:
8d64927716dbac173022858a7b63d75c5e3e990f6b783dfdd7b35969da0c0221
bundle SHA-256:
3bb51b7752305d250c509a1080c8b6c07fb75a250c99edb6252450def8a84ef9
```

The raw JSONL and capsule directory remain local and ignored under the
two-newer-compatible-bundle retention rule.

## CE-0141 Result

The post-fix exact audit is:

```text
artifacts/viability_audit/g5_complete_mask_stage4a_postfix_20260728.json
report digest:
e1853759053784ff1e35c3a1996ff5d730f969529e0bc1e318a07a432045f651
file SHA-256:
dc0d10a4cbc762f6bb608e9e6a83cad4fa30b8aa357a33b8f0eb303f271c4c8f
```

Two complete generations were byte-identical.

**Observed:** all 15,069 available canonical root/capsule joins passed.
`root_validation_failure_count`, its failure histogram, and missing capsule
count are all zero. This physically closes the CE-0141 construction defect:
the post-fix shipped-game trace contains no mixed manager/query coverage root.
The manager frame remains separately recorded and has no unconditional input
clock authority under CE-0120.

The retained-artifact regression and complete Linux/Windows quick suites pass
`741/741` in `8.850/14.854 s`, with three existing Windows platform skips.

## Restricted Witness And Remaining Boundary

The first eligible Boolean-empty decision/query/source root is
`596/595/595`, joined to `policy_579_595.npz`.

- active, held desired, and issued masks are `0x05`;
- no command is pending;
- all 36 canonical no-Bomb root actions completed;
- exact stationary horizon is 32 frames under cadence support `(4,5,6)`;
- 16 actions share the best label;
- the label is 32 frames with margin `0x1.32e07a0000000p+4`;
- all 36 native witnesses match the scalar labels with zero margin error.

**Observed boundary:** coverage is rooted correctly at frame 595, but unseen
future events are `UNKNOWN` from frame 596, the first successor transition.
The result therefore remains:

```text
finite_model_authority = exact restricted stationary lower witness
physical_model_status = model_unknown
physical_action_authority = none
```

Closing CE-0141 does not close future births, stop/resume, redirects, laser
phase/extent, player-aim dependence, enemy-body enablement, unknown callbacks,
CE-0120, or any issue-time consumer contract.

## Decision

1. Mark CE-0141 physically fixed and retain both the failing pre-fix trace and
   passing post-fix report.
2. Do not compare the 10- and 14-hit audit runs as a strategy A/B.
3. Keep complete-mask stationary results outside action authority.
4. Continue G5 one event class at a time, beginning with future bullet birth,
   with static/IDA evidence, native runtime traces, update-order fixtures,
   semantic differential tests, and an explicit residual `UNKNOWN` report.
