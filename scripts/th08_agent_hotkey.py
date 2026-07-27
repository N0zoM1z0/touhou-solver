#!/usr/bin/env python3
"""Compatibility entry point for the TH08 hotkey agent supervisor."""

from __future__ import annotations

import sys

from th08_automation import agent_hotkey as _implementation

if __name__ == "__main__":
    raise SystemExit(_implementation.main())

sys.modules[__name__] = _implementation
