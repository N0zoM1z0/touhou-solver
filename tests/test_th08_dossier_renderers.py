from __future__ import annotations

import unittest

from analysis.dossier import full_run_render, practice_render
from analysis import th08_practice_dossier, th08_run_dossier


class Th08DossierRendererOwnershipTests(unittest.TestCase):
    def test_full_run_entry_point_preserves_renderer_aliases(self) -> None:
        self.assertIs(
            th08_run_dossier.render_markdown,
            full_run_render.render_markdown,
        )
        self.assertIs(
            th08_run_dossier.write_death_csv,
            full_run_render.write_death_csv,
        )
        self.assertIs(
            th08_run_dossier._format_number,
            full_run_render._format_number,
        )

    def test_practice_entry_point_preserves_renderer_aliases(self) -> None:
        self.assertIs(
            th08_practice_dossier.render_markdown,
            practice_render.render_markdown,
        )
        self.assertIs(
            th08_practice_dossier.write_death_csv,
            practice_render.write_death_csv,
        )
        self.assertIs(
            th08_practice_dossier._format,
            practice_render._format,
        )


if __name__ == "__main__":
    unittest.main()
