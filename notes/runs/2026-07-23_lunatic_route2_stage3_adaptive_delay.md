# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_adaptive_delay_20260723_184741

## Scope And Integrity

- Valid practice scope: `57..26582` (8005 decisions).
- Scope terminator: `frame_counter_regression`; 477 reset-tail decisions were excluded.
- The agent's raw summary is not scope-valid because thprac reset the manager counter before the external stop.
- Native hit edges: 6, at `[2340, 16705, 20469, 22792, 23960, 24489]`.
- Hard no-Bomb verification: **PASS** across 8005 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F2340-T1`. It occurred during a nonspell phase at player (300.328, 413.423), with 289 bullets and 0 lasers. The projectile model reported pipeline clearance -1.538.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 4 |
| `observed_bullet_overlap` | 2 |

Contributing factors:

- `corridor_deadline_miss`: 6
- `fast_mode`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 2340 | nonspell | (300.328, 413.423) | `up` | 289/0 | -1.538/-1.538 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 16705 | 42 野符「GHQクライシス」 | (12.288, 422.404) | `up_right_fast` | 484/0 | -2.883/-2.883 | 2f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 20469 | nonspell | (201.409, 393.759) | `up_right_fast` | 370/0 | -1.784/-1.784 | 0f/5f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 22792 | 46 国体「三種の神器　郷」 | (278.988, 396.930) | `down_fast` | 438/0 | -0.588/-0.588 | 0f/7f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 23960 | 46 国体「三種の神器　郷」 | (320.764, 364.971) | `down_right_fast` | 416/0 | -1.045/-1.045 | 0f/6f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 24489 | 46 国体「三種の神器　郷」 | (62.621, 360.106) | `right_fast` | 477/0 | -0.804/-0.804 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |

## Interpretation

- Retained witnesses classify 2 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 3.000 frames median and 4.000 frames p95. The local plan took 18.192 ms median and 35.261 ms p95.
- Modeled action hold counts were `{'2': 319, '3': 5890, '4': 1609, '5': 187}` overall and `{'3': 19, '4': 306, '5': 187}` in active spell 50.
- Modeled uncontrollable-prefix counts were `{'1': 11, '2': 735, '3': 6921, '4': 338}`.
- Adaptive delay supports were `{'1,2': 11, '1,2,3': 37, '2': 9, '2,3': 170, '2,3,4': 1801, '2,3,4,5': 3058, '2,3,4,5,6': 1868, '3,4': 112, '3,4,5': 466, '3,4,5,6': 473}`; 135 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 50/486.
- Of 4705 unambiguous output transitions, 4067 (0.864) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 6}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 6 hit windows with a positive warning lead; those leads were `[6, 4, 5, 7, 6, 3]` frames.
- Spell 50 contains 0 hits. Its 71 unique corridor solves took 240.381 ms median, 458.480 ms p95, and 546.025 ms maximum.
- In spell 50, the bottom-eight-pixel occupancy fraction was - during the 60 frames preceding a hit versus 0.269 outside those windows. This separates terminal escape-space loss from solver latency alone.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 100.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Acceptance Verdict

- **Accepted as the new Stage-3 no-Bomb discovery baseline:** total hits fell from 8 to 6 (25%) against `173245`, and from 11 to 6 against the rejected scalar-delay run.
- Spell 35 remained at 0 hits. Spell 38 improved from 1 to 0 and spell 50 improved from 1 to 0.
- Spell 46 regressed from 2 to 3 hits and is now the dominant phase-specific target.
- Initial resources were 8 lives / 3 Bombs / 128 Power versus 8 / 4 / 128 in `173245`. No Bomb input occurred in either run; Bomb-item utility is unchanged while stock is below eight.

## Robust-Control Postmortem

- Every hit had an unsafe last-alive robust certificate. Continuous robust action-set exhaustion began 6, 4, 5, 7, 6, and 3 frames before the respective hit.
- The old scalar pipeline classification hid this signal: five cases retained positive nominal prefix clearance, but no surviving first action was safe over the learned delay support.
- The controller changed the nominal first action 135 times. This was sufficient to remove all spell-50 hits, but it currently reacts only after the nominal action becomes unsafe. It does not value how many safe successor controls or how much reachable repair volume remain.
- All six 240-frame windows contain a corridor deadline miss, but only 5.5% of alive near-hit decisions had negative instantaneous slack versus 9.2% outside hit windows. The window-level contributor is not evidence that corridor latency caused these contacts.

## Cost And Estimator Limits

- Local planning rose from 13.717/30.701 ms median/p95 to 18.192/35.261 ms. Decision cadence rose from 2/3 frames to 3/4.
- Spell-50 corridor solve p95 rose from 396.457 to 458.480 ms and result-age p95 from 28 to 32 frames, but no result was stale and spell 50 had zero hits.
- The estimator retained 120 recent end-to-end samples; cumulative maximum counters were 50 support overruns and 486 overwritten/censored transitions. 4,067 of 4,705 unambiguous transitions were visible on the next observation.
- A matching `input_current` frame is presently treated as a point sample even though pickup occurred within the interval since the last mismatching observation. This upper-bound bias helps safety but keeps the guard active for 6,970 of 8,005 decisions and frequently expands support through frame 6.

## Next Correction Gate

Add a game-neutral robust viability term before collision: safe first-action count, robust safe successor count over a second control interval, and reachable repair volume. Spell 46 must fall below three hits without reintroducing spell-50 failures. Separately, represent input pickup as interval-censored bounds so conservatism is calibrated without using poll cadence as exact plant delay.
