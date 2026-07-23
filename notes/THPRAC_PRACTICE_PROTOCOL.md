# THPRAC Stage-Practice Protocol

## Purpose

THPRAC is the fast counterexample loop. It isolates one Lunatic stage or spell
without replaying all earlier resources. The original no-life-decrement route
remains the final integration test for cross-stage position, item, Bomb, Power,
and route feasibility.

## Handoff

1. Codex starts the exact TH08 executable through
   `run_th08_no_life_decrement_attach.bat` and verifies its SHA-256 and patch
   byte.
2. The operator starts `thprac.v2.1.3.0.exe`, selects Lunatic,
   Sakuya/Remilia, and the desired stage or checkpoint.
3. After practice gameplay begins, the operator presses F8 once.
4. The prewarmed daemon validates active route 2 and difficulty 3, then starts
   a timestamped trace under `artifacts/runtime_reports/`.
5. Stop with F9 when the selected scope ends. Do not merge separate practice
   attempts into one route score.

## No-Bomb Diagnostic Policy

F8 practice and long-run traces use `--no-bomb`. This forbids both proactive
Bomb and deathbomb input. Every trace begins with:

```json
{"kind": "controller_config", "bomb_policy": "disabled"}
```

The live controller also checks the final action mask and fails closed if bit
`0x02` appears. This removes Bomb invulnerability, cancellation, timing, and
resource effects from planner diagnosis.

The first native hit in each fresh practice attempt is the canonical causal
counterexample. Death/respawn changes position, clears bullets, and alters
later state even when the no-life-decrement patch preserves stock. Later hits
remain useful for discovery but are not equivalent independent trials.

## Acceptance Layers

- **Checkpoint:** repeatable no-Bomb survival of the selected wave or spell.
- **Stage:** no-Bomb completion from that stage's practice start.
- **Route:** original-game Lunatic Final-B run with finite resource accounting.
- **Final:** repeat the same process for Extra, then validate executable input
  playback rather than accepting only an offline plan.

