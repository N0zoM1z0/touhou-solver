from __future__ import annotations

import unittest

from analysis.dossier import attribution
from analysis import th08_practice_dossier, th08_run_dossier


class Th08DossierAttributionOwnershipTests(unittest.TestCase):
    def test_legacy_full_run_imports_are_exact_aliases(self) -> None:
        aliases = {
            "_case_prefix_for_difficulty": "case_prefix_for_difficulty",
            "_classify_death": "classify_death",
            "_death_clusters": "cluster_deaths",
            "_death_ledger": "build_death_ledger",
            "_input_mask_action": "input_mask_action",
            "_nearest_bullet": "nearest_bullet",
            "_nearest_enemy_body": "nearest_enemy_body",
            "_nearest_laser": "nearest_laser",
            "_robust_control_unsafe": "robust_control_unsafe",
            "_spell_attribution": "spell_attribution",
            "_viability_action_set_empty": "viability_action_set_empty",
        }
        for legacy_name, owner_name in aliases.items():
            with self.subTest(legacy_name=legacy_name):
                self.assertIs(
                    getattr(th08_run_dossier, legacy_name),
                    getattr(attribution, owner_name),
                )

    def test_practice_dossier_uses_shared_death_ownership(self) -> None:
        self.assertIs(
            th08_practice_dossier._case_prefix_for_difficulty,
            attribution.case_prefix_for_difficulty,
        )
        self.assertIs(
            th08_practice_dossier._death_ledger,
            attribution.build_death_ledger,
        )
        self.assertIs(
            th08_practice_dossier._death_clusters,
            attribution.cluster_deaths,
        )


if __name__ == "__main__":
    unittest.main()
