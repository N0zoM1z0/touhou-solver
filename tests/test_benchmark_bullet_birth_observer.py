from __future__ import annotations

import unittest

from benchmarks.benchmark_bullet_birth_observer import (
    _abba_samples,
    _future_scenarios,
    _pool,
    _set_active_states,
)
from th08_live.bullet_decode import BULLET_STATE_OFFSET
from th08_live.sensor import BULLET_STRIDE


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

    def test_future_scenarios_are_stable_and_nonblocking(self) -> None:
        scenarios = _future_scenarios()

        self.assertEqual(set(scenarios), {"absent", "done", "inflight"})
        self.assertIsNone(scenarios["absent"][0])
        self.assertTrue(scenarios["done"][0].done())
        self.assertFalse(scenarios["inflight"][0].done())

    def test_active_state_toggle_reuses_the_same_blob(self) -> None:
        blob = _pool(2)
        identity = id(blob)

        _set_active_states(blob, density=2, active=False)
        self.assertEqual(
            int.from_bytes(
                blob[
                    BULLET_STATE_OFFSET
                    : BULLET_STATE_OFFSET + 2
                ],
                "little",
            ),
            0,
        )
        _set_active_states(blob, density=2, active=True)
        self.assertEqual(id(blob), identity)
        self.assertEqual(
            int.from_bytes(
                blob[
                    BULLET_STRIDE + BULLET_STATE_OFFSET
                    : BULLET_STRIDE + BULLET_STATE_OFFSET + 2
                ],
                "little",
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
