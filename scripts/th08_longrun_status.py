#!/usr/bin/env python3
"""Stream a compact progress snapshot from a growing TH08 long-run trace."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterable

from th08_trial_report import STAGE_ROUTE_LABELS


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "runtime_reports"


def summarize_progress(
    rows: Iterable[dict[str, object]],
) -> dict[str, object]:
    first_frame = None
    latest = None
    summary = None
    hit_frames: list[int] = []
    stage_transitions: list[dict[str, object]] = []
    previous_stage = None
    decision_count = 0
    auto_confirm_events = 0
    runtime_error = None

    for row in rows:
        kind = row.get("kind")
        if kind == "summary":
            summary = row
            continue
        if kind == "runtime_error":
            runtime_error = row
            continue
        if kind != "decision":
            continue
        decision_count += 1
        latest = row
        frame = int(row["frame"])
        if first_frame is None:
            first_frame = frame
        if row.get("hit_started"):
            hit_frames.append(frame)
        if row.get("auto_confirm") is not None:
            auto_confirm_events += 1
        stage_index = row.get("stage_route_index")
        if stage_index is not None:
            stage_index = int(stage_index)
            if stage_index != previous_stage:
                stage_transitions.append(
                    {
                        "frame": frame,
                        "stage_route_index": stage_index,
                        "stage_label": STAGE_ROUTE_LABELS.get(stage_index),
                    }
                )
                previous_stage = stage_index

    result: dict[str, object] = {
        "decision_count": decision_count,
        "first_frame": first_frame,
        "hit_count": len(hit_frames),
        "hit_frames": hit_frames,
        "stage_transitions": stage_transitions,
        "auto_confirm_events": auto_confirm_events,
        "complete": summary is not None,
        "termination_reason": (
            summary.get("termination_reason")
            if summary is not None
            else None
        ),
        "runtime_error": runtime_error,
    }
    if latest is not None:
        stage_index = latest.get("stage_route_index")
        stage_index = int(stage_index) if stage_index is not None else None
        result["latest"] = {
            "frame": int(latest["frame"]),
            "stage_route_index": stage_index,
            "stage_label": STAGE_ROUTE_LABELS.get(stage_index),
            "resources": latest.get("resources"),
            "player": latest.get("player"),
            "active_bullets": latest.get("active_bullets"),
            "active_lasers": latest.get("active_lasers"),
            "active_items": latest.get("active_items"),
            "action": latest.get("action"),
            "auto_confirm": latest.get("auto_confirm"),
        }
    else:
        result["latest"] = None
    return result


def load_rows(path: Path) -> Iterable[dict[str, object]]:
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # A concurrent writer may not have finished its final line yet.
                continue


def latest_trace(report_dir: Path = DEFAULT_REPORT_DIR) -> Path:
    candidates = list(report_dir.glob("*_hotkey_longrun_*.jsonl"))
    if not candidates:
        raise FileNotFoundError(f"no long-run traces below {report_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime_ns)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    args = parser.parse_args(argv)
    path = args.input if args.input is not None else latest_trace()
    status = summarize_progress(load_rows(path))
    stat = path.stat()
    status.update(
        {
            "path": str(path),
            "size_bytes": stat.st_size,
            "updated_seconds_ago": max(0.0, time.time() - stat.st_mtime),
        }
    )
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
