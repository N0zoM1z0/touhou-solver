# TH08 Stage 3 Dynamic-Hold Physical Postmortem

## Accepted Scope

- Run: `lunatic_route2_stage3_practice_20260723_173245`.
- Stage-3 manager frames: `56..26550`; 8,884 decisions.
- Initial resources: 8 lives, 4 Bombs, 128 Power.
- Native hit frames:
  `[7144, 13652, 15010, 17641, 21019, 22490, 23788, 25665]`.
- Hard no-Bomb passed across every decision and input mask.
- The `173212` trace lasted only 359 frames and ended by external stop. It is
  a discarded bootstrap attempt, not a physical candidate.

## Physical Comparison

| Metric | Fixed hold (`170433`) | Dynamic hold (`173245`) | Change |
| --- | ---: | ---: | ---: |
| Total hits | 10 | 8 | -20% |
| First hit frame | 1052 | 7144 | +6092 frames |
| Active spell-35 hits | 0 | 0 | retained |
| Active spell-50 hits | 5 | 1 | -80% |
| Spell-50 solve median | 164.3 ms | 185.3 ms | +12.8% |
| Spell-50 solve p95 | 362.2 ms | 396.5 ms | +9.5% |
| Spell-50 age p95 | 27 frames | 28 frames | +1 frame |
| Spell-50 stale solutions | 0 | 0 | unchanged |

The improvement is not explained by faster corridor solving. Spell-50 solve
latency was slightly worse while hits fell from five to one. The changed
control model is the useful intervention: spell 50 used hold 4 for 473 of 645
decisions and hold 3 for the remaining 172, matching its observed cadence of
three frames median and four frames p95.

The improvement is not uniform. Hit attribution changed from
`nonspell=2, spell42=2, spell46=1, spell50=5` to
`nonspell=3, spell38=1, spell42=1, spell46=2, spell50=1`. The new spell-38
and extra nonspell/spell-46 failures remain regressions even though the total
and final-spell results improved.

## Runtime Budget

- Complete iteration: 27.29 ms median, 45.39 ms p95, 79.28 ms maximum.
- Local MPC: 13.72 ms median, 30.70 ms p95, 54.02 ms maximum.
- Pool reads: 8.53 ms median, 12.52 ms p95, 20.58 ms maximum.
- Pool decode: 1.27 ms median, 2.40 ms p95.
- Previous trace flush: 1.04 ms median, 1.68 ms p95.
- Actual input transitions: 1.72 ms median and 5.53 ms p95.

Moving the unchanged planner behind CFFI is not the next correction. NumPy
already owns the dense hazard fields, trace cost is small, and the spell-50
physical result improved without reducing solve time.

## Control Causality

The hit-row output action is computed after native phase 2 is detected. It
cannot be the action that caused the hit. The dossier now retains the active
game input, the last alive decision, and the newly issued post-detection action
separately.

Five hits had an already-unsafe committed prefix in the last alive decision.
Their usable warning was only two or three manager frames, no longer than the
old fixed three-frame prefix. Three hits had positive last-alive margins and
zero usable warning:

| Hit | Last-alive pipeline | Active input | Result |
| ---: | ---: | --- | --- |
| 13652 | 3.628 | `left` | collision appeared after positive causal margin |
| 21019 | 0.290 | `left_fast` | collision appeared after positive causal margin |
| 25665 | 0.495 | `up_fast` | collision appeared after positive causal margin |

These are actuation-epoch or prediction-margin failures, not evidence that the
newly computed hit-row action was wrong.

Of 5,237 unambiguous output transitions, 4,522 (86.3%) were visible in the next
decision snapshot. For those transitions the SendInput-to-snapshot delta was
one frame at both median and p95. This disproves the assumption that the
three-to-four-frame decision cadence is also the actuation delay. The two plant
parameters must remain separate:

- `control_delay_frames`: previous-input prefix before a new mask takes effect;
- `action_hold_frames`: duration until the controller can replace that mask.

## Remaining Global Failure

Seven of eight hits have a negative corridor deadline somewhere in the
preceding 240 frames. The spell-50 hit is the exception: its minimum recorded
gate slack is positive, yet it occurs at y=423.2 with 200 lasers. Scalar gate
slack therefore does not certify repair space.

Spell-50 bottom-eight-pixel occupancy fell from 83.1% to 52.4% near hits, but
the surviving hit is still a terminal-boundary failure. The next global
objective must retain future reachable volume, safe successor controls, or a
connected-component repair-radius certificate.

## Prepared Experiment

The next controller estimates the uncontrollable prefix from the rolling p90
of the last 120 operational `action_lag` samples. It starts at two frames and
is clamped to `1..4`. Action hold remains its independent rolling cadence p90,
clamped to `2..6`. Both values and the estimation sample count are persisted
per decision.

Acceptance for the next Stage-3 run:

1. Hard no-Bomb and initial 8/4/128 must pass.
2. Dynamic delay must converge to the measured action-lag distribution.
3. Spell 35 must remain at zero hits.
4. Spell 50 must not regress above one hit.
5. Total hits must beat eight before the global repair-space change is judged.
