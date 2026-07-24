# TH08 Final B No-Bomb Practice: 2026-07-24 08:19

## Scope

- Original `th08.exe`, Lunatic Practice Start, Sakuya/Remilia, Stage 6B.
- Automated native-state menu selection and hard no-Bomb agent.
- Complete route scope: frames `2..75091`, 14,484 decisions.
- Termination: `route_complete`; automatic no-save exit and process cleanup.
- Native hit edges: 18.
- Raw trace remains ignored; compact dossier, comparison, session, deaths, and
  regressions artifacts are retained.

## Lifecycle Gate

- The immediately preceding run `081231` aborted at frame 22,801 with
  `KeyError('stay')` after a boundary-constrained beam fell back outside its
  certificate action domain.
- The corrected run crossed frame 22,801, completed all of Final B, emitted
  no Bomb bit/action, and required no manual dialogue or save-menu input.
- Linux passed 307 tests; focused Windows boundary, terminal-threat, and
  shared-laser tests passed before launch.

## Comparison

- Versus the most recent complete Stage-6B baseline `060039`, hits changed
  `30 -> 18`.
- Spell 150 changed `4 -> 0`; spell 154 `5 -> 1`; spell 158 `2 -> 1`;
  spell 166 `5 -> 3`; spells 174/178 each `1 -> 0`.
- Spell 162 regressed `1 -> 2`; spell 170 regressed `5 -> 6`; spell 186
  remained `1`.
- Dense spell-154 global solve median/p95 improved
  `936/1345 -> 246/346 ms`; all-stage solve median/p95 improved
  `284/462 -> 246/389 ms`.
- This comparison spans several accepted solver and laser changes and is not
  an isolated survival attribution for the boundary-clamp correction.

## Failure Boundary

- All 18 hit windows were classified
  `global_viability_kernel_exhausted_before_hit`.
- Contact classes: 9 modeled committed-prefix collisions, 5 observed bullet
  overlaps, 3 observed laser overlaps, and 1 sensor gap/unmodeled hazard.
- Twelve hits carried `playfield_boundary`; pre-hit bottom-eight-pixel
  occupancy rose from `0.304` to `0.517`.
- Spell 170 contributed six hits with no lasers. Its empty-kernel recovery
  repeatedly selected actions while the player remained at the bottom edge.
- The next correction must make empty-kernel recovery path-aware and
  boundary-controllable. A stage/spell steering rule is not acceptable.
