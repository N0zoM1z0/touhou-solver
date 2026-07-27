#!/usr/bin/env python3
"""Compatibility entry point for TH08 ECL parsing and reporting."""

from __future__ import annotations

import sys

from th08_ecl_tool import controller as _implementation

if __name__ == "__main__":
    raise SystemExit(_implementation.main())

sys.modules[__name__] = _implementation
