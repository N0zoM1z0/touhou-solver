# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260731_122855

## Scope And Integrity

- Valid practice scope: `1..43891` (13306 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 13, at `[6981, 23145, 24853, 28755, 29488, 30790, 31811, 36229, 36649, 40449, 41488, 41957, 43231]`.
- Hard no-Bomb verification: **PASS** across 13306 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F6981-T1`. It occurred during a nonspell phase at player (340.731, 426.343), with 635 bullets and 0 lasers. The projectile model reported pipeline clearance -1.118.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 9 |
| `observed_bullet_overlap` | 4 |

Contributing factors:

- `fast_mode`: 11
- `playfield_boundary`: 8
- `pool_density_over_1000`: 6

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 6981 | nonspell | (340.731, 426.343) | `stay` | 635/0 | -1.118/-9.558 | 0f/0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 23145 | 103 幻波「赤眼催眠(マインドブローイング)」 | (12.879, 432.000) | `up_right_fast` | 892/0 | -1.508/-1.508 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 24853 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `stay` | 1105/0 | -1.127/-1.127 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 28755 | nonspell | (11.253, 432.000) | `up_right_fast` | 1073/0 | -1.424/-1.424 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 29488 | nonspell | (376.000, 432.000) | `up_fast` | 1068/0 | -1.991/-1.991 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30790 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (148.902, 432.000) | `up_right_fast` | 971/0 | -6.561/-6.561 | 4f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 31811 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (90.264, 432.000) | `up_left_fast` | 992/0 | -6.367/-6.367 | 4f/20f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 36229 | nonspell | (376.000, 432.000) | `up_fast` | 468/0 | -1.607/-1.607 | 0f/4f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 36649 | nonspell | (12.879, 399.264) | `down_right_fast` | 445/0 | -2.168/-2.168 | 2f/12f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 40449 | 111 懶惰「生神停止(マインドストッパー)」 | (193.486, 16.000) | `right_fast` | 502/0 | -2.280/-2.280 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 41488 | 115 散符「真実の月(インビジブルフルムーン)」 | (153.673, 424.000) | `right_fast` | 1173/0 | -1.904/-2.693 | 5f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 41957 | 115 散符「真実の月(インビジブルフルムーン)」 | (133.249, 432.000) | `up_fast` | 1056/0 | -2.301/-2.301 | 0f/6f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 43231 | 115 散符「真実の月(インビジブルフルムーン)」 | (129.564, 423.515) | `right_fast` | 1159/0 | 0.472/-4.049 | 6f/9f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 5 | 9362 | 0 | 0 | 0 | 0 | 0 | - | 0.394 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 935 | 0 | 0 | 0 | 0 | 0 | - | 0.365 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 2 | 699 | 0 | 0 | 0 | 0 | 0 | - | 0.272 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1108 | 0 | 0 | 0 | 0 | 0 | - | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 3 | 1202 | 0 | 0 | 0 | 0 | 0 | - | 0.426 |

## Interpretation

- Retained witnesses classify 4 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 16.862 ms median and 25.244 ms p95.
- The full enemy sensor produced 6749 snapshots; capture read time was `{'median': 4.380400001537055, 'p95': 9.697600005893037, 'max': 40.070899995043874}`, snapshot age was `{'median': 5.0, 'p95': 7.0, 'max': 11.0}` frames, and 7 phase-counter discontinuities were excluded; 12577 decisions retained at least one robust-union body (maximum 42); 9987 decisions contained latent contact-disabled geometry (maximum 42), and 4568 contained bounded inactive-slot memory (maximum 36). 227 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.7412319183349609, 'p95': 1.9318313598632812, 'max': 1.98291015625}` / `{'median': 0.0, 'p95': 1.9513872861862183, 'max': 1.9829552173614502}` / `{'median': 0.0, 'p95': 0.9658595323562622, 'max': 1.4893341064453125}`.
- The issue-time enemy guard retained 13306 observations, detected 3633 during-plan geometry changes, recertified 3633 decisions, and overrode 62 actions. Read/recertificate timing was `{'median': 1.631999999517575, 'p95': 2.8984000091440976, 'max': 7.448699994711205}` / `{'median': 2.515899992431514, 'p95': 5.38639999285806, 'max': 15.80570000805892}` ms; 9956 issue captures contained latent bodies (maximum 42), and 4564 contained dormant bodies (maximum 37). Fresh/global transactions preserved 3571/3633 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 9619 observations (9589 contact enabled, 30 anticipatory, 0 errors). 9619 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 9619}`.
- The terminal-threat heuristic covered 13306 decisions with horizon counts `{'0': 628, '10': 12678}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 1574, '3': 10579, '4': 1078, '5': 75}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 334, '2': 5146, '3': 6875, '4': 951}`.
- Adaptive delay supports were `{'1': 158, '1,2': 100, '1,2,3': 3, '1,2,3,4': 502, '1,2,3,4,5': 48, '1,2,3,4,5,6': 289, '2': 6, '2,3': 1473, '2,3,4': 5810, '2,3,4,5': 2226, '2,3,4,5,6': 1984, '3,4': 32, '3,4,5': 50, '3,4,5,6': 625}`; 96 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 56/338.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 6776 unambiguous output transitions, 6036 (0.891) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 1, 'robust_action_set_exhausted_before_hit': 12}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[0, 6, 7, 6, 7, 12, 20, 4, 12, 3, 11, 6, 9]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.569 during the 60 frames preceding a hit versus 0.349 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 2.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

The default-off kill-before-saturation rule was physically exercised, so this
run is not an empty feature gate:

- **Observed:** 109 decisions selected a matching low-HP ordinary-enemy
  target. Of 37 same-direction unfocus requests, 27 were accepted by a fresh
  issue-safe certificate, four were rejected because the unfocused action was
  not fresh-safe, and six failed closed because no fresh recertification
  transaction was available.
- **Observed:** ten accepted preferences occurred before the canonical first
  hit. No preference coincided with an issue-deadline miss. All complete masks
  and the accepted replay remained no-Bomb.
- **Observed:** no decision received global allowed actions, no decision was
  viability-constrained, and the rolling global worker produced no policy.
  Early-kill action authority therefore did not rescue the current global
  delivery/kernel path in this physical gate.
- **Observed, different RNG:** first hit moved from the prior Stage-5
  workload's frame 2124 to 6981, while total hits changed from 12 to 13.
- **Inferred:** this is mixed physical evidence, not a causal A/B. It does not
  overturn the separate same-root native observation that one early defeat
  prevented hostile births, and it does not justify promoting the rule
  route-wide.

Compact recomputation:
`artifacts/runtime_reports/th08_kill_before_saturation_physical_stage5_20260731_122855.json`.

The next decisive gate is a second same-root enemy/root plus a rotated
physical workload after global publication is available. Do not broaden the
HP/alignment heuristic from this single different-RNG run.
