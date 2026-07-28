# Live Controller CLI Schema Refactor

Date: 2026-07-28

Status: behavior-preserving structural checkpoint

## Boundary

The public `scripts/th08_live_dodge_agent.py` was already a 22-line
compatibility facade, while `scripts/th08_live/controller.py` had regrown to
4,698 lines after later G5 and combat instrumentation. Its 374-line
`build_parser()` mixed a stable launch schema into the remaining live-session
owner.

This checkpoint moves the parser schema to `scripts/th08_live/cli.py`.
`LiveParserDefaults` is an immutable dependency object, and
`build_live_parser()` has no controller/runtime import. The controller retains
the historical `build_parser()` name and constructs the defaults on every
call from its current module globals. This preserves tests and external users
that patch compatibility constants before building a parser.

The controller falls from 4,698 to 4,341 lines. The dominant remaining block
is still `_run_live_session`; no claim is made that line count alone improves
control.

## Exact Characterization

The parent-commit parser and extracted parser were loaded side by side and
compared over all 57 actions:

- action class and option strings;
- destination, `nargs`, constant, and default;
- type and choices;
- required flag, help, and metavar; and
- the one mutually exclusive Bomb group.

The normalized schemas are exactly equal. A separate regression patches
controller horizon, corridor cadence, and transition-timeout globals and
confirms that the compatibility wrapper resolves the patched values at call
time.

## Automated Evidence

- focused extracted-CLI tests: 3/3;
- existing live-controller facade tests: 92/92;
- hotkey launch-contract tests: 16/16;
- practice/full-route supervisor tests: 25/25 and 6/6;
- focused Ruff: pass;
- complete Linux quick suite: 976 tests in 9.979 seconds; and
- complete Windows quick suite: 976 tests in 26.840 seconds with three
  existing platform skips.

## Authority

This is parser ownership only. It changes no option, default, action mask,
Bomb policy, capture, planner, issue order, trace schema, runtime service,
timing path, model, physical evidence, or live action authority. No physical
trial is required for this pure launch-schema move; the next lifecycle/session
extraction must receive its own appropriate physical gate.
