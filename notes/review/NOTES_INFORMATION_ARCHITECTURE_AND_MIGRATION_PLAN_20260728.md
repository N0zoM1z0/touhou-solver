# Notes Information Architecture And Migration Plan

Date: 2026-07-28

Status: accepted repository-maintenance plan; no model or action-authority
change

## Problem

The repository's evidence is durable, but its current storage topology makes
routine orientation unnecessarily expensive:

- 226 tracked Markdown files occupy 3,475,069 bytes;
- 92 files are directly under `notes/`;
- 132 physical run reviews are already isolated under `notes/runs/`;
- two external-review documents are under `notes/review/`;
- `notes/RESEARCH_LOG.md` alone is 515,082 bytes and 8,462 lines after the
  latest checkpoint; and
- `notes/COUNTEREXAMPLES.md` is 311,238 bytes, 5,060 lines, and 165 durable
  counterexamples.

The two ledgers account for about 826 KiB before an agent reads any active
formal contract. They are valuable evidence and must not be summarized away,
but reading either monolith to locate one recent checkpoint wastes context and
encourages stale handoffs.

There are 14 tracked inbound references to `RESEARCH_LOG.md` across seven
files and 12 references to `COUNTEREXAMPLES.md` across nine files. No tracked
reference uses a Markdown anchor into either ledger. This makes stable
entrypoint indexes plus shards possible without breaking anchor targets.

## Source-Of-Truth Invariants

1. `START_HERE.md` remains the short volatile handoff.
2. `STRATEGY.md` remains the live/shadow/proposed/rejected ledger.
3. `notes/RESEARCH_LOG.md` and `notes/COUNTEREXAMPLES.md` remain stable
   canonical entrypoints.
4. Historical prose, ordering, evidence labels, hashes, failures, and
   authority boundaries are not rewritten during migration.
5. The daily research-log shards and counterexample-range shards become the
   authoritative historical bodies named by the canonical indexes.
6. The current append target is explicit in each canonical index and in
   `AGENTS.md`; new evidence must not make the index monolithic again.
7. Formal notes named by `START_HERE.md` are moved only with an atomic
   repository-wide literal-link rewrite and missing-link validation.
8. Raw runtime evidence, ignored `audits/`, and unrelated user files are out
   of scope.

## Target Topology

```text
notes/
  README.md                         short topology and routing index
  RESEARCH_LOG.md                   stable chronological index
  COUNTEREXAMPLES.md                stable CE-range index and entry template
  research_log/
    2026-07-22.md
    ...
    2026-07-28.md                   current append target
  counterexamples/
    CE-0001-0049.md
    CE-0050-0099.md
    CE-0100-0139.md
    CE-0140-0165.md                 current range
  research/
    g5/                             future-hazard/ECL G5 contracts and results
    stage5_combat/                  combat-progress contracts and results
  architecture/                     refactor and maintenance evidence
  operations/                       practice and unattended-run protocols
  runs/                             compact physical run reviews
  review/                           external/consolidated review documents
```

The active general control formalizations remain at their existing root
paths in this migration. They are named directly by the workspace contract,
form the current authority chain, and do not dominate the root count. A later
formal-contract migration should be proposed only if the stable-link rewrite
and human navigation benefit justify that extra churn.

## Sharding Boundaries

### Research log

The chronological body is split by the date written in each heading:

| Shard | Original inclusive lines |
| --- | ---: |
| `2026-07-22.md` | 3..769 |
| `2026-07-23.md` | 770..1331 |
| `2026-07-24.md` | 1332..2572 |
| `2026-07-25.md` | 2573..3095 |
| `2026-07-26.md` | 3096..4042 |
| `2026-07-27.md` | 4043..6111 |
| `2026-07-28.md` | 6112..end |

The legacy G2 section begins as an H2 on July 27 and continues with dated H3
entries on July 28. The July-28 shard receives a local wrapper heading, while
the original body from line 6112 onward remains byte-preserved between
explicit source-content markers.

### Counterexamples

The durable failures are split on existing CE headings:

| Shard | First original line | Entries |
| --- | ---: | ---: |
| `CE-0001-0049.md` | 21 | 49 |
| `CE-0050-0099.md` | 992 | 50 |
| `CE-0100-0139.md` | 2458 | 40 |
| `CE-0140-0165.md` | 3849 | 26 |

The entry template stays in the canonical index. New failures append to the
current range until a 50-entry boundary is reached.

## File Classification Boundary

This checkpoint moves only clear responsibility families:

- every `G5_*.md` note to `notes/research/g5/`;
- the five `STAGE5_*COMBAT*.md` notes to
  `notes/research/stage5_combat/`;
- explicit refactor/maintenance notes to `notes/architecture/`; and
- practice/automation protocols to `notes/operations/`.

Mixed or foundational formal notes remain in place. This reduces root clutter
without hiding the current authority chain behind a speculative taxonomy.
Future notes use the closest responsibility directory instead of returning to
the flat root.

## Mechanical Validation Gates

Before committing the migration:

1. reconstruct both legacy monolith bodies from the shards and compare their
   SHA-256 values to the pre-migration blobs:
   - research log:
     `432cbdc7e75661776574bffe165869c3534bfe4cfdfb51da57f78e7bf208c0ab`;
   - counterexamples:
     `2267928c8b59e4704dfb1cd7c7219d4ee42f2d12f50677c333ec23231fe1cab0`;
2. verify every moved file is represented as a Git rename;
3. scan every tracked Markdown literal path and reject missing targets;
4. require zero stale references to moved paths;
5. require all 165 CE headings exactly once and all dated research headings
   exactly once across shards;
6. run `git diff --check`; and
7. keep the migration documentation-only, with no Python/C++/planner/native
   semantic changes.

## Acceptance And Follow-Up

The migration is accepted when historical content is reconstructable,
canonical indexes route a new agent to the current shard, links resolve, and
the root note count falls materially. It does not change any strategy status
or evidence authority.

Afterward, resume the roadmap at the next narrow live-session/controller seam
and the separately contracted auxiliary ECL event class. Notes organization
must not become an excuse for a big-bang rewrite of either code or research
semantics.
