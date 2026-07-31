from __future__ import annotations

import unittest
from types import SimpleNamespace

from th08_live import PolicyCoordinator, PolicyQueryRequest
from touhou_control.policy_guidance import LocalPolicyGuidance


class PolicyCoordinatorTests(unittest.TestCase):
    def test_query_uses_one_solution_and_preserves_arguments(self) -> None:
        calls: list[tuple[str, tuple[object, ...], object]] = []

        def query(name: str, result: object):
            def execute(*args: object, **kwargs: object) -> object:
                calls.append((name, args, kwargs))
                return result

            return execute

        guidance = LocalPolicyGuidance(
            support_covers_current=True,
            allowed_first_actions=("left",),
        )
        solution = SimpleNamespace(
            plan=SimpleNamespace(
                viability_policy=SimpleNamespace(delay_frames=(1, 2, 3))
            )
        )
        coordinator = PolicyCoordinator(
            target_query=query("target", (10.0, 20.0, 30)),
            viability_query=query("viability", "viable"),
            safety_value_query=query("safety", "safety"),
            guidance_assembler=lambda **kwargs: (
                calls.append(("guidance", (), kwargs)) or guidance
            ),
        )
        request = PolicyQueryRequest(
            solution=solution,
            target_frame=120,
            query_frame=118,
            player_x=33.0,
            player_y=44.0,
            active_action="left",
            observed_action="up",
            lookahead_frames=12,
            max_age_frames=20,
            current_delay_frames=(2, 3),
        )

        snapshot = coordinator.query(request)

        self.assertEqual(
            [name for name, _args, _kwargs in calls],
            ["target", "viability", "safety", "guidance"],
        )
        for _name, args, _kwargs in calls[:3]:
            self.assertIs(args[0], solution)
        self.assertEqual(calls[0][2], {
            "current_frame": 120,
            "lookahead_frames": 12,
            "max_age_frames": 20,
        })
        self.assertEqual(calls[-1][2], {
            "viability_query": "viable",
            "safety_value_query": "safety",
            "policy_delay_frames": (1, 2, 3),
            "current_delay_frames": (2, 3),
        })
        self.assertEqual(snapshot.primary.target, (10.0, 20.0, 30))
        self.assertEqual(snapshot.primary.viability_query, "viable")
        self.assertEqual(snapshot.safety_value_query, "safety")
        self.assertIs(snapshot.guidance, guidance)


if __name__ == "__main__":
    unittest.main()
