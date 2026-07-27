#!/usr/bin/env python3
"""Compatibility entry point for supervised TH08 Practice Start trials."""

from __future__ import annotations

import sys

from th08_automation import practice_supervisor as _supervisor


if __name__ == "__main__":
    try:
        raise SystemExit(_supervisor.main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
else:
    # Preserve historical imports and patch seams for tests, BAT wrappers, and
    # the full-route supervisor while implementation modules are separated.
    sys.modules[__name__] = _supervisor
