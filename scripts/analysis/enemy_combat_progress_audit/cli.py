"""Command-line delivery for the enemy combat-progress physical audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .report import audit_enemy_combat_progress


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--route-id", type=int, required=True)
    parser.add_argument("--difficulty-index", type=int, required=True)
    parser.add_argument("--stage-route-index", type=int, required=True)
    arguments = parser.parse_args(argv)
    report = audit_enemy_combat_progress(
        arguments.trace,
        expected_route_id=arguments.route_id,
        expected_difficulty_index=arguments.difficulty_index,
        expected_stage_route_index=arguments.stage_route_index,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"passed": report["passed"], "output": str(arguments.output)}))
    return 0 if report["passed"] else 1


__all__ = ["main"]
