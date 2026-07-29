# Lunatic Route-2 Stage-5 SEM-MODE-B Attempt 035718

Date: 2026-07-30  
Status: failed before first decision; CE-0191  
Repository checkpoint: `c814b09`  
Physical code checkpoint: `31f92eb`

## Scope And Provenance

- Original-game Practice Start, Lunatic, Sakuya/Remilia, Stage 5.
- Shipped executable SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`.
- No-life-decrement patch at `0x0044D0FA` observed as `0x00`.
- `--trace-enemy-mode-transitions` enabled from stage entry.
- Hard no-Bomb and `stop-after-hits=0`.

## Observed Result

The native menu trace reached Stage-5 cursor 5 and the agent entered gameplay.
At frame 1 it observed unit root scale with root-only future coverage, emitted
`time_scale_authority_unknown`, and selected the default
`terminate_and_release_keys` fallback. No decision record exists. The summary
has zero hits and zero Bombs only because no controlled interval occurred.
This is not a physical mode-transition or survival sample.

## Evidence

- Local ignored raw JSONL:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260730_035718.jsonl`,
  five rows, SHA-256
  `da31073f043a6a615830d3410769174993ce30273becf44e1c1648117f0e5dad`.
- Retained session:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260730_035718.session.json`,
  SHA-256
  `560cce7dd93dea844c84bf673f4aa8ad5988c408d806fac6b42652d6b2083e24`.
- Local ignored launch log SHA-256:
  `5a5017ec9d40869ed392505fc6c77727feb8b8626e55ae80dbca805400a6f736`.

## Cleanup And Authority

Supervisor cleanup released injected keys. Read-only process checks found no
remaining TH08, controller, supervisor, or helper. The attempt establishes
only that the default hard scale fail-close prevents this whole-stage
diagnostic workload. It grants no survival, planner, or SEM-MODE transition
authority.
