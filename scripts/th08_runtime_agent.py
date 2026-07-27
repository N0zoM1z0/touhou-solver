#!/usr/bin/env python3
"""Compatibility entry point for the structured TH08 runtime boundary."""

from __future__ import annotations

import sys

from th08_runtime import controller as _controller


if __name__ == "__main__":
    try:
        raise SystemExit(_controller.main())
    except Exception as exc:
        print(f"error: {exc}")
        raise SystemExit(1)
else:
    # Preserve historical imports and patch seams while the implementation is
    # progressively split behind the th08_runtime package.
    sys.modules[__name__] = _controller
