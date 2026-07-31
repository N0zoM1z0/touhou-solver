# TH08 Pre-Prune Archive

The active workspace was pruned on 2026-07-31 after checkpoint `d2b810d`.
Nothing in the archive has live or solver authority. It exists only for
historical recovery.

## Recovery anchors

- Git tag: `pre-workspace-prune-20260731`
- Tagged commit: `d2b810d`
- Full tracked tree:
  `archive/bundles/tracked-pre-prune-d2b810d.tar.zst`
  (`fef7885d9ff969afb72aaee2d87c8ab96b9917ad9022d24ecd1db90fcfbcd4f2`)
- Documentation:
  `archive/bundles/docs-pre-prune-d2b810d.tar.zst`
  (`523bd5056e3baade5794dc44eb978ec9e30fad05300dc18f2adadccb7f7a483c`)
- Code and tests:
  `archive/bundles/code-tests-pre-prune-d2b810d.tar.zst`
  (`4a11724151f524f3a58b4bea67f93881f429d3af338ff6170ead1ddcc4660daa`)

The local `archive/` directory is ignored by Git. It also contains retired
raw JSONL, launch logs, captures, old roots, and external reference clones.

## Relocated active-run raw evidence

The 2026-07-31 Stage 3/4A/5 compact dossiers intentionally preserve their
capture-time `artifacts/runtime_reports/*.jsonl` provenance paths. The large
ignored files now live at:

```text
archive/raw/runtime_reports/lunatic_route2_stage3_unattended_20260731_091104.jsonl
archive/raw/runtime_reports/lunatic_route2_stage4a_unattended_20260731_091925.jsonl
archive/raw/runtime_reports/lunatic_route2_stage5_unattended_20260731_093027.jsonl
```

Do not rewrite retained dossier provenance to reflect local relocation.
Resolve the basename through `archive/raw/runtime_reports/` and verify the
recorded SHA-256 before use.

## Inspect without restoring

```bash
git show pre-workspace-prune-20260731:path/to/file
tar --use-compress-program=unzstd -tf \
  archive/bundles/tracked-pre-prune-d2b810d.tar.zst
```

Extract into a new temporary directory, never over the active workspace:

```bash
restore_dir="$(mktemp -d)"
tar --use-compress-program=unzstd \
  -xf archive/bundles/tracked-pre-prune-d2b810d.tar.zst \
  -C "$restore_dir"
```

Do not restore an old subsystem merely because a historical note references
it. First demonstrate that it answers a current hit, planner, model, or
delivery question better than the retained active path.
