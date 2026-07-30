#!/usr/bin/env python3
"""Archive one TH08 replay under its content identity before slot overwrite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_replay_archive import archive_replay  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("archive_dir", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    record = archive_replay(
        args.source,
        args.archive_dir,
        manifest=args.manifest,
    )
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
