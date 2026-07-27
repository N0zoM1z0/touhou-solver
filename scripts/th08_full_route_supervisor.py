#!/usr/bin/env python3
"""Compatibility entry point for supervised full-route TH08 trials."""

from __future__ import annotations

import sys

from th08_automation import full_route_supervisor as _implementation

if __name__ == "__main__":
    raise SystemExit(_implementation.main())

sys.modules[__name__] = _implementation
