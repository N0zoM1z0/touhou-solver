# Unattended Original-Game Practice Automation

Date: 2026-07-24

## Scope

`scripts/th08_practice_supervisor.py` automates the original TH08 Practice
Start flow without thprac:

1. Enable and verify Caps Lock.
2. Terminate only an identity-verified stale TH08 process.
3. Start `run_th08_no_life_decrement_attach.bat`.
4. Verify the exact executable SHA-256 and runtime patch byte.
5. Acquire the TH08 foreground window.
6. Select the fourth main-menu entry, accept the default Lunatic difficulty,
   move right twice to accept the third Sakuya/Remilia team, and move to the
   requested stage.
7. Start the prewarmed no-Bomb agent before sending the final stage confirm.
8. Monitor progress, move the completed-stage save prompt right to "do not
   save", terminate the verified game process, materialize compact practice
   artifacts, and optionally repeat.

Screenshots are not a gameplay sensor. The menu sequence is a bounded bootstrap
action from a fresh process. After final confirm, the agent fails closed unless
native state reports difficulty 3, route 2, and the requested stage-route
index.

## Stage Mapping

| CLI | Menu row | Native stage-route index |
| --- | ---: | ---: |
| `1` | 1 | 0 |
| `2` | 2 | 1 |
| `3` | 3 | 2 |
| `4a` | 4 | 3 |
| `4b` | 5 | 4 |
| `5` | 6 | 5 |
| `6a` | 7 | 6 |
| `6b` | 8 | 7 |

The selected practice stage is configured as terminal for this trial. Its first
stable scene unload ends capture without sending terminal-menu confirm pulses.
Normal cross-stage runs retain the existing route successor map.

## Commands

From a Windows console:

```bat
\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat --stage 3
```

Repeat a stage five times:

```bat
\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat --stage 6b --repeat 5
```

Continuous same-build regression:

```bat
\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat --stage 4a --forever
```

`Ctrl+C` stops the supervisor. The cleanup path requests an agent stop,
releases every injected gameplay key, and terminates only the verified TH08
image. `--leave-game-running` disables the final game termination.

The wrapper uses the Windows Store Python alias under `%LOCALAPPDATA%`, whose
installed environment contains `numpy`. The IDA 9.3 Python used by the patch
BAT does not contain the planner dependencies and is intentionally limited to
the small runtime patcher.

## Artifacts

Each attempt writes:

- raw ignored JSONL and launch log under `artifacts/runtime_reports/`;
- tracked session manifest and raw summary;
- dossier JSON/Markdown, death CSV, and executable regression cases;
- comparison JSON when an earlier unattended run exists for the same stage;
- a human-readable copy under `notes/runs/`.

Failed bootstrap attempts still write a session manifest containing the menu
plan, target identity if available, and exact exception. They must not be used
as gameplay acceptance evidence.

The first armed bootstrap `20260724_005845` is such a rejected attempt:
`cmd.exe /S /C` nested the quoted BAT path and never launched TH08. CE-0051
records the corrected separate-argv invocation.

The next bootstrap `20260724_010112` exposed that a fresh team menu starts on
its first entry, not Sakuya/Remilia. Native analysis then established that the
team menu uses Left/Right, so the corrected sequence is `Right`, `Right`, `Z`.

The title flow is now synchronized against native manager modes `0 -> 8 -> 9
-> 11` and the live title cursor. `g_difficulty_index` and
`g_stage_route_index` are intentionally not used before the final stage `Z`:
the native Practice-stage handler commits both only during that final input.
The gameplay agent validates difficulty, route, and stage immediately after
the transition.

Completed Stage-1 acceptance run `20260724_011933` covered frames `2..21008`,
reported `route_complete`, retained four hit windows, and passed the hard
no-Bomb audit across 6,306 decisions.

## Current Evidence Boundary

The corrected team selection, final confirm, auto-dialogue progression,
terminal unload, artifact generation, and verified process cleanup have passed
one complete Stage-1 physical trial. Other stage rows and repeated/forever
recycling still require physical coverage.
