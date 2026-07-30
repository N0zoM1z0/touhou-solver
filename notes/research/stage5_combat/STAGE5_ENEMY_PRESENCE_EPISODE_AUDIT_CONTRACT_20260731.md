# Stage-5 Enemy Presence-Episode Audit Contract

Date: 2026-07-31

Taskbook card: `COMBAT-KILL-01`

Status: offline audit of retained evidence; no kill or action authority

## Task Card

Question: how much generation and end-reason authority can the accepted
2026-07-28 Stage-5 combat-progress trace support without inventing native
events that were not captured?

Hypothesis: contiguous active-slot observations can recover bounded presence
episodes and end windows, but the post-update active-only observer cannot
verify ordinary mode-0 kills because the native health-defeat path clears the
active bit in the same manager update.

Earliest decision effect: none. This is a retrospective audit of an existing
trace. It does not rank or issue actions.

Win condition:

- every observation is schema- and identity-checked in one deterministic
  pass;
- active-slot absence/presence transitions produce explicit left/right
  censoring and bounded start/end windows;
- native generation, verified kill, timeout, scripted despawn, transition,
  and unknown remain separate authority classes;
- damage-adjacent disappearances are retained as candidates, never relabeled
  as kills; and
- the next capture contract is precise enough to falsify a kill claim.

Reject or defer: if the old trace cannot observe an end edge, the audit must
return `UNKNOWN` and continue to another WS-H task instead of requesting an
unchanged physical replay or treating an HP decrease as a kill.

Out of scope: target selection, bullet ownership, drops, prevented births,
Power policy, a native snapshot/game run, and live combat ranking.

## Evidence Boundary

The input is the accepted ignored raw trace
`artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260728_224116.jsonl`,
SHA-256
`569a8767e25806661acf9b66365cdf227189d53bb525a906d913cd08fe61d8bb`.
Its tracked v1 audit already grants trace-only HP/damage observation and
explicitly grants no generation, end-reason, kill, targeting, or action
authority.

Observed native dataflow revalidated in `enemy_manager_update`
(`0x0042C660`):

- resolved player-shot damage is subtracted from current HP at
  `0x0042D349`;
- HP `<= 0`, unless explicitly deferred, enters defeat processing in the same
  manager update;
- defeat mode 0 clears active flag bit 0 at `0x0042D899`;
- main-ECL completion and offscreen cleanup can also clear active bit 0
  through a different path while HP remains positive; and
- the existing observer retains only slots whose active bit is still set.

Therefore a post-update active-only row cannot witness the ordinary mode-0
HP-defeat edge. An absent slot after a positive-HP observation is compatible
with a later kill, timeout/script end, offscreen cleanup, transition, or
unobserved reuse.

## Finite Audit State

One audit state is keyed by `(stage_route_index, gameplay_epoch, slot)` and
contains:

- an observation-presence ordinal, which is not a native generation ID;
- first and last observed decision frames;
- left-censored status and the bounded start window after an observed absence;
- initial, minimum, and last observed HP;
- count of observed positive frame-damage rows and adjacent HP decreases;
- last damageability gate, defeat mode, and flags; and
- a right-censored marker or bounded disappearance window.

Rows remain in the same observation episode only across consecutive retained
observations in which the slot is active. A decision-frame gap does not prove
that the native allocation remained alive; it is retained as an uncertainty
width. Epoch boundaries right-censor every open episode.

## Classification

The v1 trace supports these labels:

- `observation_presence_episode`: exact only for the retained row sequence;
- `damage_adjacent_disappearance_candidate`: the last retained active row has
  positive frame damage before a later absence; and
- `unobserved_end_reason`: every disappearance without a same-update native
  end record.

It does not support `verified_kill`, `timeout`, `scripted_despawn`,
`transition`, or native generation identity.

## Authority Answers

1. Histories merge only by epoch, slot, and uninterrupted retained active-row
   presence. They are not declared native-generation-equivalent across
   observation gaps.
2. The audit has no controller/nature recurrence. It enumerates every
   retained observation in chronological order and preserves every gap.
3. Exact solution answers only which presence episodes and windows the trace
   contains. It does not answer why an enemy ended or whether killing it
   prevented a volley.
4. The algorithm is exact for the declared observation projection. A trace
   with a non-increasing frame, inconsistent schema/identity, or impossible
   slot row falsifies acceptance. Any end-reason label beyond the captured
   fields falsifies the authority boundary.
5. There is no issue-time consumer. The output is an offline negative gate
   for future experiment design.

## Retained Result

The deterministic one-pass audit of the immutable Stage-5 trace retains:

- 11,735 stable observations and 133,070 active rows;
- 1,823 observation-presence episodes, of which 1,789 end before a later
  observed absence and 34 are right-censored;
- positive last-observed HP and defeat mode 0 for all 1,789 ended episodes;
- 17 damage-adjacent disappearance candidates, all with unknown end reason;
  and
- zero verified kills, timeouts, scripted despawns, or transitions.

One disappearance window is 1,802 decision frames wide; even the 54
single-frame windows have no same-update clear-path record and therefore no
kill authority. The compact report is
`artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260728_224116.presence_episode_audit.json`,
SHA-256
`d483268f3e69443a5d36ace92b71e8da165f87b59e45d761bcdb99fcb2865162`.
Independent regeneration is byte-identical.

This rejects the old trace as a `COMBAT-KILL-01` kill-policy gate. It does not
reject the kill-before-saturation hypothesis itself.

## Required Next Capture

A future `COMBAT-KILL-01` root/capture must retain a same-update end event
before slot reuse, including:

- slot plus an allocation/generation identity or a proven one-update root;
- HP before damage, resolved damage, HP after damage, damage source class,
  active flag before/after, and defeat mode;
- which native path cleared or retained active state: HP defeat, main-ECL
  completion, offscreen cleanup, timeout/health transition, or other;
- current main/aux ECL program state and the end-subroutine/transition fields;
- drop/item spawn records and RNG identity; and
- source-linked hostile births before and after the end edge.

Only a same-root branch with that event plus exact survival can test whether
earlier verified kill prevents later emissions.
