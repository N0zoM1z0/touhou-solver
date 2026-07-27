#!/usr/bin/env python3
"""Build or replay the retained 61-root losing-state dossier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis.exact_root_loss import (
    build_dossier,
    render_markdown,
    replay_dossier,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--source-report", type=Path, required=True)
    build.add_argument("--trace", type=Path, required=True)
    build.add_argument("--capsule-dir", type=Path, required=True)
    build.add_argument("--bundle-audit", type=Path)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--markdown", type=Path)
    build.add_argument("--minimum-pre-hit-frames", type=int, default=240)

    replay = subparsers.add_parser("replay")
    replay.add_argument("--dossier", type=Path, required=True)
    replay.add_argument("--capsule-dir", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--root-limit", type=int)
    replay.add_argument("--variant", action="append", dest="variants")
    return parser


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build":
        dossier = build_dossier(
            source_report_path=args.source_report,
            trace_path=args.trace,
            capsule_dir=args.capsule_dir,
            bundle_audit_path=args.bundle_audit,
            minimum_pre_hit_frames=args.minimum_pre_hit_frames,
        )
        _write_json(args.output, dossier)
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(
                render_markdown(dossier),
                encoding="utf-8",
            )
        print(json.dumps(dossier["gate"], indent=2))
        return 0 if dossier["gate"]["passed"] else 1

    replay = replay_dossier(
        dossier_path=args.dossier,
        capsule_dir=args.capsule_dir,
        root_limit=args.root_limit,
        selected_variants=(
            tuple(args.variants) if args.variants else None
        ),
    )
    _write_json(args.output, replay)
    print(json.dumps(replay["gate"], indent=2))
    return 0 if replay["gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
