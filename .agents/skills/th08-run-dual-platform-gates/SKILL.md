---
name: th08-run-dual-platform-gates
description: Run focused or complete TH08 test, native, differential, and report-integrity gates on Linux and Windows. Use after changes to Windows process/input/parser code, native kernels, formal recurrences, retained-report tooling, or before physical promotion. Never run Linux and Windows performance gates concurrently.
---

# Run TH08 Dual-Platform Gates

Validate the affected contract on both consuming platforms while preserving
timing integrity and the independent Python-oracle boundary.

## Select The Smallest Gate

1. Read `AGENTS.md`, `START_HERE.md`, and the changed contract.
2. Inspect the diff and choose focused tests first. Run the complete quick
   discovery suite before a code checkpoint.
3. Run expensive capsule, unrestricted, long-horizon, RSS, broad trace, or
   performance profiles only when their recurrence/kernel changed or the
   result will be retained.
4. Rebuild only affected native targets. Do not commit native build output.

## Execute Without Cross-Contamination

1. Run Linux tests through `unittest discover` with `PYTHONPATH=scripts`, as
   required by `AGENTS.md`.
2. Wait for Linux performance-sensitive work to finish before starting the
   Windows gate.
3. Use the exact verified UNC loader in `START_HERE.md`. Change only its test
   pattern or explicitly documented workload argument.
4. Never execute Linux and Windows performance gates concurrently. Treat a
   concurrent result as contaminated and rerun the failing timing gate alone.
5. Run Windows tests for Windows/process/input/parser/native changes and
   before physical promotion. Do not probe Windows during live gameplay.

## Preserve Authority

1. Keep the formal Python scalar oracle independent of the C++
   implementation it checks.
2. Compare Python/C++ behavior, immutable report bytes/hashes, fail-closed
   cases, and declared adversarial capsules where relevant.
3. Treat parity as implementation evidence only. Never present parity or a
   benchmark pass as physical-model validity or survival authority.
4. Report exact platform, command/profile, test count, duration, skips,
   affected native build, report digests, and whether each timing included
   decoding, lowering, packing, induction, or publication.
5. Preserve failures and counterexamples. Do not weaken a gate or erase a
   fixture to make the suite pass.
