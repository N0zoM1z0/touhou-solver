# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_practice_20260723_170433

## Scope And Integrity

- Valid practice scope: `93..26383` (7576 decisions).
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 10, at `[1052, 7266, 17008, 17750, 23194, 24710, 25036, 25475, 25865, 26219]`.
- Hard no-Bomb verification: **PASS** across 7576 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F1052-T1`. It occurred during a nonspell phase at player (308.118, 158.682), with 360 bullets and 0 lasers. The projectile model reported pipeline clearance -2.103.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `observed_bullet_overlap` | 7 |
| `active_laser_without_observed_overlap` | 1 |
| `modeled_committed_prefix_collision` | 1 |
| `observed_laser_overlap` | 1 |

Contributing factors:

- `corridor_deadline_miss`: 10
- `fast_mode`: 9
- `action_lag_over_model`: 2
- `playfield_boundary`: 2

## Death Ledger

| Role | Frame | Spell | Player | Action | Bullets/lasers | Pipeline/min 240f | Gate min | Primary cause |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| canonical | 1052 | nonspell | (308.118, 158.682) | `up_fast` | 360/0 | -2.103/-3.851 | -25.047 | `observed_bullet_overlap` |
| discovery | 7266 | nonspell | (39.695, 369.142) | `up` | 496/0 | 0.029/-0.655 | -12.815 | `observed_bullet_overlap` |
| discovery | 17008 | 42 野符「GHQクライシス」 | (287.422, 407.544) | `left_fast` | 477/0 | 0.745/-1.982 | -26.752 | `observed_bullet_overlap` |
| discovery | 17750 | 42 野符「GHQクライシス」 | (127.261, 419.059) | `right_fast` | 489/0 | -1.751/-2.347 | -12.563 | `observed_bullet_overlap` |
| discovery | 23194 | 46 国体「三種の神器　郷」 | (356.893, 427.513) | `left_fast` | 523/0 | 0.823/-2.406 | -11.139 | `observed_bullet_overlap` |
| discovery | 24710 | 50 虚史「幻想郷伝説」 | (92.895, 432.000) | `up_fast` | 337/200 | -3.439/-3.439 | -6.753 | `observed_laser_overlap` |
| discovery | 25036 | 50 虚史「幻想郷伝説」 | (202.320, 420.686) | `right_fast` | 284/190 | 0.039/0.039 | -3.265 | `observed_bullet_overlap` |
| discovery | 25475 | 50 虚史「幻想郷伝説」 | (191.265, 416.000) | `left_fast` | 263/200 | 1.409/-3.121 | -11.721 | `active_laser_without_observed_overlap` |
| discovery | 25865 | 50 虚史「幻想郷伝説」 | (191.507, 431.060) | `up_left_fast` | 262/181 | -5.329/-6.292 | -14.107 | `modeled_committed_prefix_collision` |
| discovery | 26219 | 50 虚史「幻想郷伝説」 | (134.831, 423.515) | `up_left_fast` | 246/162 | 0.193/-3.172 | -10.012 | `observed_bullet_overlap` |

## Interpretation

- Retained witnesses classify 7 bullet overlaps, 1 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 16.931 ms median and 45.068 ms p95.
- Spell 50 contains 5 hits. Its 84 unique corridor solves took 164.270 ms median, 362.155 ms p95, and 429.123 ms maximum.
- In spell 50, the bottom-eight-pixel occupancy fraction was 0.831 during the 60 frames preceding a hit versus 0.089 outside those windows. This separates terminal escape-space loss from solver latency alone.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 12.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Measure complete loop, decode, trace-write, and input costs; make the MPC action-hold model follow observed controller cadence instead of assuming a fixed two frames. Separately, the global objective must value terminal escape viability so that a currently clear bottom cell is not treated as a good long-horizon component when it has no repair space.
