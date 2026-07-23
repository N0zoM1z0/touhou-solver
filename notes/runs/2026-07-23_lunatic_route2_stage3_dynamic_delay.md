# TH08 Stage 3 No-Bomb Practice Review: lunatic_route2_stage3_dynamic_delay_20260723_180832

## Scope And Integrity

- Valid practice scope: `68..26736` (8878 decisions).
- Scope terminator: `frame_counter_regression`; 1388 reset-tail decisions were excluded.
- The agent's raw summary is not scope-valid because thprac reset the manager counter before the external stop.
- Native hit edges: 11, at `[1850, 2703, 7377, 12441, 16182, 21418, 23938, 24358, 25203, 25538, 26300]`.
- Hard no-Bomb verification: **PASS** across 8878 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S2-F1850-T1`. It occurred during a nonspell phase at player (186.346, 372.174), with 151 bullets and 0 lasers. The projectile model reported pipeline clearance -1.945.

The primary class is `modeled_committed_prefix_collision`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Baseline Comparison Verdict

- Against the accepted `173245` dynamic-hold run, total hits regressed from 8 to 11 (+37.5%).
- Active spell-50 hits regressed from 1 to 3.
- Spell-50 corridor solve p95 improved from 396.457 ms to 383.891 ms, solution-age p95 improved from 28 to 27 frames, and both runs had zero stale solutions.
- The delay-2 scalar path therefore fails physical acceptance independently of corridor performance. A p90 point estimate is not conservative because earlier and later input pickup produce different trajectories.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `modeled_committed_prefix_collision` | 8 |
| `observed_bullet_overlap` | 3 |

Contributing factors:

- `corridor_deadline_miss`: 10
- `fast_mode`: 10
- `action_lag_over_model`: 1

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 1850 | nonspell | (186.346, 372.174) | `down_right_fast` | 151/0 | -1.945/-1.945 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 2703 | nonspell | (220.970, 378.161) | `down_right_fast` | 304/0 | -1.921/-1.921 | 0f | `observed_bullet_overlap` | `late_collision_after_positive_causal_margin` |
| discovery | 7377 | nonspell | (28.922, 322.804) | `up_right_fast` | 471/0 | -1.835/-1.835 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 12441 | nonspell | (190.284, 279.672) | `up_left_fast` | 401/0 | -1.636/-1.636 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 16182 | 38 始符「エフェメラリティ137」 | (283.982, 416.469) | `left_fast` | 273/0 | -2.581/-2.581 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 21418 | nonspell | (213.265, 410.478) | `up_left_fast` | 436/0 | -3.085/-3.085 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 23938 | 46 国体「三種の神器　郷」 | (193.867, 422.368) | `up_fast` | 406/0 | -3.071/-3.071 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |
| discovery | 24358 | 46 国体「三種の神器　郷」 | (181.246, 390.317) | `up_left_fast` | 426/0 | -0.198/-1.559 | 2f | `observed_bullet_overlap` | `committed_prefix_unsafe_before_hit` |
| discovery | 25203 | 50 虚史「幻想郷伝説」 | (92.783, 388.623) | `up_right_fast` | 265/200 | 1.056/-3.908 | 3f | `observed_bullet_overlap` | `committed_prefix_unsafe_before_hit` |
| discovery | 25538 | 50 虚史「幻想郷伝説」 | (168.965, 408.107) | `up_right_fast` | 305/200 | -2.364/-2.448 | 3f | `modeled_committed_prefix_collision` | `committed_prefix_unsafe_before_hit` |
| discovery | 26300 | 50 虚史「幻想郷伝説」 | (196.694, 403.259) | `down_left` | 268/200 | -2.796/-2.796 | 0f | `modeled_committed_prefix_collision` | `late_collision_after_positive_causal_margin` |

## Interpretation

- Retained witnesses classify 3 bullet overlaps, 0 laser overlaps, and 0 exact same-epoch enemy-body overlaps.
- The controller decision cadence was 2.000 frames median and 3.000 frames p95. The local plan took 13.676 ms median and 30.764 ms p95.
- Modeled action hold counts were `{'2': 1207, '3': 6416, '4': 1255}` overall and `{'3': 70, '4': 611}` in active spell 50.
- Modeled uncontrollable-prefix counts were `{'1': 1216, '2': 6505, '3': 1157}`.
- Of 4887 unambiguous output transitions, 4335 (0.887) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'late_collision_after_positive_causal_margin': 8, 'committed_prefix_unsafe_before_hit': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Spell 50 contains 3 hits. Its 81 unique corridor solves took 176.228 ms median, 383.891 ms p95, and 447.645 ms maximum.
- In spell 50, the bottom-eight-pixel occupancy fraction was 0.098 during the 60 frames preceding a hit versus 0.234 outside those windows. This separates terminal escape-space loss from solver latency alone.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 56.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Replace the scalar delay with an online end-to-end distribution learned from command transitions becoming visible in TH08 `input_current`. Certify the emitted first action over the learned support until the following command can take effect. A fresh Stage-3 run must beat eight total hits without increasing spell-50 hits, preserve hard no-Bomb, keep loop cadence stable, and retain estimator samples, censored transitions, overruns, support changes, and robust overrides in its dossier.
