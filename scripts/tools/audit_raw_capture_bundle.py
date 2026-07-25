#!/usr/bin/env python3
"""Validate one ignored JSONL/capsule bundle before retention cleanup."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from touhou_control.viability_audit_capsule import (
    read_viability_audit_capsule,
)


def _capsule_name(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    return raw.replace("\\", "/").rsplit("/", 1)[-1]


def _hash_file(path: Path, digest) -> None:
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)


def audit(
    *,
    trace: Path,
    capsule_dir: Path,
    session: Path,
) -> dict[str, object]:
    session_record = json.loads(session.read_text(encoding="utf-8"))
    trace_digest = hashlib.sha256()
    bundle_digest = hashlib.sha256()
    referenced: set[str] = set()
    decision_count = 0
    record_count = 0
    first_frame = None
    last_frame = None
    with trace.open("rb") as source:
        for raw_line in source:
            trace_digest.update(raw_line)
            bundle_digest.update(raw_line)
            if not raw_line.strip():
                continue
            row = json.loads(raw_line)
            record_count += 1
            frame = row.get("frame")
            if isinstance(frame, int):
                first_frame = frame if first_frame is None else first_frame
                last_frame = frame
            if row.get("kind") != "decision":
                continue
            decision_count += 1
            corridor = row.get("corridor")
            if isinstance(corridor, dict):
                name = _capsule_name(corridor.get("audit_capsule"))
                if name is not None:
                    referenced.add(name)

    paths = tuple(sorted(capsule_dir.glob("*.npz")))
    available = {path.name for path in paths}
    missing = sorted(referenced - available)
    unreadable = []
    source_frames = []
    hazard_counts = {
        "moving_aabbs": 0,
        "piecewise_aabbs": 0,
        "segment_trajectories": 0,
        "packed_segment_samples": 0,
    }
    for index, path in enumerate(paths, 1):
        try:
            capsule = read_viability_audit_capsule(path)
            source_frames.append(int(capsule.metadata["source_frame"]))
            hazard_counts["moving_aabbs"] += len(capsule.aabbs)
            hazard_counts["piecewise_aabbs"] += len(
                capsule.piecewise_aabbs
            )
            hazard_counts["segment_trajectories"] += len(
                capsule.segment_trajectories
            )
            if capsule.packed_segments is not None:
                hazard_counts["packed_segment_samples"] += int(
                    capsule.packed_segments.sample_count
                )
            bundle_digest.update(path.name.encode("utf-8"))
            _hash_file(path, bundle_digest)
        except Exception as error:  # retained diagnostic boundary
            unreadable.append(
                {
                    "capsule": path.name,
                    "error": f"{type(error).__name__}: {error}",
                }
            )
        if index % 100 == 0:
            print(f"validated {index}/{len(paths)} capsules", flush=True)

    all_checks_pass = bool(
        record_count > 0
        and decision_count > 0
        and paths
        and not missing
        and not unreadable
    )
    return {
        "schema": "th08-raw-capture-bundle-audit-v1",
        "all_checks_pass": all_checks_pass,
        "workload": {
            "run_id": session_record.get("run_id"),
            "stage": session_record.get("stage"),
            "hard_no_bomb": session_record.get("hard_no_bomb"),
            "viability_audit": session_record.get("viability_audit"),
            "postpublished_survival_shadow": session_record.get(
                "postpublished_survival_shadow"
            ),
            "pipeline_prewarm_shadow": session_record.get(
                "pipeline_prewarm_shadow"
            ),
            "candidate_verifier_shadow": session_record.get(
                "candidate_verifier_shadow"
            ),
        },
        "trace": {
            "path": str(trace),
            "bytes": trace.stat().st_size,
            "sha256": trace_digest.hexdigest(),
            "record_count": record_count,
            "decision_count": decision_count,
            "first_frame": first_frame,
            "last_frame": last_frame,
            "referenced_capsule_count": len(referenced),
        },
        "capsules": {
            "directory": str(capsule_dir),
            "count": len(paths),
            "bytes": sum(path.stat().st_size for path in paths),
            "source_frame_min": min(source_frames) if source_frames else None,
            "source_frame_max": max(source_frames) if source_frames else None,
            "missing_references": missing,
            "unreadable": unreadable,
            "hazard_counts": hazard_counts,
        },
        "bundle_sha256": bundle_digest.hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("capsules", type=Path)
    parser.add_argument("session", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    report = audit(
        trace=args.trace,
        capsule_dir=args.capsules,
        session=args.session,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
