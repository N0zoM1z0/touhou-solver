from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.prune_th08_physical_raw import discover_prunable_bundles


class PruneTh08PhysicalRawTests(unittest.TestCase):
    def _bundle(
        self,
        root: Path,
        run_id: str,
        *,
        accepted: bool = True,
        compact: bool = True,
    ) -> None:
        reports = root / "reports"
        notes = root / "notes"
        replays = root / "replays"
        reports.mkdir(exist_ok=True)
        notes.mkdir(exist_ok=True)
        replays.mkdir(exist_ok=True)
        (reports / f"{run_id}.jsonl").write_text("{}\n")
        (reports / f"{run_id}.launch.log").write_text("launch\n")
        sha256 = (run_id.encode().hex() + "0" * 64)[:64]
        session = {
            "status": "completed",
            "trial_accepted": accepted,
            "hard_no_bomb": True,
            "post_stage_replay_save": {
                "current_archive": {"metadata": {"sha256": sha256}}
            },
        }
        (reports / f"{run_id}.session.json").write_text(
            json.dumps(session)
        )
        if compact:
            for suffix in (
                "summary.json",
                "dossier.json",
                "regressions.json",
                "comparison.json",
                "deaths.csv",
            ):
                (reports / f"{run_id}.{suffix}").write_text("{}\n")
            (notes / f"{run_id}.md").write_text("retained\n")
        (replays / f"th8_01_{sha256}.rpy").write_bytes(b"rpy")
        (replays / f"th8_01_{sha256}_manifest.json").write_text("{}\n")

    def test_keeps_two_newest_complete_bundles_per_workload(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for stamp in ("20260801_010000", "20260801_020000", "20260801_030000"):
                self._bundle(root, f"lunatic_route2_stage3_unattended_{stamp}")
            self._bundle(
                root,
                "lunatic_route2_stage4a_unattended_20260801_010000",
            )

            bundles = discover_prunable_bundles(
                report_dir=root / "reports",
                run_note_dir=root / "notes",
                replay_dir=root / "replays",
                keep=2,
            )

            self.assertEqual(
                [bundle.run_id for bundle in bundles],
                ["lunatic_route2_stage3_unattended_20260801_010000"],
            )

    def test_never_prunes_unaccepted_or_incomplete_evidence(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._bundle(
                root,
                "lunatic_route2_stage5_unattended_20260801_010000",
                accepted=False,
            )
            self._bundle(
                root,
                "lunatic_route2_stage5_unattended_20260801_020000",
                compact=False,
            )
            self._bundle(
                root,
                "lunatic_route2_stage5_unattended_20260801_030000",
            )

            bundles = discover_prunable_bundles(
                report_dir=root / "reports",
                run_note_dir=root / "notes",
                replay_dir=root / "replays",
                keep=1,
            )

            self.assertEqual(bundles, ())


if __name__ == "__main__":
    unittest.main()
