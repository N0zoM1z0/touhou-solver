"""Canonical compact records for the G3 capsule report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from analysis.belief_upper_certification_audit import Root
from touhou_control.partial_survival_witness import StationaryPolicyWitness


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def label_record(label) -> dict[str, object]:
    return {
        "guaranteed_frames": int(label.guaranteed_frames),
        "bottleneck_margin_hex": float(label.bottleneck_margin).hex(),
    }


def root_record(root: Root) -> dict[str, object]:
    return {
        "decision_frame": root.decision_frame,
        "query_frame": root.query_frame,
        "source_frame": root.source_frame,
        "capsule": root.capsule,
        "spell_id": root.spell_id,
        "x_hex": float(root.x).hex(),
        "y_hex": float(root.y).hex(),
        "observed_action": root.observed_action,
        "pending": (
            None
            if root.pending is None
            else {
                "action": root.pending.action,
                "remaining_frames": root.pending.remaining_frames,
            }
        ),
        "delay_frames": root.delay_frames,
        "nominal_delay": root.nominal_delay,
        "trace_state_viable": root.trace_state_viable,
        "issued_action": root.issued_action,
    }


def witness_record(
    witness: StationaryPolicyWitness,
) -> dict[str, object]:
    return {
        "root_action": witness.root_action,
        "continuation_action": witness.continuation_action,
        "label": label_record(witness.label),
        "policy_digest": witness.policy_digest,
        "witness_digest": witness.witness_digest,
        "evaluated_state_count": witness.evaluated_state_count,
        "worst_branch": [
            {
                **asdict(step),
                "prefix_bottleneck_margin": float(
                    step.prefix_bottleneck_margin
                ).hex(),
                "state_label": label_record(step.state_label),
                "successor_label": (
                    None
                    if step.successor_label is None
                    else label_record(step.successor_label)
                ),
            }
            for step in witness.worst_branch
        ],
    }
