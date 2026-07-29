from __future__ import annotations

from pathlib import Path
import unittest

from th08_automation.practice_supervisor import build_parser
from th08_live.scale_source_trace import FINAL_B_ECL_STATIC_SHA256


ROOT = Path(__file__).resolve().parents[1]
BAT = ROOT / "run_th08_finalb_scale_live_trial.bat"


class FinalBScaleLiveTrialTests(unittest.TestCase):
    def test_bat_uses_original_game_practice_supervisor(self) -> None:
        text = BAT.read_text(encoding="utf-8")

        self.assertIn("scripts\\th08_practice_supervisor.py", text)
        self.assertIn("--stage 6b", text)
        self.assertIn("--difficulty lunatic", text)
        self.assertIn("--enable-finalb-scale-source-authority", text)
        self.assertIn(FINAL_B_ECL_STATIC_SHA256, text)
        self.assertNotIn("thprac", text.lower())

    def test_command_contract_parses_as_finalb_practice(self) -> None:
        args = build_parser().parse_args(
            [
                "--armed",
                "--stage",
                "6b",
                "--difficulty",
                "lunatic",
                "--runtime-ecl-static-image",
                "artifacts/decoded/ecldata7.ecl",
                "--runtime-ecl-static-sha256",
                FINAL_B_ECL_STATIC_SHA256,
                "--enable-finalb-scale-source-authority",
            ]
        )

        self.assertEqual(args.stage.route_index, 7)
        self.assertEqual(args.difficulty.menu_index, 3)
        self.assertTrue(args.enable_finalb_scale_source_authority)


if __name__ == "__main__":
    unittest.main()
