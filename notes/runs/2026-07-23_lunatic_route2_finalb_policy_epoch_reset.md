# TH08 Final B Policy-Epoch Reset Physical Review

## Trial Identity

- Run id:
  `lunatic_route2_finalb_policy_epoch_reset_20260723_234414`
- Executable:
  `D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)\th08.exe`
- Executable SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
- Scope: Lunatic, Sakuya/Remilia route 2, focused thprac Final B.
- Manager frames: `1..70295`; 17,723 decisions in one monotone frame epoch.
- Termination: native `route_complete`.
- Integrity: no parse/runtime error; raw summary agrees with the selected
  scope; no manual Z intervention was reported.
- Runtime patch: no-life-decrement byte verified at `0x44D0FA`.
- Bomb policy: hard disabled. All 17,723 masks, flags, and actions pass the
  no-Bomb audit.

## Outcome

- Native hit edges: 37.
- Phase hits: nonspell 6; spell 150 three; 154 three; 158 one; 162 seven;
  166 six; 170 seven; 174 one; 178 one; 182 zero; 186 one; 190 one.
- Contact taxonomy: 14 observed bullet overlaps, nine observed laser
  overlaps, 13 modeled committed-prefix collisions, and one sensor gap or
  unmodeled hazard.
- Planner taxonomy: 26 global viability-kernel exhaustions, nine local robust
  action-set exhaustions, and two missing preceding alive decisions.
- The full frame list, pre-hit geometry, warning leads, active input, delay
  support, resource state, and spell names are retained in the death CSV and
  executable regression artifact.

## What Passed

The prior `222808` selected attempt inherited a roughly 70k submit clock and
had no global policy until spell 190. This fresh run started submitting and
querying near the beginning of Final B.

| Delivery metric | Prior selected epoch | This run |
| --- | ---: | ---: |
| Native policies | 5 | 911 |
| Available queries | 65 | 16,813 |
| Constrained decisions | 3 | 8,164 |
| Solve median | 4,149.5 ms | 208.1 ms |
| Solve p95 | 4,871.1 ms | 369.3 ms |
| Solve max | 8,562.8 ms | 609.3 ms |
| Median serial margin | -544 frames | +32 frames |
| Expired policy decisions | 452 | 255 |

This physically accepts both corrections behind that change:

- gameplay-epoch reset prevents a restarted thprac attempt from inheriting
  the previous submit clock or completed future;
- the native transition cache keeps sparse/open viability workloads
  serviceable under actual game contention.

It does not accept Final-B survival.

## Why It Still Died

Of 16,813 available policy queries, 8,292 returned an empty robust action set.
The system is now calculating and delivering policies quickly enough, but the
queried live state is outside the finite-horizon controlled set for almost
half of those queries.

The dominant general symptom is long-horizon positioning:

- 47.3% of alive decisions in the 60 frames before a hit occupied the bottom
  eight pixels, versus 20.2% outside those windows;
- 18 of 37 hits had a playfield-boundary factor;
- spell 166 returned an empty set for 1,043 of 1,131 queries;
- spells 162 and 170 each produced seven hits;
- 35 hit windows had advance robust exhaustion evidence, sometimes tens or
  hundreds of frames before contact.

The first fresh-attempt hit at frame 1441 is also a distinct model defect. The
captured bullet AABB remained 2.06 pixels clear while the native hit edge
occurred. It is retained as a sensor-gap or unmodeled-transform witness rather
than being forced into the positioning class.

The next correction should not be another planner-language or kernel-speed
rewrite. It must preserve a nonempty viability funnel across rolling epochs:

- predict future ECL emissions and laser phase/geometry changes;
- replace a merely collision-free finite-horizon terminal set with a
  conservative phase-continuation safe set;
- value minimum future kernel volume early enough to leave boundary traps;
- diagnose policy-to-policy funnel discontinuity separately from delay
  support mismatch;
- validate each dominant spell with repeated fresh focused trials before the
  next complete route.

## Transition And Auto-Confirm

The run recorded 129 in-game wall-confirm pulses and 16 terminal transition
pulses. It reached terminal unload without an auto-Z stall.

After the worker completed, the old daemon remained in its F8 polling loop and
later observed a second F8 edge. It started the separate `235835` trace during
active gameplay; F9 safely stopped it at frames `5311..8725` with no hit or
Bomb. That trace is not part of this result.

The hotkey daemon is now one-shot: after its first worker ends, it exits and
releases all injected keys before it can accept another arm.

## Trial Inventory

- `232736`: route-complete summary with 38 hits. It predates the
  operator-confirmed clean retry and is not used as this checkpoint's
  acceptance baseline.
- `234229`: external-stop partial, frames `2244..2809`; discarded.
- `234414`: complete clean trial used by this review.
- `235835`: unexpected second-arm partial, frames `5311..8725`; retained only
  for control-protocol regression.

## Retained Artifacts

- `artifacts/runtime_reports/lunatic_route2_finalb_policy_epoch_reset_20260723_234414.dossier.json`
- `artifacts/runtime_reports/lunatic_route2_finalb_policy_epoch_reset_20260723_234414.dossier.md`
- `artifacts/runtime_reports/lunatic_route2_finalb_policy_epoch_reset_20260723_234414.deaths.csv`
- `artifacts/runtime_reports/lunatic_route2_finalb_policy_epoch_reset_20260723_234414.regressions.json`
- `artifacts/runtime_reports/lunatic_route2_finalb_policy_epoch_reset_20260723_234414.comparison.json`
- `artifacts/runtime_reports/lunatic_route2_hotkey_longrun_20260723_234414.summary.json`
- `artifacts/runtime_reports/lunatic_route2_hotkey_longrun_20260723_235835.summary.json`

The 243 MB raw JSONL remains local and ignored. Its SHA-256 is
`3dd67c2cedca980a84a1f7432f308386b80817eb08d8339c6784f72fd7ed5acc`.
