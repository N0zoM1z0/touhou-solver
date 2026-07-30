# Native Replay Wind-Tunnel Local Artifacts

The `raw/` subtree is local, ignored, and retained outside `/tmp`.

- `raw/accepted/` contains the current 36-replay corpus, corrected
  manager-2137 all-action child runs, six manager-2257 follow-ups, and corpus
  generator output.
- `raw/rejected/` contains the interrupted/wrong-fence native branch run.
- `raw/legacy/` contains the earlier replay corpora, generator-only audit,
  inventories, and stdout needed to reconstruct the investigation history.

Tracked compact evidence lives under `artifacts/runtime_reports/`. The
canonical accepted reports are:

- `native_replay_stage5_latest_first_hit_20260730.json`;
- `native_replay_stage5_latest_manager2130_capture_retry_20260730.json`;
- `th08_native_replay_causal_branch_corpus_latest_root2129_20260730.json`;
- `th08_native_branch_trials_latest_root2129_fence2137_all36_20260730.json`;
- `th08_native_branch_trials_latest_root2129_witness_fence2257_20260730.json`.

Wrong-fence or incomplete reports are under
`artifacts/runtime_reports/rejected/`; successful intermediate reports
superseded by a complete aggregate are under
`artifacts/runtime_reports/superseded/`.

Do not delete the current accepted raw bundles until two newer compatible
replay-capable bundles and compact tracked reports exist. Never commit raw
child logs or large generated replay portfolios.
