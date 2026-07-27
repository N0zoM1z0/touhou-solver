from __future__ import annotations

import unittest

from runtime_agent import InputTransition
from th08_live import IssueController


class IssueControllerTests(unittest.TestCase):
    def make_controller(
        self,
        events: list[object],
        *,
        forbidden_mask: int = 0,
    ) -> IssueController:
        ticks = iter((1.000, 1.003))

        def build(
            previous_mask: int,
            target_mask: int,
            *,
            supported_mask: int,
        ) -> tuple[InputTransition, ...]:
            events.append(
                (
                    "build",
                    previous_mask,
                    target_mask,
                    supported_mask,
                )
            )
            return (InputTransition(0x40, True),)

        return IssueController(
            api="api",
            pid=73,
            supported_mask=0xF7,
            forbidden_mask=forbidden_mask,
            transition_builder=build,
            transition_sender=lambda api, transitions: events.append(
                ("send", api, transitions)
            ),
            foreground_guard=lambda api, pid: events.append(
                ("foreground", api, pid)
            ),
            clock=lambda: next(ticks),
        )

    def test_dispatch_preserves_guard_build_send_order_and_timing(
        self,
    ) -> None:
        events: list[object] = []
        controller = self.make_controller(events)

        result = controller.dispatch(
            0x01,
            0x41,
            require_foreground=True,
        )

        self.assertEqual(
            events,
            [
                ("foreground", "api", 73),
                ("build", 0x01, 0x41, 0xF7),
                (
                    "send",
                    "api",
                    (InputTransition(0x40, True),),
                ),
            ],
        )
        self.assertEqual(result.previous_mask, 0x01)
        self.assertEqual(result.target_mask, 0x41)
        self.assertEqual(
            result.transitions,
            (InputTransition(0x40, True),),
        )
        self.assertAlmostEqual(result.input_ms, 3.0)

    def test_forbidden_bomb_fails_before_guard_or_send(self) -> None:
        events: list[object] = []
        controller = self.make_controller(
            events,
            forbidden_mask=0x02,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "no-bomb policy produced a Bomb input",
        ):
            controller.dispatch(
                0x01,
                0x03,
                require_foreground=True,
            )

        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
