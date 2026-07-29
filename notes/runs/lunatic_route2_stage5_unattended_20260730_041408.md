# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260730_041408

## Scope And Integrity

- Valid practice scope: `1..42463` (11879 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 10, at `[3519, 13472, 22550, 23262, 29253, 29733, 30133, 30508, 34814, 38385]`.
- Hard no-Bomb verification: **PASS** across 11879 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Physical Provenance And Authority

- Pre-trial repository checkpoint: `23ce97a`; physically exercised code:
  `60ae5b9`.
- Original shipped executable SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`;
  the no-life-decrement byte at `0x0044D0FA` was `0x00`.
- The original-game stage-selection script chose Lunatic Sakuya/Remilia
  Stage 5 and enabled `--trace-enemy-mode-transitions` plus
  `--diagnostic-continue-root-only-scale` from stage entry. No THPRAC,
  exact-spell selection, or operator-time feature switch was used.
- The root-only scale proxy is an unknown-direction diagnostic
  approximation. Mode records and this run have physical occurrence and
  failure-analysis authority only: `action_authority=false`,
  `hard_authority=false`, and `physical_survival_authority=false`.
- The supervisor selected no-save after the terminal scene. No new compatible
  native replay was found, so no replay pass is claimed.
- Ignored raw JSONL is retained locally (482,944,752 bytes), SHA-256
  `773cbdb322dc5e15f80da4800ce82bcd0f41c1e6f82826812087edc9a328dca9`.
  The ignored launch log SHA-256 is
  `895586a05926072d22148b17b839243d570121ada0728fc611ee4d8778af5668`.
- The terminal supervisor released injected keys and terminated the game.
  Post-run process inspection found no TH08, controller, or supervisor
  process.

## SEM-MODE-B Native Observation

- The compact report covers all 11,879 decisions in frames `1..42463` and
  passes its integrity gate. It retains 11,763 coherent captures
  (`99.023%`) and explicitly excludes 116 crossed/incoherent captures:
  70 `enemy_mode_sync_mismatch`, 43 `player_or_input_changed`, and 3
  `enemy_frame_unstable`.
- 11,308 decisions were coherent on the first attempt; 571 used the bounded
  second attempt. Capture read time was 2.238 ms mean, 4.599 ms p95, and
  10.965 ms maximum.
- The report retains 1,455 adjacent focus-input edges, 299 adjacent coherent
  secondary-character transitions, and 308 unique mode-sensitive
  pointer/raw-flags pairs.
- Observed body-set witness: frames `394 -> 397` change 13 stable enemy
  pointers from flags `0x11003B49` to `0x11003349` as secondary mode changes
  true to false. Frames `444 -> 447` change 12 stable pointers in the reverse
  direction. The only changed flag bit is native enemy bit `0x800`.
- Ten root-only scale observations use unit bits `1065353216` and the explicit
  `diagnostic_constant_current_root_unknown_direction` fallback. None claims
  hard or survival authority.
- Compact mode-report SHA-256:
  `545677cead65e312942408cbaa977694be6416b7afbaea663802462c0775dfd9`.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F3519-T1`. It occurred during a nonspell phase at player (376.000, 431.585), with 954 bullets and 0 lasers. The projectile model reported pipeline clearance -2.766.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 7 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `fast_mode`: 8
- `playfield_boundary`: 5
- `pool_density_over_1000`: 4

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 3519 | nonspell | (376.000, 431.585) | `left_fast` | 954/0 | -2.766/-2.766 | 0f/3f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 13472 | nonspell | (39.857, 432.000) | `down_right` | 607/0 | 0.377/-2.621 | 5f/25f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 22550 | 103 幻波「赤眼催眠(マインドブローイング)」 | (376.000, 432.000) | `up_fast` | 889/0 | -3.052/-3.052 | 0f/7f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 23262 | 103 幻波「赤眼催眠(マインドブローイング)」 | (183.314, 416.686) | `left_fast` | 1242/0 | -2.071/-2.071 | 4f/16f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 29253 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (101.410, 432.000) | `up_right_fast` | 963/0 | -4.630/-4.630 | 8f/22f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 29733 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (148.465, 417.858) | `down_fast` | 1017/0 | -1.828/-9.118 | 30f/102f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 30133 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (143.135, 419.515) | `up_left_fast` | 1015/0 | -5.299/-5.750 | 11f/19f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 30508 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (195.082, 360.200) | `stay` | 1011/0 | -7.755/-7.755 | 8f/69f | `modeled_committed_prefix_collision` | `robust_action_set_exhausted_before_hit` |
| discovery | 34814 | nonspell | (376.000, 411.164) | `up_fast` | 460/0 | 0.365/-3.157 | 5f/39f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 38385 | 111 懶惰「生神停止(マインドストッパー)」 | (190.610, 30.320) | `left_fast` | 503/0 | -1.462/-1.462 | 0f/0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 3 | 8389 | 0 | 0 | 0 | 0 | 0 | - | 0.440 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 2 | 601 | 0 | 0 | 0 | 0 | 0 | - | 0.294 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 4 | 723 | 0 | 0 | 0 | 0 | 0 | - | 0.244 |
| 111 懶惰「生神停止(マインドストッパー)」 | 1 | 1079 | 0 | 0 | 0 | 0 | 0 | - | 0.000 |
| 115 | 0 | 1087 | 0 | 0 | 0 | 0 | 0 | - | 0.501 |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 2.000 frames median and 4.000 frames p95. The local plan took 17.200 ms median and 28.235 ms p95.
- The full enemy sensor produced 6123 snapshots; capture read time was `{'median': 4.654199932701886, 'p95': 10.219299932941794, 'max': 48.22080000303686}`, snapshot age was `{'median': 5.0, 'p95': 8.0, 'max': 13.0}` frames, and 7 phase-counter discontinuities were excluded; 11184 decisions retained at least one robust-union body (maximum 51); 8900 decisions contained latent contact-disabled geometry (maximum 51), and 3945 contained bounded inactive-slot memory (maximum 38). 247 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.3973541259765625, 'max': 5.303776502609253}` / `{'median': 0.0, 'p95': 4.441553115844727, 'max': 4.710235118865967}` / `{'median': 0.0, 'p95': 0.6671829223632812, 'max': 1.000009536743164}`.
- The issue-time enemy guard retained 11879 observations, detected 3179 during-plan geometry changes, recertified 3179 decisions, and overrode 35 actions. Read/recertificate timing was `{'median': 1.8726000562310219, 'p95': 3.7609999999403954, 'max': 9.350599953904748}` / `{'median': 2.7537000132724643, 'p95': 6.166400038637221, 'max': 21.63190010469407}` ms; 8874 issue captures contained latent bodies (maximum 51), and 3945 contained dormant bodies (maximum 38). Fresh/global transactions preserved 3144/3179 planned actions, relaxed 0 fresh/global empty intersections, inherited 0 earlier planner relaxations, and recorded 0 silent outside-global selections.
- The synchronous spell-owner guard retained 8471 observations (8441 contact enabled, 30 anticipatory, 0 errors). 8471 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 8471}`.
- The terminal-threat heuristic covered 11879 decisions with horizon counts `{'0': 598, '10': 11281}`; it reported 0 collision and 0 sub-safety-clearance warnings, and relaxed 0 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 511, '3': 9183, '4': 1786, '5': 399}` overall.
- Modeled uncontrollable-prefix counts were `{'1': 202, '2': 162, '3': 10867, '4': 423, '5': 225}`.
- Adaptive delay supports were `{'1,2': 1, '1,2,3,4': 167, '1,2,3,4,5': 249, '1,2,3,4,5,6': 432, '2,3': 152, '2,3,4': 1857, '2,3,4,5': 3952, '2,3,4,5,6': 4643, '3,4': 27, '3,4,5,6': 384, '5,6': 15}`; 164 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 30/369.
- Robust viability supplied 0 available policy queries (0 had new delay support outside the cached policy), constrained 0 decisions, and exposed 0 empty queried action sets. Recovery guidance was available/selected on 0/0 empty-kernel queries; distant-kernel guidance was available/selected on 0/0. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `None`, `None`, `None`, and `None`.
- Queried policy phase offsets within the coarse control layer were `{}`.
- Global-horizon/local-prefix cross-tab covered 0 decisions: 0 had a winning global state but unsafe selected prefix, 0 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 0 selected actions were outside the reported winning set. 0 newer issue-time hazard versions and 0 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 0 unique policies with solve-time statistics `None` and first-observed ages `None`. Policy status counts were `{}`; 0 robust-mode decisions had no query.
- Of 6164 unambiguous output transitions, 4901 (0.795) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 9, 'late_collision_after_positive_causal_margin': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 9 hit windows with a positive warning lead; those leads were `[3, 25, 7, 16, 22, 102, 19, 69, 39, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.511 during the 60 frames preceding a hit versus 0.393 outside those windows.
- Mean selected control-reserve deficit was 0.000 during the 60 frames preceding a hit versus 0.000 outside those windows.
- Soft recovery was selected on 0.000 of alive decisions in the 60-frame pre-hit windows versus 0.000 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 16.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

SEM-MODE-B physical occurrence is complete, but the first-hit failure and all
later hits remain counterexamples. Continue with SEM-MODE-C: carry the
immutable player/enemy mode key through causal pickup/cadence histories,
project enemy contact body sets at the correct update phase, and merge only
observation-compatible branches. Do not consume this diagnostic trace as
live authority or resume observer-off physical promotion before the causal
recurrence and differential gates pass.
