# TH08 Counterexample Ledger

This ledger preserves failures that changed the reverse-engineering model or
the live agent. A row is not complete until it points to reproducible evidence
or states exactly what evidence is still missing.

## Entry Template

```text
ID / date:
Observed symptom:
Invalid assumption:
Evidence or trace:
Root-cause class: world model | sensing/latency | planner | objective/resource | control/runtime
Correction:
Regression test:
Live verification:
Status: observed | inferred | unknown | fixed
```

## Ledger Routing

Historical entries are preserved verbatim in range shards. Append a new
counterexample to the current range, presently
[`counterexamples/CE-0170-0219.md`](counterexamples/CE-0170-0219.md), and add a
new 50-entry range when the current range reaches its boundary. Do not append
CE bodies to this index.

| Range | Entries |
| --- | ---: |
| [CE-0001–CE-0049](counterexamples/CE-0001-0049.md) | 49 |
| [CE-0050–CE-0099](counterexamples/CE-0050-0099.md) | 50 |
| [CE-0100–CE-0139](counterexamples/CE-0100-0139.md) | 40 |
| [CE-0140–CE-0169](counterexamples/CE-0140-0165.md) | 30 |
| [CE-0170–CE-0219](counterexamples/CE-0170-0219.md) | 4 |

The pre-shard file had SHA-256
`2267928c8b59e4704dfb1cd7c7219d4ee42f2d12f50677c333ec23231fe1cab0`.
Concatenating this file's original first 20 lines with the payload between
each shard's `LEGACY-CONTENT-START` and `LEGACY-CONTENT-END` markers in range
order reconstructs that blob exactly. New entries follow the end marker in
the current range. Use
[`RESEARCH_LOG.md`](RESEARCH_LOG.md) for chronological evidence and this
ledger for durable falsifiers and failures.
