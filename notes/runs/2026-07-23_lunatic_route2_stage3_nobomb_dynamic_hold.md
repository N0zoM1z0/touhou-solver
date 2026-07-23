# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_practice_20260723_173245

## Scope And Integrity

- Valid practice scope: `56..26550` (8884 decisions).
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Native hit edges: 8, at `[7144, 13652, 15010, 17641, 21019, 22490, 23788, 25665]`.
- Hard no-Bomb verification: **PASS** across 8884 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F7144-T1`. It occurred during a nonspell phase at player (26.313, 368.054), with 311 bullets and 0 lasers. The projectile model reported pipeline clearance -1.566.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 4 |
| `observed_bullet_overlap` | 4 |

Contributing factors:

- `corridor_deadline_miss`: 7
- `fast_mode`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 7144 | nonspell | (26.313, 368.054) | `up_right_fast` | 311/0 | -1.566/-3.254 | 3f | `modeled_committed_prefix_collision` | `committed_prefix_unsafe_before_hit` |
| discovery | 13652 | nonspell | (331.675, 392.784) | `left` | 456/0 | -1.881/-1.881 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 15010 | 38 始符「エフェメラリティ137」 | (283.023, 286.384) | `left_fast` | 311/0 | 2.988/-2.563 | 2f | `observed_bullet_overlap` | `committed_prefix_unsafe_before_hit` |
| discovery | 17641 | 42 野符「GHQクライシス」 | (268.840, 426.725) | `up_right` | 482/0 | -2.087/-2.087 | 2f | `observed_bullet_overlap` | `committed_prefix_unsafe_before_hit` |
| discovery | 21019 | nonspell | (255.682, 329.292) | `left_fast` | 355/0 | -3.340/-3.340 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 22490 | 46 国体「三種の神器　郷」 | (57.084, 421.592) | `up_fast` | 390/0 | 0.192/-1.433 | 2f | `observed_bullet_overlap` | `committed_prefix_unsafe_before_hit` |
| discovery | 23788 | 46 国体「三種の神器　郷」 | (89.151, 415.331) | `up_fast` | 464/0 | 2.459/-1.899 | 2f | `observed_bullet_overlap` | `committed_prefix_unsafe_before_hit` |
| discovery | 25665 | 50 虚史「幻想郷伝説」 | (225.925, 423.221) | `up_fast` | 253/200 | -1.930/-1.930 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 13.717 ms median and 30.701 ms p95.
- Modeled action hold counts were `{'2': 1461, '3': 6493, '4': 930}` overall and `{'3': 172, '4': 473}` in active spell 50.
- Modeled uncontrollable-prefix counts were `{'3': 8884}`.
- Of 5237 unambiguous output transitions, 4522 (0.863) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'committed_prefix_unsafe_before_hit': 5, 'late_collision_after_positive_causal_margin': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Spell 50 contains 1 hits. Its 76 unique corridor solves took 185.279 ms median, 396.457 ms p95, and 442.191 ms maximum.
- In spell 50, the bottom-eight-pixel occupancy fraction was 0.524 during the 60 frames preceding a hit versus 0.313 outside those windows. This separates terminal escape-space loss from solver latency alone.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 83.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Dynamic action hold is now physically exercised and complete loop timing is available. The next controller must model the separate actuation-delay distribution: newly injected input is usually visible one manager snapshot after SendInput, while planning cadence controls how long it remains held. The global corridor objective must also score terminal reachable volume and repair directions so a locally clear boundary cell is not accepted as a dead end.
