from __future__ import annotations

import unittest

from benchmarks.benchmark_bullet_birth_observer import _abba_samples


class BulletBirthObserverBenchmarkTests(unittest.TestCase):
    def test_abba_pairing_balances_order_and_returns_one_mean_per_pair(
        self,
    ) -> None:
        calls: list[str] = []

        def baseline() -> None:
            calls.append("B")

        def interleaved() -> None:
            calls.append("I")

        baseline_samples, interleaved_samples = _abba_samples(
            baseline,
            interleaved,
            iterations=3,
            warmup=1,
        )
        self.assertEqual(calls, list("BIIB" * 4))
        self.assertEqual(len(baseline_samples), 3)
        self.assertEqual(len(interleaved_samples), 3)
        self.assertTrue(all(value >= 0.0 for value in baseline_samples))
        self.assertTrue(all(value >= 0.0 for value in interleaved_samples))


if __name__ == "__main__":
    unittest.main()
