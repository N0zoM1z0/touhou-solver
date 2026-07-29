# Live Reporting And Handoff

Use this reference to write the audit continuously, make each finding
actionable, and leave a report another agent can verify without hidden context.

## Contents

1. Start the report immediately
2. Finding structure
3. Positive validation and performance structure
4. Executive summary and priority
5. Consolidated IDA and verification backlogs
6. Final consistency pass
7. Handoff template

## 1. Start The Report Immediately

Create the requested report before deep analysis. Use this initial skeleton:

```markdown
# TH08 IDA / Native-To-Solver Read-Only Audit (In Progress)

Date:
Workspace:
Branch/HEAD:
Connected IDB identity:
Executable identity:
Latest retained evidence cutoff:
Scope:
Non-actions:

## Evidence Labels

- Observed:
- Inferred:
- Hypothesized:

## Live Summary

## Pending Checks
```

Write findings as soon as evidence is sufficient. Revise an earlier finding
when later evidence narrows it. Do not keep a separate hidden conclusion that
never reaches the file.

## 2. Use A Complete Finding Record

Use:

```markdown
## F-### — Short, mechanical title

Severity:
Status:
Reachability:
Authority boundary:

Native evidence:

- address/instructions;
- producer/consumer/order;
- state and numeric semantics.

Solver evidence:

- decoder/model/projection/ABI/planner path;
- exact omission or mismatch.

Direction:

- conservative / optimistic / mixed / unknown;
- what it can and cannot prove.

Minimal reproduction or retained witness:

Impact:

Recommended correction:

Verification gate:

IDA/catalog recommendation:
```

Include exact file/symbol/address names, but avoid copying large pseudocode
blocks when a short formula or branch description is enough.

Separate:

- implementation defect;
- misleading name/comment/type;
- missing model information;
- missing runtime evidence;
- performance opportunity.

## 3. Record Revalidations And Performance Separately

For a positive result:

```markdown
## V-### — Revalidated claim

Conclusion:
Native evidence:
Source correspondence:
Remaining boundary:
```

For performance:

```markdown
## P-### — Performance conclusion

Priority:
Measured workload/boundary:
Observed source cost:
Proposed optimization:
Semantic invariants:
Benchmark gate:
Unmeasured claims:
```

Do not hide correct work among defects. Positive validations help later agents
avoid repeating expensive reverse engineering.

## 4. Build The Executive Summary Last

Replace the live summary only after all findings stabilize. Include:

- what was revalidated;
- top unsafe/authority issues;
- top conservative false-hazard issues;
- overlooked native routines;
- native robustness failures;
- best measured performance opportunity;
- number of findings/validations/performance conclusions;
- current workload versus acceptance-target scope.

Prioritize correction by authority risk, not by ease:

1. optimistic physical transitions;
2. action/observation causality;
3. wrong exact oracle or timer;
4. mixed-direction geometry/time;
5. missing reachable native callbacks/births;
6. conservative viable-set pollution;
7. crash/ABI hardening;
8. IDA naming/types;
9. performance.

Adjust this order when retained physical evidence makes another issue more
urgent.

## 5. Consolidate Actionable Backlogs

Add one IDA/catalog table:

| Address/table | Current problem | Proposed name/type/comment | Evidence |
| --- | --- | --- | --- |

Add one verification matrix covering:

- native timer/float32 boundaries;
- action-conditioned state;
- geometry endpoints/corners;
- lifecycle and collision-enable schedules;
- RNG/pool behavior;
- C ABI extreme values;
- performance parity and timing.

Add an authority interpretation section:

- which old winning witnesses remain useful;
- which losing/empty labels cannot imply native loss;
- which hard certificates must be withdrawn or fail closed;
- which findings are shadow-only;
- which physical hits were not reclassified.

## 6. Run A Final Consistency Pass

Check:

- unique finding IDs;
- no stale “in progress” or pending language;
- evidence labels on every material conclusion;
- severity matches actual reachability;
- conservative findings are not described as unsafe misses;
- static findings are not used to reclassify hits;
- performance numbers name workload and boundary;
- current source still contains the reported issue;
- concurrent worktree changes did not resolve or invalidate a finding;
- positive validations do not contradict defect scope;
- direct-helper and physical-source counts are not conflated;
- report states what was not run or modified.

Run focused tests and minimal reproductions again if the source changed during
the audit.

## 7. Finish The Handoff

End the report with:

```markdown
## Validation Performed

## Explicit Non-Actions

## Final Assessment
```

In the final user response:

1. Link the report using its absolute path.
2. State the most consequential three to seven findings.
3. State positive validations.
4. Report focused test/reproduction results.
5. Confirm whether repository and IDA were untouched.
6. Give report size/hash when useful.

If the user authorized implementation, route fixes through the repository
contract, update authority documents, and retain a focused checkpoint. If the
task was investigation-only, stop after the report and do not apply suggested
renames or fixes.
