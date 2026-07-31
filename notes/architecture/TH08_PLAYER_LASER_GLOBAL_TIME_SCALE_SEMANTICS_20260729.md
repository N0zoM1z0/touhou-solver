# TH08 Player/Laser Global Time-Scale Authority

Last updated: 2026-07-31.

## Problem

TH08's global gameplay scale is not a timeless scalar. One future frame may
have distinct:

- scale visible to the priority-9 player update;
- writes made by enemy ECL callbacks;
- scale visible to the priority-14 laser update.

A hard certificate therefore needs an immutable sequence
`(player_scale_bits[t], laser_scale_bits[t])`, not the current root value
repeated through the horizon.

## Revalidated Native Semantics

Global float32 scale is stored at `0x017CE8E0`.

Player update:

- SHT-selected X/Y speeds are multiplied by player-axis scales;
- those float32 values are multiplied by global scale at
  `0x0044BA67..0x0044BA85`;
- float32 deltas are stored at player `+0x3F8/+0x3FC`;
- the deltas are added to position.

Laser update:

- each active `0x59C` laser reads the laser-phase global scale;
- head and length/speed-related motion use that scale;
- the scaled timer is advanced later in the same update.

Scale writers:

- callback 18 (`0x00424F90`) writes `1.0f / int32(arg1)`;
- callback 28 (`0x004251B0`) writes the reciprocal and scales active bullet
  velocities;
- callback 29 (`0x00425290`) reverses bullet scaling/restores state and writes
  the final scale.

These callbacks disprove a generic constant-root-scale assumption.

## Immutable Contract

Scale bits, phase schedule, coverage, content identity, route/spell identity,
and semantics version are part of every scale-sensitive request/publication.

Rules:

- player and laser transitions consume their own same-frame scale;
- movement is a per-step float32 recurrence, not `speed * frames`;
- incomplete, nonfinite, mismatched, or too-short schedules are `UNKNOWN`;
- a lookup miss does not start cold proof work on the issue thread;
- unit-scale historical evidence remains valid only under its old slice;
- root-only continuation cannot authorize a hard certificate.

The exact primitive semantics version is
`th08-player-laser-phase-scale-v1-0044ba67-00431bc9`.

## Final-B Exact Authority

The shipped `ecldata7.ecl` image is pinned by SHA-256
`20b35dca3820438f0b90ae44e3362a7af27d2fc1ac7ae5888c477dc1c89a3734`.

For the accepted Final-B source:

- spell 190/subroutine 44;
- root scale one quarter;
- Bomb zero;
- coherent main/aux ECL state and content identity;
- the only scale write in the declared prefix is callback 18 at relative
  frame 240;
- player phases remain quarter-scale through frame 240;
- laser phases use the prior same-frame ordering and restore to unit at the
  declared write.

The full-route supervisor captures/binds that typed schedule through
`FinalBScaleScheduleAuthority`. Exact-version consumers may use only the
remaining covered suffix. The checked-in launcher supplies the pinned ECL
image and enables this authority:

```bat
run_th08_full_route_agent.bat
```

The accepted physical delivery run observed 111 decisions consuming offsets
1 through 238 with quarter-scale roots, no fallback, and no fresh hit before
the terminal window. This closes only that pinned Final-B schedule slice.

## Diagnostic Root-Only Continuation

Practice Start lacks the full preceding route/ECL schedule. The explicit
`--diagnostic-continue-root-only-scale` option may continue a whole focused
diagnostic using the current root scale as an unknown-direction proxy.

It:

- records the root scale and provenance;
- does not claim a future schedule;
- cannot combine with exact Final-B authority;
- preserves hard no-Bomb and normal issue semantics;
- exists only to obtain physical workload evidence when scale coverage would
  otherwise stop at frame 1.

Any native scale change inside a consumed horizon falsifies the proxy. Default
flag-off behavior remains fail-closed.

## Authority Limits

The exact Final-B schedule is live only for its pinned Route-2 identity.
Nothing here proves:

- all future scale writers in another stage/route;
- Extra scale coverage;
- generic action-conditioned ECL schedule closure;
- correctness of a root-only constant schedule;
- physical survival outside the retained slice.

If a new root encounters non-unit or varying scale without an exact schedule,
return `UNKNOWN` and localize the source before planning through it.

## Focused Verification

The active scale checks are:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_th08_live_scale_schedule_authority.py'
```

Run a Final-B physical trial only when the scale producer/consumer or live
issue path changes and the user authorizes it.
