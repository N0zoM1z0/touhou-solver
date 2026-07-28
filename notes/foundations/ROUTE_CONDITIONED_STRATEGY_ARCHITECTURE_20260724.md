# Route-Conditioned Strategy Above A Universal Safety Core

Status: architectural decision after the first native Boss-HP experiment.
This note distinguishes observed evidence, inference, and hypothesis.

## Decision

There is no evidence that one TH08-wide scalar weight vector, grid, horizon,
lead time, or preferred position is sufficient. There is still a reusable
solver boundary:

```text
native game mechanics and event model
    -> fresh collision / delay / viability action set
    -> game/team/stage/phase strategy profile
    -> resource-aware objective inside that set
    -> issue-time certificate for the action actually sent
```

The first and last layers are universal in semantics. Their implementation may
be native for speed and their concrete mechanics come from a game adapter.
The middle policy is allowed to be practiced and route-conditioned.

This is not permission to hide a Stage-4 spell check inside collision code.
It is permission to say explicitly that Stage 4A spell 57 has a different
event schedule, useful tube, damage response, Power requirement, and planning
lead than a Stage-5 Reisen stop/resume pattern.

## What "Backboarding" Means For An Agent

A top player's memorized route is more structured than one set of weights.
The agent analogue is a phase-conditioned policy package:

- identity: game, team, difficulty, route, stage, spell/nonspell, health
  segment, and timer/event window;
- a reference tube or set of timed waypoints, including safe entry and exit
  regions rather than one exact coordinate trace;
- known projectile births, laser activation, stop/resume/redirect events, and
  the lead time needed before each gate;
- the local horizon, global resolution, replanning cadence, and policy expiry
  that meet this phase's delivery budget;
- Power/item targets and a resource floor required for later boss phases;
- an executable player-shot/option model and a phase-completion target;
- a fallback profile and the conditions that invalidate the practiced route;
- provenance: captures, RNG/entry-state cohort, adverse examples, and last
  physical validation.

Weights may be one implementation detail inside a profile, but they cannot
replace these discrete modes and event-relative gates.

## Mathematical Boundary

Let `K_t(s)` be the fresh action set certified by native collision, delay, and
finite-horizon viability. Strategy never selects outside `K_t`.

For profile `p`, the route-level state includes:

```text
z = (stage, phase, timer, boss_hp, power, lives, bombs,
     entry_position, option/shot_state, rng_or_uncertainty)
```

The profile selects

```text
a* = argmax over a in K_t(s) of
     E[V_p(z_next, s_next)]
```

where the next profile may change at a health threshold, timeout, spell start,
enemy wave, or route transition. Power and boss HP belong in `z`; treating
them only as `w_item * item + w_damage * alignment` loses the fact that:

- a Power pickup can shorten several future phases;
- a hit loses Power and changes every later damage opportunity;
- a boss timeout and an HP clear lead to different exposure and rewards;
- damage delivered now changes future hazard duration;
- an item detour is useful only if the whole bridge remains viable.

In practice the full hybrid dynamic program is too large. The first useful
approximation is hierarchical and lexicographic:

1. fresh collision/delay/viability membership;
2. minimum delivery validity and survival margin;
3. phase-specific hard deadlines or resource floors;
4. predicted phase progress using the executable shot model;
5. safe item/Power acquisition and reference-tube tracking;
6. score/graze/positional preferences.

The order may be profile-specific after item 2, but survival membership never
is.

## Observed Boss Experiment

Two Stage-4A captures are retained:

- shadow-only:
  `lunatic_route2_stage4a_unattended_20260724_231247`;
- explicit, subsequently rejected horizontal-alignment live experiment:
  `lunatic_route2_stage4a_unattended_20260724_231637`.

The native registry observation is stable:

- registry `0x00F54CC0`, slot 0;
- Boss identity is flags2 bit index 2, concrete mask `0x4`;
- current/max/phase HP are enemy `+0x2DFC/+0x2E00/+0x2E04`;
- phase timer elapsed is `+0x2E1C`, timeout is `+0x3378`;
- all 873 shadow spell-57 samples and all 906 live samples had a stable
  manager-frame bracket and an open native damage gate.

The shadow run exposed 725 fresh viable/issue-safe decisions; horizontal
damage shadow disagreed with the baseline action 198 times. The explicit live
experiment changed 123 spell-57 decisions and improved normal player/Boss
horizontal error from a 51.50-pixel median to 25.19 pixels.

That geometric improvement did not imply more observed damage:

| Spell 57 sample | Shadow controller | Alignment live experiment |
| --- | ---: | ---: |
| HP observation interval | 2000 -> 633 | 2000 -> 835 |
| comparable game frames | 2872 | 3079 |
| observed HP/frame | 0.47597 | 0.37837 |
| Power first / median | 75 / 43 | 100 / 84 |
| normal alignment median | 51.50 px | 25.19 px |
| action changes | 0 | 123 |

The shadow capture was manually stopped at phase timer 2729/3000. The live
capture reached 2996/3000. Therefore this pair does **not** establish a phase
duration comparison. RNG, hit history, Power trajectory, and entry state are
also different, so the HP-rate difference is adverse evidence rather than a
causal estimate.

It is nevertheless enough to reject Boss-x alignment as live damage authority:
the proxy made its own metric much better without demonstrating better native
HP response, even in a run whose measured Power was higher.

## Existing Model That Should Replace The Proxy

The repository already contains the correct starting point:

- `th08_player_shot_model.py` implements default SHT cadence, source
  positions, shot movement, collision, damage, piercing behavior, and the
  shared 50-damage cap;
- `th08_option_model.py` implements route-2 focus transitions and the four
  option positions;
- decoded SHT levels provide Power-dependent shot records;
- the new Boss sensor supplies native HP response, phase threshold, timer, and
  damage gate.

The next damage experiment should simulate short-horizon shot coverage from
the actual player/option state and calibrate predicted damage against native
HP deltas. It must first run shadow and report prediction error by Power,
focus/option state, Boss motion, and spell. No new live damage authority is
retained from the alignment experiment.

## Which Current Constants Belong Where

Game mechanics, not tuneable strategy:

- native pool addresses/layouts and active flags;
- player movement increments and collision radius;
- bullet/laser phase and transform rules;
- shot/option cadence, hitboxes, damage, and caps;
- manager update ordering and phase-transition semantics.

Reusable algorithm/service settings, calibrated by hardware and uncertainty:

- worker count and packed/native representation;
- policy version/expiry rules;
- observed control-delay support;
- sensor epoch and issue-time service deadlines.

Likely profile parameters:

- local horizon 10 and terminal threat horizon 32;
- global 16-pixel/8-frame lattice and 80-frame horizon;
- corridor lookahead, lead, overlap, commit duration, and replan interval;
- reference position/tube and boundary reserve;
- Power/item floor, pickup windows, and phase-completion objective;
- pattern-specific event lookahead and uncertainty inflation.

The current code still places most of the last group in process-wide constants.
Moving them into a profile is an architectural target, not evidence that any
specific replacement values are already known.

## Calibration And Anti-Overfit Gate

A route-specific profile is expected to fit its phase; it must not fit one
accidental run:

1. learn or tune on several RNG and entry-resource states;
2. validate on held-out seeds/entries and a second physical capture;
3. retain every hit and proxy/model disagreement;
4. compare native HP, Power, phase exit, policy freshness, and hard-safety
   vectors, not only score or total hit count;
5. reject changes that improve a proxy but not its native outcome;
6. keep the universal safety/kernel tests cross-stage and adversarial.

The target is therefore a general safety and modeling engine carrying
explicitly specialized practiced strategies—not a universal weight vector,
and not a collection of unreviewable spell-name conditionals.
