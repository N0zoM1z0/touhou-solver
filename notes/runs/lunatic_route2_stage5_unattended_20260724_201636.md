# TH08 Stage 5 No-Bomb Practice Review: lunatic_route2_stage5_unattended_20260724_201636

## Scope And Integrity

- Valid practice scope: `2..46642` (7436 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `raw_trace_end`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **YES**.
- Native hit edges: 27, at `[637, 3491, 3993, 4468, 8007, 10727, 12344, 14248, 23414, 23884, 24329, 24961, 25577, 30870, 31260, 31710, 32112, 32581, 33048, 33403, 34240, 34537, 41212, 41939, 42511, 43108, 45538]`.
- Hard no-Bomb verification: **PASS** across 7436 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S5-F637-T1`. It occurred during a nonspell phase at player (376.000, 371.820), with 480 bullets and 0 lasers. The projectile model reported pipeline clearance -3.441.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 16 |
| `observed_bullet_overlap` | 10 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `action_lag_over_model`: 14
- `pool_density_over_1000`: 12
- `playfield_boundary`: 11
- `fast_mode`: 10
- `corridor_deadline_miss`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 637 | nonspell | (376.000, 371.820) | `up_fast` | 480/0 | -3.441/-3.441 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3491 | nonspell | (8.000, 432.000) | `stay` | 397/0 | -1.467/-1.467 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 3993 | nonspell | (8.000, 432.000) | `stay` | 719/0 | -3.181/-3.181 | 0f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 4468 | nonspell | (90.448, 395.500) | `up_left_fast` | 409/0 | 0.028/-2.675 | 4f/4f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 8007 | nonspell | (316.268, 432.000) | `down` | 735/0 | -1.956/-10.765 | 52f/57f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 10727 | nonspell | (75.267, 378.700) | `left` | 869/0 | -2.208/-2.208 | 0f/0f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 12344 | nonspell | (376.000, 267.875) | `stay` | 330/0 | -2.202/-2.202 | 0f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 14248 | nonspell | (190.460, 412.201) | `right` | 265/0 | -1.742/-7.554 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23414 | 103 幻波「赤眼催眠(マインドブローイング)」 | (8.000, 100.616) | `stay` | 1371/0 | -3.540/-3.540 | 10f/18f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 23884 | 103 幻波「赤眼催眠(マインドブローイング)」 | (99.737, 432.000) | `left_fast` | 1092/0 | -3.660/-3.660 | 0f/9f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24329 | 103 幻波「赤眼催眠(マインドブローイング)」 | (265.963, 432.000) | `down_right` | 1091/0 | -2.488/-2.488 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24961 | 103 幻波「赤眼催眠(マインドブローイング)」 | (230.050, 39.605) | `up_left` | 1259/0 | -2.195/-7.045 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 25577 | 103 幻波「赤眼催眠(マインドブローイング)」 | (351.605, 307.605) | `up_fast` | 854/0 | -2.618/-3.631 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 30870 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (165.945, 389.574) | `left_fast` | 767/0 | 0.455/-6.046 | 16f/16f | `sensor_gap_or_unmodeled_hazard` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31260 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (11.326, 96.196) | `left` | 979/0 | -7.530/-10.965 | 75f/75f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31710 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (260.032, 395.499) | `right` | 1008/0 | -6.004/-8.185 | 28f/144f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32112 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (332.632, 290.880) | `down` | 1007/0 | -9.166/-10.240 | 34f/93f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32581 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (99.571, 263.850) | `up_right_fast` | 1007/0 | -8.374/-9.580 | 149f/156f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33048 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (311.555, 432.000) | `down_right` | 1017/0 | -6.815/-10.892 | 14f/136f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33403 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (149.701, 370.241) | `left_fast` | 1002/0 | -8.996/-10.142 | 34f/34f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34240 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (34.214, 310.188) | `up_left` | 1014/0 | -8.948/-9.997 | 43f/43f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 34537 | 107 狂視「狂視調律(イリュージョンシーカー)」 | (199.699, 217.307) | `up_fast` | 1010/0 | -6.307/-18.680 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 41212 | 111 懶惰「生神停止(マインドストッパー)」 | (168.331, 199.756) | `left` | 367/0 | -4.612/-4.612 | 7f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 41939 | 111 懶惰「生神停止(マインドストッパー)」 | (185.894, 194.330) | `up_left` | 345/0 | -1.399/-1.399 | 0f/8f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 42511 | 111 懶惰「生神停止(マインドストッパー)」 | (192.475, 35.658) | `down_right_fast` | 504/0 | -2.596/-2.596 | 0f/6f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 43108 | 111 懶惰「生神停止(マインドストッパー)」 | (192.179, 171.957) | `down_left` | 335/0 | -2.100/-2.100 | 6f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 45538 | 115 散符「真実の月(インビジブルフルムーン)」 | (376.000, 432.000) | `up_left_fast` | 1285/0 | -1.916/-1.916 | 6f/11f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 8 | 4871 | 4770 | 3269 | 0 | 1489 | 1113 | 98.797 | 0.216 |
| 103 幻波「赤眼催眠(マインドブローイング)」 | 5 | 584 | 576 | 176 | 0 | 400 | 167 | 142.925 | 0.167 |
| 107 狂視「狂視調律(イリュージョンシーカー)」 | 9 | 699 | 693 | 561 | 0 | 129 | 253 | 105.856 | 0.150 |
| 111 懶惰「生神停止(マインドストッパー)」 | 4 | 663 | 657 | 218 | 0 | 436 | 174 | 99.688 | 0.000 |
| 115 散符「真実の月(インビジブルフルムーン)」 | 1 | 619 | 613 | 411 | 0 | 196 | 172 | 65.447 | 0.484 |

## Interpretation

- Retained witnesses classify 10 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 4.000 frames median and 8.000 frames p95. The local plan took 28.445 ms median and 60.513 ms p95.
- The full enemy sensor produced 6367 snapshots; capture read time was `{'median': 33.894099993631244, 'p95': 60.743700014427304, 'max': 98.2419999781996}`, snapshot age was `{'median': 6.0, 'p95': 11.0, 'max': 21.0}` frames, and 6 phase-counter discontinuities were excluded; 5221 decisions retained at least one robust-union body (maximum 48); 2699 decisions contained latent contact-disabled geometry (maximum 48), and 3558 contained bounded inactive-slot memory (maximum 45). 646 body samples retained observed world-motion estimates; world/internal speed and disagreement were `{'median': 0.0, 'p95': 4.477142333984375, 'max': 9.27862548828125}` / `{'median': 0.0, 'p95': 4.472171783447266, 'max': 5.484699249267578}` / `{'median': 0.0, 'p95': 1.0, 'max': 4.372798919677734}`.
- The issue-time enemy guard retained 7436 observations, detected 2198 during-plan geometry changes, recertified 2198 decisions, and overrode 771 actions. Read/recertificate timing was `{'median': 2.273199992487207, 'p95': 4.885400005150586, 'max': 25.531899998895824}` / `{'median': 12.976850004633889, 'p95': 24.321000004420057, 'max': 37.78039998724125}` ms; 2672 issue captures contained latent bodies (maximum 48), and 3578 contained dormant bodies (maximum 45).
- The synchronous spell-owner guard retained 2565 observations (2550 contact enabled, 15 anticipatory, 0 errors). 2565 observed owners were outside the ordinary 480-slot async scan; pointer counts were `{'0x0057D2F0': 2565}`.
- The terminal-threat heuristic covered 7436 decisions with horizon counts `{'0': 91, '10': 7248, '32': 97}`; it reported 1 collision and 24 sub-safety-clearance warnings, and relaxed 24 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 44, '3': 109, '4': 364, '5': 3177, '6': 3742}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 51, '3': 219, '4': 657, '5': 4053, '6': 2456}`.
- Adaptive delay supports were `{'1,2,3': 16, '1,2,3,4,5,6': 1, '2,3': 66, '2,3,4': 26, '2,3,4,5': 77, '2,3,4,5,6': 354, '3': 1, '3,4': 4, '3,4,5': 62, '3,4,5,6': 4851, '4,5,6': 1685, '5,6': 264, '6': 29}`; 1040 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 300/210.
- Robust viability supplied 7309 available policy queries (0 had new delay support outside the cached policy), constrained 2650 decisions, and exposed 4635 empty queried action sets. Recovery guidance was available/selected on 549/331 empty-kernel queries; distant-kernel guidance was available/selected on 3633/3383. Safe-action count, selected repair-volume, selected recovery-distance, and selected control-reserve deficit statistics were `{'median': 0.0, 'p95': 17.0, 'max': 17.0}`, `{'median': 0.0, 'p95': 153.0, 'max': 153.0}`, `{'median': 147.5127113166862, 'p95': 339.4112549695428, 'max': 502.41019097944263}`, and `{'median': 0.0, 'p95': 24.0, 'max': 48.0}`.
- Queried policy phase offsets within the coarse control layer were `{'0': 1120, '1': 1122, '2': 968, '3': 864, '4': 773, '5': 800, '6': 851, '7': 811}`.
- Global-horizon/local-prefix cross-tab covered 3892 decisions: 0 had a winning global state but unsafe selected prefix, 2655 had a losing global state but safe short prefix, 0 selected globally certified actions contradicted the fresh local prefix checker, and 7 selected actions were outside the reported winning set. 1495 newer issue-time hazard versions and 8 deadline-held old inputs were excluded from the aligned comparison.
- The rolling worker produced 1879 unique policies with solve-time statistics `{'median': 100.17180000431836, 'p95': 166.7068999959156, 'max': 201.27619997947477}` and first-observed ages `{'median': 5.0, 'p95': 10.0, 'max': 1799.0}`. Policy status counts were `{'pending_future_epoch': 37, 'queryable': 7312, 'expired': 22}`; 62 robust-mode decisions had no query.
- Of 4150 unambiguous output transitions, 3526 (0.850) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'global_viability_kernel_exhausted_before_hit': 26, 'missing_pre_hit_alive_decision': 1}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 22 hit windows with a positive warning lead; those leads were `[5, 5, 5, 4, 57, 0, 11, 0, 18, 9, 6, 0, 0, 16, 75, 144, 93, 156, 136, 34, 43, 0, 7, 8, 6, 6, 11]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.267 during the 60 frames preceding a hit versus 0.220 outside those windows.
- Mean selected control-reserve deficit was 4.557 during the 60 frames preceding a hit versus 2.471 outside those windows.
- Soft recovery was selected on 0.050 of alive decisions in the 60-frame pre-hit windows versus 0.052 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 0.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Post-Run Differential Audit

- This run intentionally enabled exact lowered-hazard capsules. Capsule I/O
  was synchronous in this controller version and added `91.58/117.58 ms`
  median/p95 to `100.17/166.71 ms` policy solves. Do not use its hit count or
  worker service time as a causal comparison with non-capture runs.
- The last two available pre-hit queries for all 27 hits reconstructed the
  live 16-pixel result exactly: 54/54 were empty in both trace and replay.
- Primary classes are 51 modeled-losing/unresolved and three 16-pixel spatial
  coarse false-empties. One separate phase-107 collision bullet was absent
  from its governing policy source.
- Fused native survival labels identify one query before hit 3,491 where the
  best set guaranteed 10 modeled frames over an eight-frame hit interval;
  endpoint-distance recovery issued `down_right_fast` outside that set.
- Full methods, limitations, and witness rows are in
  `notes/STAGE5_VIABILITY_DIFFERENTIAL_AUDIT_20260724.md` and
  `artifacts/viability_audit/stage5_20260724_201636.json`.
