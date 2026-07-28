# Stage-5 Enemy Combat-Progress Physical Gate Preparation

Date: 2026-07-28

Status: implementation accepted for one default-off physical gate; no physical
result yet

## Integration Boundary

The `--trace-enemy-combat-progress` option now propagates explicitly through:

```text
practice/full-route supervisor
  -> Windows hotkey daemon
  -> immutable long-run argument builder
  -> live controller
  -> existing first-64 enemy-prefix capture
  -> post-issue combat-progress stage
  -> synchronous JSONL trace
```

Every layer defaults to false. The option does not require or silently enable
bullet-birth tracing. It adds no process-memory call: the controller requests
combat decoding from the same first-64 `u32/read/u32` capture and receives the
same body tuple used by live safety.

The trace stage runs only after `commit_physical_issue` returns. It cannot
alter the action selected or issued in the current decision. Its synchronous
serialization may perturb the next controller cadence, so capture, decode,
record construction, stage, and previous serialization timings are explicit
evidence rather than being called side-effect-free.

## Fail-Closed Physical Schema

The physical stage requires exactly 64 scanned slots, positive capture-attempt
count, and finite non-negative capture/stage/previous-emit timings. Each row
retains raw signed values and the authority declarations from
`STAGE5_ENEMY_COMBAT_PROGRESS_OBSERVATION_CONTRACT_20260728.md`.

The stable `scripts/analysis/th08_enemy_combat_progress_audit.py` entry point
delegates to the bounded `analysis/enemy_combat_progress_audit/` schema,
streaming-report, and CLI modules. It reads the raw JSONL stream once and
independently checks:

- exact physical route/difficulty/stage identity;
- observation and inventory schema/layout;
- literal revalidated offsets and masks;
- 64-slot scope, ascending unique slots, and slot-derived pointers;
- active flag, local damage-gate expression, and defeat-mode parity;
- stable manager-frame brackets and one/two-attempt capture bounds;
- finite timings and the fixed decode/record p95/p99/max limits;
- strictly increasing decision frames inside each stage/epoch;
- at least one active row, positive frame-damage row, and adjacent active-slot
  positive-HP decrease candidate.

The last item is deliberately named a candidate. Slot continuity is not
generation identity, and neither HP reduction nor disappearance proves a
kill. The audit publishes `generation/end_reason/kill/targeting/action`
authority as `none`.

The report includes exact raw trace SHA-256 and a canonical internal digest.
Regenerating it from identical raw bytes must be byte-identical.

## Automated Evidence

- Focused Ruff passes.
- Nine combat-progress implementation/stage tests pass.
- Three strict streaming-audit tests pass, including deterministic
  regeneration, pointer/schema rejection, and a retained timing-gate miss.
- CLI/argument/supervisor focused tests prove the option is independently
  default-off and explicitly propagated.
- Complete Linux discovery passes 972 tests in 11.319 seconds.
- Complete Windows discovery passes 972 tests in 18.037 seconds with the
  three existing platform skips.

## Authorized Physical Command

Use the existing non-TTY supervised Lunatic Stage-5 practice launch:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat' \
  --stage 5 --trace-enemy-combat-progress \
  --status-seconds 15 --stall-timeout 120
```

After accepted supervisor completion, audit the exact raw trace:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/th08_enemy_combat_progress_audit.py \
  TRACE.jsonl REPORT.json \
  --route-id 2 --difficulty-index 3 --stage-route-index 5
```

Do not combine this first gate with bullet-birth, auxiliary-VM, runtime-ECL,
viability, or targeting experiments. Hard no-Bomb, foreground/identity
checks, automatic transition acceptance, exact cleanup, compact retained
evidence, and two-newest-compatible raw-bundle retention remain mandatory.

## Promotion Rule

A passing audit accepts only default-off physical combat-progress observation.
It does not accept S18 targeting. A separate generation/end tracker and
streaming exposure audit must be contracted before comparing fast-kill
strategies, Power collection, boss alignment, or survival outcomes.

The authorized run and audit passed on 2026-07-28. The bounded result and
remaining authority exclusions are retained in
`STAGE5_ENEMY_COMBAT_PROGRESS_STAGE5_RESULT_20260728.md`.
