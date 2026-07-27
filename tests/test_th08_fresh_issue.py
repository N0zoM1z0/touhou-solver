from __future__ import annotations

import unittest
from types import SimpleNamespace

import th08_live_dodge_agent as live
from th08_live.fresh_issue import (
    FreshEnemyIssueDependencies,
    recertify_fresh_enemy_prefix,
)
from th08_live.models import (
    EnemyBody,
    EnemyBodyModeMemory,
    EnemyPoolSnapshot,
)
from th08_local_planner import LocalProposal


def _body(pointer: int, x: float) -> EnemyBody:
    return EnemyBody(
        pointer=pointer,
        x=x,
        y=100.0,
        vx=0.0,
        vy=0.0,
        half_width=8.0,
        half_height=8.0,
        flags=1,
    )


def _decision(action: str, mask: int) -> live.Decision:
    return live.Decision(
        mask=mask,
        action=action,
        min_clearance=4.0,
        immediate_clearance=4.0,
        score=0.0,
        bomb=False,
    )


class FreshIssueStageTests(unittest.TestCase):
    def test_unchanged_prefix_preserves_proposal_without_commit(self) -> None:
        planned = EnemyPoolSnapshot(40, 40, (_body(100, 20.0),), 0.1)
        memory = EnemyBodyModeMemory(maximum_age_frames=80)
        proposal = LocalProposal.from_decision(
            _decision("stay", live.SHOT | live.FOCUS)
        )
        commit_calls = []
        clock_values = iter((1.0, 1.002))

        result = recertify_fresh_enemy_prefix(
            proposal=proposal,
            reader=object(),
            memory=memory,
            alignment_frame=40,
            planned_prefix_snapshot=planned,
            planned_prefix_bodies=planned.bodies,
            enemy_bodies=planned.bodies,
            commit=lambda *args: commit_calls.append(args),
            dependencies=FreshEnemyIssueDependencies(
                capture_prefix=lambda _reader: planned,
                detect_changes=lambda *_snapshots: (),
                merge_prefix=lambda background, _prefix: background,
                monotonic=lambda: next(clock_values),
            ),
        )

        self.assertIs(result.decision, proposal.decision)
        self.assertFalse(result.changed)
        self.assertAlmostEqual(result.read_ms, 2.0)
        self.assertEqual(result.recertification_ms, 0.0)
        self.assertEqual(commit_calls, [])

    def test_changed_prefix_commits_against_merged_fresh_bodies(self) -> None:
        planned = EnemyPoolSnapshot(50, 50, (_body(100, 20.0),), 0.1)
        current = EnemyPoolSnapshot(51, 51, (_body(100, 24.0),), 0.2)
        background = (_body(200, 200.0),)
        corrected = _decision("left", live.SHOT | live.LEFT)
        proposal = LocalProposal.from_decision(
            _decision("right", live.SHOT | live.RIGHT)
        )
        committed_bodies = []
        clock_values = iter((2.0, 2.003, 2.004, 2.009))

        def commit(_proposal, bodies):
            committed_bodies.append(bodies)
            return SimpleNamespace(decision=corrected)

        result = recertify_fresh_enemy_prefix(
            proposal=proposal,
            reader=object(),
            memory=EnemyBodyModeMemory(maximum_age_frames=80),
            alignment_frame=51,
            planned_prefix_snapshot=planned,
            planned_prefix_bodies=planned.bodies,
            enemy_bodies=background,
            commit=commit,
            dependencies=FreshEnemyIssueDependencies(
                capture_prefix=lambda _reader: current,
                detect_changes=lambda *_snapshots: ("position",),
                merge_prefix=lambda base, prefix: base + prefix,
                monotonic=lambda: next(clock_values),
            ),
        )

        self.assertIs(result.decision, corrected)
        self.assertTrue(result.changed)
        self.assertEqual(result.changes, ("position",))
        self.assertAlmostEqual(result.read_ms, 3.0)
        self.assertAlmostEqual(result.recertification_ms, 5.0)
        self.assertEqual(
            committed_bodies,
            [background + result.prefix_bodies],
        )
        self.assertEqual(
            result.enemy_bodies_for_shadow,
            background + result.prefix_bodies,
        )

    def test_dormant_prefix_identity_is_retained_in_result(self) -> None:
        first = EnemyPoolSnapshot(60, 60, (_body(100, 20.0),), 0.1)
        empty = EnemyPoolSnapshot(62, 62, (), 0.1)
        memory = EnemyBodyModeMemory(maximum_age_frames=80)
        memory.merge_snapshot(first, frame=60)
        clock_values = iter((3.0, 3.001))
        proposal = LocalProposal.from_decision(
            _decision("stay", live.SHOT | live.FOCUS)
        )

        result = recertify_fresh_enemy_prefix(
            proposal=proposal,
            reader=object(),
            memory=memory,
            alignment_frame=62,
            planned_prefix_snapshot=first,
            planned_prefix_bodies=first.bodies,
            enemy_bodies=first.bodies,
            commit=lambda *_args: SimpleNamespace(
                decision=proposal.decision
            ),
            dependencies=FreshEnemyIssueDependencies(
                capture_prefix=lambda _reader: empty,
                detect_changes=lambda *_snapshots: (),
                monotonic=lambda: next(clock_values),
            ),
        )

        self.assertEqual(result.dormant_pointers, frozenset({100}))
        self.assertEqual(
            tuple(body.pointer for body in result.prefix_bodies),
            (100,),
        )


if __name__ == "__main__":
    unittest.main()
