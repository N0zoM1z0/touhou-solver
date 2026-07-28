# Touhou Solver

Research-grade perception, robust planning, and native input control for
*Touhou Eiyashou ~ Imperishable Night* (TH08).

This repository combines native game-state sensing, deterministic danmaku
projection, collision certification, robust finite-horizon viability, and
physical replay evidence. It is a research system, not a finished no-hit bot:
the current controller has completed a full Hard route, but Lunatic and Extra
have **not** met the physical acceptance target.

## What Is Implemented

- TH08 archive, ECL, stage, replay, bullet, laser, enemy, item, and route
  analysis tools.
- Native pool reads and packed decoding from the running 32-bit game.
- Shared native C++ hazard queries and local beam reduction, with independent
  Python/NumPy differential oracles.
- An issue-time local input-pipeline collision certificate with explicit
  active, held, pending, pickup-delay, and no-write semantics.
- A coarse robust viability planner and versioned publication path.
- Deterministic TH08-like semantic fuzzing across Normal, Hard, Lunatic, and
  beyond-native-pool densities.
- Replayable physical run dossiers, death ledgers, compact benchmark reports,
  and minimized counterexample regressions.

The latest retained evidence includes:

- one clean zero-hit Hard Stage-1 focused run;
- one complete Hard Route-2 run with 39 hits, 38 of them after global
  viability-kernel exhaustion;
- zero geometry or endpoint mismatches in a 256-case gate and a 96-case
  high-intensity semantic differential corpus; and
- rejection of both synchronous and same-issue asynchronous supplemental
  delivery after a retained deadline counterexample (CE-0131).

These observations establish implementation parity and identify the current
bottleneck. They do not prove complete shipped-game semantics, unrestricted
optimality, or physical safety.

## Current Research Direction

Local decode and geometry performance are no longer the primary limitation.
The next algorithmic gate is earlier preservation of global feasibility and
explicit behavior after the finite viable set becomes empty. Candidate
publication, supplemental continuation, and finer-grid work remain
offline/shadow-only unless their model and delivery contracts are separately
promoted.

The frozen-manager-frame input boundary (CE-0120) also remains unresolved at
the actuator-authority level: held input can continue moving the player while
`enemy_manager_frame` is frozen. It is a parallel sensing/control obligation,
not a reason to silently reinterpret wall time as a game input clock.

For the exact checkpoint and authority status, read:

- [`AGENTS.md`](AGENTS.md) — durable workspace and evidence contract;
- [`START_HERE.md`](START_HERE.md) — current handoff, commands, and next gate;
- [`STRATEGY.md`](STRATEGY.md) — live, shadow, proposed, and rejected ledger;
- [`notes/README.md`](notes/README.md) — responsibility-based evidence index;
- [`notes/COUNTEREXAMPLES.md`](notes/COUNTEREXAMPLES.md) — retained failures;
- [`notes/RESEARCH_LOG.md`](notes/RESEARCH_LOG.md) — chronological evidence.

## Requirements

Offline work:

- Python 3.11 or newer;
- NumPy;
- a C++17 compiler (`g++`) for the Linux native backend.

Windows physical integration additionally uses:

- a 64-bit MinGW-w64 C++ compiler to cross-build the native DLL;
- Windows plus WSL interop;
- a supported original TH08 executable.

The game executable is not provided. Physical-control tools inject keyboard
input and should be used only after reading the safety and live-control
sections of `AGENTS.md` and the exact route instructions in `START_HERE.md`.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt

# Linux native backend
python scripts/tools/build_native_planner.py --target linux

# Fast deterministic checkpoint
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_*.py'
```

Cross-build both native targets when the compilers are available:

```bash
python scripts/tools/build_native_planner.py --target all
```

Run the bounded semantic differential gate:

```bash
PYTHONPATH=scripts python \
  scripts/analysis/th08_semantic_differential.py \
  --profile gate --seed 0xce0132 --count 256 \
  --output /tmp/th08-semantic-gate.json
```

Physical commands and executable checks are intentionally not duplicated
here; use the verified commands in `START_HERE.md`.

## Repository Layout

- `scripts/touhou_control/` — reusable, game-neutral control and planning
  components.
- `scripts/` — TH08 adapters, parsers, models, and live orchestration.
- `scripts/analysis/` — differential, report, replay, and dossier tools.
- `scripts/benchmarks/` — explicit timing, ablation, and contention workloads.
- `scripts/tools/` — build, probe, patch, and capture entry points.
- `native/` — C++17 native planner and local-control kernels.
- `tests/` — deterministic unit, oracle, and counterexample regressions.
- `notes/` — formal contracts, reverse-engineering evidence, run notes, and
  research history.
- `artifacts/` — compact retained reports and selected reproducibility
  fixtures; large raw runtime captures remain local and ignored.

## Evidence Discipline

Every safety claim is labeled observed, inferred, or hypothesized. Python/C++
agreement proves implementation parity only. A physical policy may condition
only on information available before its decision, must preserve
controller/nature quantifiers, and must meet the immutable version and issue
deadline it claims.

Survival is a hard constraint. Bomb input is disabled by default. Generated
stress cases, offline solves, and shadow policies do not gain live action
authority without an explicit strategy-ledger promotion and retained physical
evidence.

## License And Project Status

Original source code and documentation are available under the
[MIT License](LICENSE). Third-party game data, names, and trademarks are not
licensed by this repository; see [`NOTICE.md`](NOTICE.md).

This is an independent research project and is not affiliated with or endorsed
by Team Shanghai Alice.
