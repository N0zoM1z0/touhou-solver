# Native Replay Causal Wind Tunnel

Last updated: 2026-07-31.

## Purpose

The wind tunnel turns one original-game replay state into a controlled native
experiment:

`replay to root -> freeze/verify -> execute action in shipped TH08 -> capture endpoint -> restore -> branch again`

It avoids replaying the entire stage for every candidate while preserving
original TH08 update, collision, ECL, RNG, and float behavior inside the
captured boundary.

It is an offline/native diagnostic. It has no live action or whole-stage
authority.

## Canonical Identity

The retained workload is a Lunatic Sakuya/Remilia Route-2 Stage-5 replay with
RNG seed 59,590. Manager frame 2,129 is the root before the priority-6 replay
action load and native calculation chain. The recorded complete input is
`0x05`.

The recorded branch enters hit phase at manager frame 2,136 from hostile
bullet slot 45 with signed box separation `-0.966766`.

Replay input is aligned at `manager_frame - 1`. A stop fence must be later than
the collision frame because calculation/collision advances before an external
same-frame observer can see the result.

## Native Seam

The executor intercepts the fixed frame-pump calculation call:

- callsite `0x00441F4D`;
- `update_chain_execute` at `0x0043CA50`;
- replay action load/store at `0x004525BE/0x004525C1`.

At the root barrier it records:

- owner thread and stack/frame pointers;
- FPU/SSE state;
- replay cursor and native clocks;
- thread set;
- committed writable mapping identity;
- all tracked private/image writable bytes;
- compact control/collision/model projection;
- immutable executable, replay, content, and schema identity.

The other 33 threads in the retained epoch are suspended. One original
calculation update runs on the owner. Rendering/audio/menu work is outside the
executor.

## Restore Contract

Every branch:

1. begins from the exact root identity;
2. installs one complete no-Bomb action at the replay seam;
3. runs the declared number of native calculation updates;
4. captures per-tick collision/control/model state;
5. verifies owner stack/FX/thread/map epoch;
6. restores dirty tracked spans plus root control state;
7. repeats the parent to detect corruption.

An endpoint may be promoted to a child root. Returning to its parent restores
the immutable parent, not an action-incompatible future.

Return `UNKNOWN` or poison the session on:

- new/untracked writable mappings;
- thread-set change;
- owner stack/FX mismatch;
- unsupported callback/transition/external state;
- invalid replay/action seam;
- root or parent-repeat disagreement;
- unsafe restore.

Future RNG is the result of native execution. It is never forced equal across
diverged actions.

## Observed Result

One-tick A→restore→A and A→restore→B checks passed. H=2/4/8 rolling checks and
same-seam natural pumps passed at the canonical root. All 36 no-Bomb masks
were executed from one immutable root.

The first short fence produced six survivor masks
`0x14/15/90/91/94/95`, but every single-intervention branch hit soon after.
Causal endpoint promotion then searched all 36 continuations instead of
reusing the recorded suffix:

- 216 secondary branches from six promoted roots;
- 26/36 third actions survive the next segment;
- 30/36 fourth actions survive the next segment;
- 324 total native causal branches.

The maximin/tie-broken witness is:

| Root frame | Mask |
| ---: | ---: |
| 2129 | `0x94` |
| 2137 | `0x44` |
| 2145 | `0x10` |
| 2153 | `0xA4` |

It stays unhit through frame 2,161, 25 frames beyond the recorded contact. A
natural H=32 frame pump agrees for 32/32 ticks. This is one exact
fixed-root/fixed-horizon witness, not a full spell or physical success.

Primary report:

`artifacts/runtime_reports/th08_native_snapshot_causal_policy_root2129_h32_20260730.json`

## Model Differential

`ModelTrajectory` consumes only explicit root state and the declared action
schedule. It compares each modeled update with the native tick and stops at
the first mismatch.

Two important corrections:

- the old bounds treated playfield extents as player-center clamps and
  mismatched immediately;
- the old closed-form hostile projection differed by one x ULP; the
  per-update binary32 recurrence matches the retained native fixture.

The model-consumable capsule retains slot-keyed hostile identity, lifecycle
flags/timers, event deltas, player mechanics, and bounded ECL/callback/emitter
source state without duplicating every full payload.

State-2 bullet motion and its timer-9 completion were corrected and match the
focused native H1/H8 corpus. The source differential still returns `UNKNOWN`
before the known auxiliary fires: a pre-enemy/pre-aux RNG consumer is not
causally closed. Retrospective birth/RNG alignment cannot be used as model
input.

Evidence:

- `artifacts/runtime_reports/th08_native_model_trajectory_root2129_h32_20260730.json`
- `artifacts/runtime_reports/th08_native_model_consumable_h1_root2129_20260730.json`
- `artifacts/runtime_reports/th08_native_state2_lifecycle_root2129_h8_20260730.json`
- `artifacts/runtime_reports/th08_native_h1_ecl_source_differential_root2129_20260730.json`

## Throughput And Warm Service

An all-36 portfolio with semantic capture/restore originally took about 63.6
seconds. A single warm session later executed 180 branches in 309.089 seconds
with exact parent repeats. This is already much faster than whole-prefix
physical/replay branching and supports solver iteration.

A persistent service is still proposed, not accepted. It must have:

- one process/session owner and single-writer queue;
- immutable session/root IDs;
- root, FX, stack, replay cursor, thread, and map validation per branch;
- cooperative cancellation and newest-work priority;
- idle TTL and guaranteed key/thread/process cleanup;
- poison state and automatic replay rebootstrap.

One 216-branch attempt detected a committed-map epoch change after 14 branches.
That session is invalid. A service must recover from the poison event; it must
not weaken mapping identity to improve uptime.

## Replay Save

Practice replay saving resolves the live `ResultSysInf` through its registered
update node rather than a fixed heap address. The revalidated menu chain is:

`10 -> 12 -> 14 -> 13 -> 2`

The supervisor archives the old slot, writes the selected slot, decodes the
result, verifies route/difficulty/stage and an empty Bomb-press list, and then
restores/retains content-addressed evidence.

Full-route Final-B terminal unload may remove the result object before the
ending/result sequence. Absence is fail-closed and is not a reason to repeat a
complete run solely for replay retention.

## Authority And Next Gate

The wind tunnel may:

- localize one hit;
- compare all actions from the same native root;
- grow a short causal action tree;
- validate a reconstructed transition;
- produce an exact finite-horizon witness.

It may not:

- reuse recorded futures after an action change;
- generalize one replay root to a stage;
- substitute for live deadline/input-pickup validation;
- authorize a physical policy by itself.

Next, capture a generation-safe ordinary-enemy combat/resource root and use
the same loop to compare focused/unfocused/refocus schedules inside the
survival-feasible set. Only an immutable cross-root winner should advance to
a focused physical trial.

## Retention

Compact reports are tracked under `artifacts/runtime_reports/`. Large native
roots/raw branches remain ignored locally. The canonical retained root is
`artifacts/native_snapshot_rolling/native_replay_stage5_latest_root2129_capture_20260730.root`.

Material IDA annotations include the calculation seam, replay action seam,
state-2 motion/timer completion, bullet flag selection, periodic emitter gate,
and dynamic result-menu object/update-node relationship.
