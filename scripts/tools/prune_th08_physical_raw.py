#!/usr/bin/env python3
"""Bound retained TH08 physical raw traces after compact evidence exists."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys


SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


_RUN_ID = re.compile(
    r"^(?P<workload>.+)_(?P<date>\d{8})_(?P<time>\d{6})$"
)
_COMPACT_SUFFIXES = (
    "session.json",
    "summary.json",
    "dossier.json",
    "regressions.json",
    "comparison.json",
    "deaths.csv",
)


@dataclass(frozen=True)
class RetainedRawBundle:
    run_id: str
    workload: str
    timestamp: str
    trace: Path
    launch_log: Path

    @property
    def bytes(self) -> int:
        return self.trace.stat().st_size + (
            self.launch_log.stat().st_size
            if self.launch_log.is_file()
            else 0
        )


def _accepted_replay_sha(session: dict[str, object]) -> str | None:
    replay = session.get("post_stage_replay_save")
    if not isinstance(replay, dict):
        return None
    current = replay.get("current_archive")
    if not isinstance(current, dict):
        return None
    metadata = current.get("metadata")
    if not isinstance(metadata, dict):
        return None
    sha256 = metadata.get("sha256")
    return sha256 if isinstance(sha256, str) and len(sha256) == 64 else None


def discover_prunable_bundles(
    *,
    report_dir: Path,
    run_note_dir: Path,
    replay_dir: Path,
    keep: int,
) -> tuple[RetainedRawBundle, ...]:
    """Return only old, fully compacted, replay-capable raw bundles."""

    if keep < 1:
        raise ValueError("raw retention count must be positive")
    eligible: dict[str, list[RetainedRawBundle]] = defaultdict(list)
    for trace in sorted(report_dir.glob("*.jsonl")):
        match = _RUN_ID.fullmatch(trace.stem)
        if match is None:
            continue
        run_id = trace.stem
        if not all(
            (report_dir / f"{run_id}.{suffix}").is_file()
            for suffix in _COMPACT_SUFFIXES
        ):
            continue
        if not (run_note_dir / f"{run_id}.md").is_file():
            continue
        try:
            session = json.loads(
                (report_dir / f"{run_id}.session.json").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, TypeError, ValueError):
            continue
        if not (
            session.get("status") == "completed"
            and session.get("trial_accepted") is True
            and session.get("hard_no_bomb") is True
        ):
            continue
        replay_sha = _accepted_replay_sha(session)
        if replay_sha is None:
            continue
        if not any(replay_dir.glob(f"*_{replay_sha}.rpy")):
            continue
        if not any(replay_dir.glob(f"*_{replay_sha}_manifest.json")):
            continue
        eligible[match.group("workload")].append(
            RetainedRawBundle(
                run_id=run_id,
                workload=match.group("workload"),
                timestamp=match.group("date") + match.group("time"),
                trace=trace,
                launch_log=report_dir / f"{run_id}.launch.log",
            )
        )

    prunable = []
    for bundles in eligible.values():
        ordered = sorted(bundles, key=lambda bundle: bundle.timestamp)
        prunable.extend(ordered[:-keep])
    return tuple(sorted(prunable, key=lambda bundle: bundle.run_id))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    repository = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=repository / "artifacts" / "runtime_reports",
    )
    parser.add_argument(
        "--run-note-dir",
        type=Path,
        default=repository / "notes" / "runs",
    )
    parser.add_argument(
        "--replay-dir",
        type=Path,
        default=repository / "artifacts" / "replays" / "archive",
    )
    parser.add_argument("--keep", type=int, default=2)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="delete the listed trace and launch-log files",
    )
    args = parser.parse_args(argv)

    bundles = discover_prunable_bundles(
        report_dir=args.report_dir,
        run_note_dir=args.run_note_dir,
        replay_dir=args.replay_dir,
        keep=args.keep,
    )
    total_bytes = sum(bundle.bytes for bundle in bundles)
    for bundle in bundles:
        print(
            f"{'delete' if args.apply else 'would_delete'} "
            f"{bundle.run_id} {bundle.bytes}"
        )
        if args.apply:
            bundle.trace.unlink()
            if bundle.launch_log.is_file():
                bundle.launch_log.unlink()
    print(
        json.dumps(
            {
                "apply": args.apply,
                "keep_per_workload": args.keep,
                "bundle_count": len(bundles),
                "bytes": total_bytes,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
