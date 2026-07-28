#!/usr/bin/env python3
"""Join retained TH08 bullet activations to physical hit candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis.birth_hit_provenance import audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--dossier", type=Path, required=True)
    parser.add_argument("--gameplay-epoch", type=int)
    parser.add_argument("--stage-route-index", type=int)
    arguments = parser.parse_args(argv)
    report = audit(
        trace=arguments.trace,
        dossier=arguments.dossier,
        gameplay_epoch=arguments.gameplay_epoch,
        stage_route_index=arguments.stage_route_index,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report["report_digest"]))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
