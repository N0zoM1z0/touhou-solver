#!/usr/bin/env python3
"""Compatibility entry point for the structured TH08 live controller."""

from __future__ import annotations

import sys

from th08_live import controller as _controller


if __name__ == "__main__":
    try:
        raise SystemExit(
            _controller.run(_controller.build_parser().parse_args())
        )
    except Exception as exc:
        print(f"error: {exc}")
        raise SystemExit(1)
else:
    # Preserve historical imports and patch seams while the remaining
    # implementation is progressively split behind th08_live modules.
    sys.modules[__name__] = _controller
