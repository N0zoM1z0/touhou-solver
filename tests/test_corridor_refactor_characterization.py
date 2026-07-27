from __future__ import annotations

import json
import unittest
from pathlib import Path

from analysis.corridor_refactor_characterization import build_report


FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "corridor_refactor_characterization_v1.json"
)


class CorridorRefactorCharacterizationTests(unittest.TestCase):
    def test_current_behavior_matches_refactor_baseline(self) -> None:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(build_report(), expected)


if __name__ == "__main__":
    unittest.main()
