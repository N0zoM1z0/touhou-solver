# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_practice_20260723_160344

## Scope And Integrity

- Valid practice scope: `54..26858` (7487 decisions).
- Scope terminator: `frame_counter_regression`; 287 reset-tail decisions were excluded.
- The agent's raw summary is not scope-valid because thprac reset the manager counter before the external stop.
- Native hit edges: 16, at `[4885, 5974, 7341, 13729, 14937, 16585, 17242, 21658, 23093, 23500, 25115, 25433, 25742, 26067, 26378, 26700]`.
- Hard no-Bomb verification: **PASS** across 7487 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F4885-T1`. It occurred during spell 35 `産霊「ファーストピラミッド」` at player (178.775, 156.000), with 0 bullets and 0 lasers. The projectile model reported pipeline clearance 9999.000.

This is a strong enemy-body collision candidate, not a bullet-planner miss. Static analysis proves that the active spell owner can invoke a lethal player/enemy AABB check at `0x42cf7a -> 0x42c290 -> 0x44a360`. The baseline trace records the owner pointer but not its position/contact size/flags, so exact same-frame overlap remains the next telemetry closure.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 6 |
| `observed_bullet_overlap` | 5 |
| `active_laser_without_observed_overlap` | 3 |
| `enemy_body_contact_candidate` | 1 |
| `observed_laser_overlap` | 1 |

Contributing factors:

- `fast_mode`: 14
- `corridor_deadline_miss`: 11
- `action_lag_over_model`: 6
- `playfield_boundary`: 5

## Death Ledger

| Role | Frame | Spell | Player | Action | Bullets/lasers | Pipeline/min 240f | Gate min | Primary cause |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| canonical | 4885 | 35 産霊「ファーストピラミッド」 | (178.775, 156.000) | `down` | 0/0 | 9999.000/12.110 | -2.500 | `enemy_body_contact_candidate` |
| discovery | 5974 | 35 産霊「ファーストピラミッド」 | (263.671, 389.385) | `up_fast` | 203/0 | -1.346/-1.346 | -10.616 | `modeled_committed_prefix_collision` |
| discovery | 7341 | nonspell | (41.460, 288.619) | `down_fast` | 440/0 | -2.888/-2.888 | -5.135 | `observed_bullet_overlap` |
| discovery | 13729 | nonspell | (250.829, 394.776) | `up_fast` | 324/0 | -3.937/-3.937 | -4.555 | `modeled_committed_prefix_collision` |
| discovery | 14937 | 38 始符「エフェメラリティ137」 | (69.843, 307.105) | `right_fast` | 293/0 | -1.867/-3.369 | -21.313 | `modeled_committed_prefix_collision` |
| discovery | 16585 | 42 野符「GHQクライシス」 | (305.040, 418.779) | `up_fast` | 482/0 | -1.225/-1.792 | -17.237 | `observed_bullet_overlap` |
| discovery | 17242 | 42 野符「GHQクライシス」 | (8.000, 410.879) | `up_fast` | 461/0 | 1.629/-2.969 | -10.204 | `observed_bullet_overlap` |
| discovery | 21658 | nonspell | (106.503, 408.008) | `right_fast` | 417/0 | -1.680/-1.680 | -12.153 | `modeled_committed_prefix_collision` |
| discovery | 23093 | 46 国体「三種の神器　郷」 | (75.222, 388.082) | `up_fast` | 379/0 | 0.759/0.759 | -0.696 | `observed_bullet_overlap` |
| discovery | 23500 | 46 国体「三種の神器　郷」 | (363.327, 422.278) | `up` | 347/0 | 2.315/-1.629 | -6.587 | `observed_bullet_overlap` |
| discovery | 25115 | 50 虚史「幻想郷伝説」 | (213.728, 432.000) | `right_fast` | 233/180 | 0.707/-2.429 | -2.153 | `active_laser_without_observed_overlap` |
| discovery | 25433 | 50 虚史「幻想郷伝説」 | (105.890, 414.110) | `down_left_fast` | 335/200 | 1.657/-6.850 | - | `active_laser_without_observed_overlap` |
| discovery | 25742 | 50 虚史「幻想郷伝説」 | (171.166, 432.000) | `left_fast` | 333/190 | -5.619/-6.999 | - | `modeled_committed_prefix_collision` |
| discovery | 26067 | 50 虚史「幻想郷伝説」 | (153.657, 432.000) | `left_fast` | 280/200 | -1.876/-6.824 | - | `observed_laser_overlap` |
| discovery | 26378 | 50 虚史「幻想郷伝説」 | (110.544, 409.000) | `down_left_fast` | 279/190 | 2.649/-6.239 | - | `active_laser_without_observed_overlap` |
| discovery | 26700 | 50 虚史「幻想郷伝説」 | (205.202, 432.000) | `right_fast` | 249/200 | -0.899/-7.053 | - | `modeled_committed_prefix_collision` |

## Interpretation

- Retained witnesses classify 5 bullet overlaps, 1 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 16.748 ms median and 44.230 ms p95.
- Spell 50 contains 6 hits. Its 32 unique corridor solves took 895.433 ms median, 2993.639 ms p95, and 3196.693 ms maximum.
- In spell 50, the bottom-eight-pixel occupancy fraction was 0.643 during the 60 frames preceding a hit versus 0.000 outside those windows. This separates terminal escape-space loss from solver latency alone.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Baseline Correction Gate

Add active-enemy lethal AABBs to the runtime snapshot, predictor, and corridor occupancy. The next fresh Stage-3 run must eliminate the spell-35 body contact as its canonical first hit without regressing the no-Bomb invariant.

## Offline Correction Prepared

- The live adapter now reads the active spell owner's native contact window and lowers its proven lethal AABB into local and global planners.
- Runtime hit telemetry now captures the native player lethal rectangle and spell-owner AABB in a stable manager-frame epoch.
- Local and global finite laser-segment clearance fields are vectorized; physical acceptance remains pending in this baseline report.
