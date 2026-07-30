from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from analysis.th08_priority17_publication_report import build_report
from th08_runtime.priority17_publication_probe import PROBE_SCHEMA


def _event(
    serial: int,
    *,
    manager_frame: int,
    current: int,
    previous: int,
) -> dict[str, object]:
    return {
        "serial": serial,
        "manager_frame": manager_frame,
        "engine_flags": 0x04,
        "raw": current,
        "current": current,
        "previous": previous,
        "replay_frame_counter": serial,
    }


def _batch(
    status: str,
    *,
    previous: int | None,
    observed: int | None,
    events: list[dict[str, object]] | None = None,
    dropped: int = 0,
) -> dict[str, object]:
    return {
        "schema": PROBE_SCHEMA,
        "role": "trace_only_no_action_authority",
        "status": status,
        "previous_serial": previous,
        "observed_serial": observed,
        "events": events or [],
        "dropped_event_count": dropped,
        "error": None,
        "action_authority": False,
    }


def _issue(
    status: str,
    *,
    pre: int | None,
    post: int | None,
) -> dict[str, object]:
    advance = (
        None if pre is None or post is None else (post - pre) & 0xFFFFFFFF
    )
    return {
        "status": status,
        "pre_dispatch_serial": pre,
        "post_dispatch_serial": post,
        "serial_advance_during_dispatch": advance,
        "error": None,
        "action_authority": False,
    }


def _decision(
    *,
    frame: int,
    previous: int,
    target: int,
    transitions: tuple[tuple[int, bool], ...],
    capture: dict[str, object],
    issue: dict[str, object],
    bomb: bool = False,
) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": frame,
        "stage_route_index": 5,
        "mask": target,
        "bomb": bomb,
        "input_dispatch": {
            "previous_mask": previous,
            "target_mask": target,
            "write_required": previous != target,
            "transition_count": len(transitions),
            "transitions": [list(value) for value in transitions],
        },
        "priority17_publication_probe": {
            "role": "trace_only_no_action_authority",
            "installation_status": "installed",
            "capture": capture,
            "issue": issue,
            "action_authority": False,
        },
    }


def _report(rows: list[dict[str, object]]) -> dict[str, object]:
    prefix = [
        {
            "kind": "controller_config",
            "priority17_publication_probe": {
                "schema": PROBE_SCHEMA,
                "status": "installed",
                "action_authority": False,
            },
        },
        {
            "kind": "priority17_publication_probe_baseline",
            **_batch(
                "baseline",
                previous=None,
                observed=10,
            ),
        },
    ]
    suffix = [
        {
            "kind": "summary",
            "termination_reason": "route_complete",
            "hit_count": 0,
        }
    ]
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "trace.jsonl"
        path.write_text(
            "\n".join(json.dumps(row) for row in [*prefix, *rows, *suffix])
            + "\n",
            encoding="utf-8",
        )
        return build_report(path)


class Priority17PublicationReportTests(unittest.TestCase):
    def test_exact_callback_exit_intermediate_and_frozen_manager_witness(
        self,
    ) -> None:
        event_11 = _event(
            11,
            manager_frame=100,
            current=0x61,
            previous=0x65,
        )
        event_12 = _event(
            12,
            manager_frame=100,
            current=0x41,
            previous=0x61,
        )
        report = _report(
            [
                _decision(
                    frame=100,
                    previous=0x65,
                    target=0x41,
                    transitions=((0x04, False), (0x20, False)),
                    capture=_batch(
                        "no_events",
                        previous=10,
                        observed=10,
                    ),
                    issue=_issue("complete", pre=10, post=11),
                ),
                _decision(
                    frame=101,
                    previous=0x41,
                    target=0x41,
                    transitions=(),
                    capture=_batch(
                        "exact",
                        previous=10,
                        observed=12,
                        events=[event_11, event_12],
                    ),
                    issue=_issue("no_write", pre=None, post=None),
                ),
                {
                    "kind": "priority17_publication_probe_final",
                    "phase": "after_key_release",
                    **_batch(
                        "no_events",
                        previous=12,
                        observed=12,
                    ),
                },
            ]
        )

        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["capture"]["callback_events"], 2)
        self.assertEqual(
            report["callback_clock"]["same_manager_frame_publication_edges"],
            1,
        )
        self.assertEqual(
            report["transactions"]["callbacks_during_dispatch"],
            1,
        )
        self.assertEqual(
            report["transactions"][
                "native_intermediate_callback_exit_witnesses"
            ],
            1,
        )
        self.assertEqual(
            report["transactions"]["outcome_counts"],
            {"final_observed_before_trace_end": 1},
        )
        witness = report["retained_native_intermediate_witnesses"][0]
        self.assertEqual(witness["mask_path"], [0x65, 0x61, 0x41])
        self.assertEqual(witness["edge_position"], "1/2")

    def test_later_transaction_ignores_events_before_its_serial_interval(
        self,
    ) -> None:
        report = _report(
            [
                _decision(
                    frame=100,
                    previous=0x00,
                    target=0x01,
                    transitions=((0x01, True),),
                    capture=_batch(
                        "no_events",
                        previous=10,
                        observed=10,
                    ),
                    issue=_issue("complete", pre=10, post=10),
                ),
                _decision(
                    frame=101,
                    previous=0x01,
                    target=0x01,
                    transitions=(),
                    capture=_batch(
                        "exact",
                        previous=10,
                        observed=11,
                        events=[
                            _event(
                                11,
                                manager_frame=101,
                                current=0x01,
                                previous=0x00,
                            )
                        ],
                    ),
                    issue=_issue("no_write", pre=None, post=None),
                ),
                _decision(
                    frame=102,
                    previous=0x01,
                    target=0x00,
                    transitions=((0x01, False),),
                    capture=_batch(
                        "exact",
                        previous=11,
                        observed=12,
                        events=[
                            _event(
                                12,
                                manager_frame=102,
                                current=0x01,
                                previous=0x01,
                            )
                        ],
                    ),
                    issue=_issue("complete", pre=12, post=12),
                ),
                _decision(
                    frame=103,
                    previous=0x00,
                    target=0x00,
                    transitions=(),
                    capture=_batch(
                        "exact",
                        previous=12,
                        observed=13,
                        events=[
                            _event(
                                13,
                                manager_frame=103,
                                current=0x00,
                                previous=0x01,
                            )
                        ],
                    ),
                    issue=_issue("no_write", pre=None, post=None),
                ),
                {
                    "kind": "priority17_publication_probe_final",
                    "phase": "after_key_release",
                    **_batch(
                        "no_events",
                        previous=13,
                        observed=13,
                    ),
                },
            ]
        )

        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(
            report["transactions"]["outcome_counts"],
            {
                "final_observed_before_replacement": 1,
                "final_observed_before_trace_end": 1,
            },
        )

    def test_overflow_is_retained_as_incomplete_not_negative_evidence(
        self,
    ) -> None:
        events = [
            _event(
                serial,
                manager_frame=serial,
                current=0x41,
                previous=0x41,
            )
            for serial in range(19, 51)
        ]
        report = _report(
            [
                _decision(
                    frame=100,
                    previous=0x65,
                    target=0x41,
                    transitions=((0x04, False), (0x20, False)),
                    capture=_batch(
                        "no_events",
                        previous=10,
                        observed=10,
                    ),
                    issue=_issue("complete", pre=10, post=10),
                ),
                _decision(
                    frame=140,
                    previous=0x41,
                    target=0x41,
                    transitions=(),
                    capture=_batch(
                        "overflow_or_trace_truncation",
                        previous=10,
                        observed=50,
                        events=events,
                        dropped=8,
                    ),
                    issue=_issue("no_write", pre=None, post=None),
                ),
                {
                    "kind": "priority17_publication_probe_final",
                    **_batch(
                        "no_events",
                        previous=50,
                        observed=50,
                    ),
                },
            ]
        )

        self.assertFalse(report["integrity"]["passed"])
        self.assertEqual(
            report["capture"]["unknown_or_overflow_batches"],
            1,
        )
        self.assertEqual(
            report["integrity"]["errors"][
                "unknown_or_overflow_capture_batches"
            ],
            1,
        )
        self.assertEqual(
            report["transactions"]["outcome_counts"],
            {"final_observed_after_gap_before_trace_end": 1},
        )
        self.assertEqual(
            report["transactions"]["first_final_publication_step_counts"],
            {},
        )
        self.assertEqual(
            report["retained_nonfinal_or_gapped_witnesses"][0][
                "classification"
            ],
            "final_observed_after_unretained_serial_gap",
        )

    def test_issue_read_error_does_not_masquerade_as_complete_bracket(
        self,
    ) -> None:
        report = _report(
            [
                _decision(
                    frame=100,
                    previous=0x65,
                    target=0x61,
                    transitions=((0x04, False),),
                    capture=_batch(
                        "no_events",
                        previous=10,
                        observed=10,
                    ),
                    issue=_issue("read_error", pre=None, post=None),
                ),
                _decision(
                    frame=101,
                    previous=0x61,
                    target=0x61,
                    transitions=(),
                    capture=_batch(
                        "exact",
                        previous=10,
                        observed=11,
                        events=[
                            _event(
                                11,
                                manager_frame=101,
                                current=0x61,
                                previous=0x65,
                            )
                        ],
                    ),
                    issue=_issue("no_write", pre=None, post=None),
                ),
                {
                    "kind": "priority17_publication_probe_final",
                    **_batch(
                        "no_events",
                        previous=11,
                        observed=11,
                    ),
                },
            ]
        )

        self.assertFalse(report["integrity"]["passed"])
        self.assertEqual(
            report["integrity"]["errors"]["unknown_issue_brackets"], 1
        )

    def test_after_key_release_final_event_is_right_censored(self) -> None:
        report = _report(
            [
                _decision(
                    frame=100,
                    previous=0x65,
                    target=0x61,
                    transitions=((0x04, False),),
                    capture=_batch(
                        "no_events",
                        previous=10,
                        observed=10,
                    ),
                    issue=_issue("complete", pre=10, post=10),
                ),
                {
                    "kind": "priority17_publication_probe_final",
                    "phase": "after_key_release",
                    **_batch(
                        "exact",
                        previous=10,
                        observed=11,
                        events=[
                            _event(
                                11,
                                manager_frame=101,
                                current=0x61,
                                previous=0x65,
                            )
                        ],
                    ),
                },
            ]
        )

        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["transactions"]["final_observed_count"], 0)
        self.assertEqual(
            report["transactions"]["outcome_counts"],
            {"unknown_or_right_censored": 1},
        )


if __name__ == "__main__":
    unittest.main()
