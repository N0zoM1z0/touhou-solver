# TH08 Launch And UNC Workflow Audit

Date: 2026-07-29

Status: current-machine one-shot paths verified; no gameplay launched

## Scope

This audit covers:

- Linux and Windows test entry points;
- Windows UNC Python imports;
- native build entry points;
- repo practice/full-route BAT wrappers;
- the external game launch/patch BAT;
- immutable Stage-5 ECL argument transport;
- ready, monitor, failure, and cleanup boundaries.

The audit used help, import, parser, hash, and focused unit checks only. It did
not start a new physical trial.

## Findings And Corrections

### Repo BAT wrappers

Both wrappers use WindowsApps Python and verify `numpy` before importing the
supervisor. They now derive the supervisor from `%~dp0`:

- `run_th08_practice_agent.bat`;
- `run_th08_full_route_agent.bat`.

This removes the hard-coded repository UNC root while preserving quoted
script execution and `%*` argument forwarding. Calling both BATs through the
documented WSL-to-`cmd.exe` boundary with `--help` succeeded. `cmd.exe` prints
its normal warning that a UNC current directory is unsupported and then uses
the Windows directory; `%~dp0` still resolves the BAT and supervisor exactly.
The warning is not a retry or failure.

### Immutable ECL preflight

Attempt `20260729_125411` proved that a malformed shell argument could reach
the child agent only after game launch and menu navigation. The supervisor
now performs, before terminating or launching any game process:

1. path/hash pair validation;
2. strict path resolution and readability;
3. regular-file validation; and
4. exact SHA-256 comparison.

The actual Windows UNC file
`artifacts\decoded\ecldata5.ecl` resolved successfully under WindowsApps
Python and matched
`3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`.

### Direct Windows tools

`scripts/tools/audit_raw_capture_bundle.py` and
`scripts/tools/th08_boss_probe.py` imported repository modules without
prepending their parent `scripts/` directory. Both now use the same direct-UNC
bootstrap as the other Windows tools. Safe Windows `runpy` imports passed.

### External game BAT

The current file exists at:

`D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)\run_th08_no_life_decrement_attach.bat`

It launches `th08.exe`, then calls the current repo patcher at
`scripts\tools\th08_attach_no_life_decrement.py`. Its IDA Python is acceptable
for this dependency-light patcher only; a safe import under that interpreter
passed. Supervisors must continue to use WindowsApps Python with `numpy`.

The external BAT is machine-specific and outside Git. If the WSL
distribution or repo path moves, update its patcher UNC path in the same
checkpoint. Its `pause` leaves the batch shell waiting, but supervisor
`finally` cleanup terminates that exact batch process; it is not supervisor
completion.

## Canonical Commands

### Linux quick suite

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

### Windows UNC quick suite

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe -c \
  'import sys,unittest; root=r"\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08"; sys.path.insert(0,root+r"\scripts"); tests=root+r"\tests"; suite=unittest.TestLoader().discover(tests,pattern="test_*.py",top_level_dir=tests); result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(0 if result.wasSuccessful() else 1)'
```

Change only the pattern for a focused run. Do not use UNC `cmd.exe` `cd`,
`pushd`, ordinary `unittest -s <UNC>`, or a PowerShell-only drive mapping as
an import root.

### Ordinary Lunatic Stage-5 control

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat' \
  --stage 5 --status-seconds 15 --stall-timeout 120
```

This is the next survival-control command. It enables no optional observer.

### Exact V6 reproduction only

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat' \
  --stage 5 --status-seconds 15 --stall-timeout 120 \
  --trace-auxiliary-vm-batches --trace-auxiliary-ecl-events \
  --auxiliary-vm-batch-every 16 --auxiliary-vm-batch-spell-id 107 \
  --auxiliary-vm-native-call-mode gil-held \
  --runtime-ecl-static-image \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\artifacts\decoded\ecldata5.ecl' \
  --runtime-ecl-static-sha256 \
  3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19
```

The UNC values are single-quoted for the WSL shell. Do not construct a
backslash path inside unescaped double quotes. V6 remains failed; use this
only to reproduce its fixed contract after reading the result note.

### Complete Lunatic Route 2

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_full_route_agent.bat' \
  --difficulty lunatic --status-seconds 30 --stall-timeout 120
```

Do not use `--leave-game-running` unless an accepted run must remain for
manual replay save and the agent will stay present.

## Verified Checks

- Linux supervisor/agent focused tests: `27 + 7 + 16`, pass.
- Windows UNC supervisor tests: 34, pass.
- Windows UNC agent-contract tests: 16, pass.
- Ruff on changed launcher/tool paths: pass.
- Practice and full-route BAT `--help` via actual `cmd.exe`: pass.
- WindowsApps direct imports of both corrected tools: pass.
- IDA-Python direct import of the external patcher: pass.
- Actual immutable ECL UNC resolution and SHA-256 preflight: pass.
- Native build-tool `--help` for planner and bullet-birth trace: pass.

- Complete Linux discovery after the launch correction: 1,055 tests in
  14.423 seconds, pass.
- A simultaneous Linux/Windows complete run made the existing Windows
  auxiliary-event benchmark timing gate fail. Its isolated focused rerun
  passed. Do not run platform performance gates concurrently.
- Final isolated Windows UNC discovery after the launch correction: 1,055
  tests in 29.477 seconds, pass with three existing skips.

The launch-only code checkpoint is `d85cca1`. It has no physical survival
authority; the latest physical run remains checkpoint `3f02ff1`.

## Operational Acceptance

The documented current-machine commands are now one-shot at the software
boundary. Physical launch can still fail closed for real external conditions:
wrong foreground, unexpected menu state, executable/hash mismatch, missing
patch, game crash, or Windows focus loss. Such a failure is evidence to
retain, not a reason to repeat blindly.
