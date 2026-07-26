# Public Release And Test-Suite Audit

Date: 2026-07-27

## Scope

Prepare the existing repository for public release as `touhou-solver` without
copying the workspace or rewriting its history. The user explicitly chose to
retain currently tracked history and research fixtures. This checkpoint
changes future ignore behavior only; it does not claim that ignored paths were
removed from earlier commits.

## Documentation Decision

- Replaced the private-workspace README with a public project overview,
  research status, requirements, quick start, evidence boundary, license, and
  non-affiliation notice.
- Added the MIT License for original project code/documentation and a separate
  notice that third-party game material is outside that license.
- Reduced `AGENTS.md` to durable rules and moved volatile menu/checkpoint
  details to `START_HERE.md`.
- Reconciled `START_HERE.md` and `STRATEGY.md` around one primary algorithmic
  direction: preserve global feasibility and define certified post-loss
  behavior. CE-0120 remains a parallel shadow actuator-boundary obligation.
- Marked both synchronous and same-issue exact-version asynchronous
  supplemental delivery rejected by the fixed Windows gate and CE-0131.
- Kept detailed historical measurements in their design notes,
  `notes/RESEARCH_LOG.md`, `notes/COUNTEREXAMPLES.md`, and run dossiers rather
  than repeating them in the handoff and ledger.

## Ignore Decision

Added future ignores for local environments/tool caches, coverage/profiling
output, crash dumps, raw decoded/extracted output, native builds, and the
local top-level `image.png`. Existing tracked decoded/extracted fixtures
remain tracked because `.gitignore` does not and should not rewrite history.
Compact evidence, shrunk counterexamples, and run summaries remain eligible
for tracking.

## Test-Suite Decision

The audit used the repository rule that tests should protect a concrete
failure, artifact, semantic contract, or authority boundary.

Removed:

- the benchmark width-string parser and display-name formatting test; it
  protected CLI/schema plumbing rather than the supplemental hard contract.

Consolidated without reducing assertions:

- three shadow opt-in wiring tests into one table-driven test in each of the
  hotkey and practice supervisor entry points;
- three native-default/Python-or-NumPy-rollback wiring tests into one
  table-driven test in each entry point.

Retained:

- both entry points' independent wiring coverage;
- Normal/Hard/Lunatic difficulty and practice-stage selection behavior;
- componentwise hard nonregression, issue transaction, deadlines,
  cancellation, version identity, native/Python differential parity, semantic
  replay/shrinking, and every retained counterexample regression.

The test-method count therefore decreases from 593 to 584 without removing an
observed model or safety assertion. Both native targets rebuilt successfully.
The complete quick suite passed `584/584` on Linux in `5.213 s` and Windows
in `14.365 s`.

## Public Automation

Added one bounded GitHub Actions workflow for Python 3.11 and 3.13. It installs
the single declared dependency, builds the Linux C++17 backend, and runs the
same deterministic quick suite required before local checkpoints. It does not
run physical control, Windows injection, broad corpora, or expensive formal
profiles.
