from __future__ import annotations

from concurrent.futures import Future
import unittest

from th08_live.birth_contention import (
    BIRTH_CONTENTION_OMITTED_SOURCES,
    FUTURE_ABSENT,
    FUTURE_DONE,
    FUTURE_INFLIGHT,
    BirthObserverContention,
    capture_birth_observer_future_states,
)


class BirthObserverContentionTests(unittest.TestCase):
    def test_endpoint_capture_is_lookup_only_and_explicit(self) -> None:
        done = Future()
        done.set_result(4)
        inflight = Future()
        before = capture_birth_observer_future_states(
            corridor_future=inflight,
            survival_future=None,
            enemy_future=done,
        )
        self.assertEqual(before.corridor, FUTURE_INFLIGHT)
        self.assertEqual(before.survival, FUTURE_ABSENT)
        self.assertEqual(before.enemy, FUTURE_DONE)
        self.assertFalse(inflight.done())

        inflight.set_result(5)
        after = capture_birth_observer_future_states(
            corridor_future=inflight,
            survival_future=None,
            enemy_future=done,
        )
        record = BirthObserverContention(before, after).record()
        self.assertEqual(
            record["corridor_future"],
            {"before": FUTURE_INFLIGHT, "after": FUTURE_DONE},
        )
        self.assertEqual(
            record["omitted_sources"],
            list(BIRTH_CONTENTION_OMITTED_SOURCES),
        )


if __name__ == "__main__":
    unittest.main()
