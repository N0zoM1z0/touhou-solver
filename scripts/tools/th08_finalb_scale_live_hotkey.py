#!/usr/bin/env python3
"""Prewarm the explicitly scoped Final-B live scale-delivery hotkey gate."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_automation.agent_hotkey import AgentHotkey  # noqa: E402
from th08_live.scale_source_trace import (  # noqa: E402
    FINAL_B_ECL_STATIC_SHA256,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATIC_ECL = ROOT / "artifacts" / "decoded" / "ecldata7.ecl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prewarm one hard-no-Bomb Lunatic Final-B spell-190 live "
            "scale-source delivery trial; F8 starts, F9 stops, F10 exits"
        )
    )
    parser.add_argument(
        "--static-ecl",
        type=Path,
        default=DEFAULT_STATIC_ECL,
    )
    parser.add_argument(
        "--static-sha256",
        default=FINAL_B_ECL_STATIC_SHA256,
    )
    parser.add_argument("--duration", type=float, default=600.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.duration <= 0.0:
        raise ValueError("duration must be positive")
    print(
        "Final-B SEM-SCALE live gate prewarmed: select the THPRAC Lunatic "
        "Sakuya/Remilia spell-190 checkpoint, then press F8; press F9 after "
        "the physical unit-scale restore or immediately on contamination.",
        flush=True,
    )
    agent = AgentHotkey(
        expected_difficulty=3,
        expected_stage=7,
        terminal_stage=7,
        runtime_ecl_static_image=args.static_ecl,
        runtime_ecl_static_sha256=args.static_sha256,
        enable_finalb_scale_source_authority=True,
        duration_seconds=args.duration,
        detailed_summary=True,
    )
    return agent.run()


if __name__ == "__main__":
    raise SystemExit(main())
