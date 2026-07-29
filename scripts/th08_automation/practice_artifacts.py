"""Compact practice-trial artifact publication and baseline selection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from analysis.th08_practice_compare import compare_dossiers
from analysis.th08_practice_dossier import main as build_practice_dossier
from th08_automation.practice_menu import PracticeDifficulty, PracticeStage
from th08_automation.practice_monitor import accepted_practice_termination


@dataclass(frozen=True)
class TrialArtifacts:
    run_id: str
    trace: Path
    summary: Path
    dossier_json: Path
    dossier_markdown: Path
    death_csv: Path
    regressions_json: Path
    comparison_json: Path | None
    run_note: Path
    session_json: Path


def previous_dossier(
    stage: PracticeStage,
    current: Path,
    *,
    runtime_report_dir: Path,
    difficulty_key: str = "lunatic",
) -> Path | None:
    def accepted_session(dossier: Path) -> bool:
        suffix = ".dossier.json"
        if not dossier.name.endswith(suffix):
            return False
        session_path = dossier.with_name(
            dossier.name[: -len(suffix)] + ".session.json"
        )
        try:
            session = json.loads(session_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        if session.get("status") != "completed":
            return False
        if session.get("trial_accepted") is not None:
            return session.get("trial_accepted") is True
        summary = session.get("agent_summary")
        return accepted_practice_termination(
            summary if isinstance(summary, dict) else None
        )

    candidates = sorted(
        runtime_report_dir.glob(
            f"{difficulty_key}_route2_stage{stage.key}_unattended_"
            "*.dossier.json"
        ),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    return next(
        (
            path
            for path in candidates
            if path != current and accepted_session(path)
        ),
        None,
    )


def materialize_artifacts(
    *,
    run_id: str,
    stage: PracticeStage,
    difficulty: PracticeDifficulty,
    trace: Path,
    session_json: Path,
    runtime_report_dir: Path,
    run_note_dir: Path,
) -> TrialArtifacts:
    prefix = runtime_report_dir / run_id
    dossier_json = prefix.with_suffix(".dossier.json")
    death_csv = prefix.with_suffix(".deaths.csv")
    regressions_json = prefix.with_suffix(".regressions.json")
    run_note_dir.mkdir(parents=True, exist_ok=True)
    run_note = run_note_dir / f"{run_id}.md"
    dossier_markdown = run_note
    build_practice_dossier(
        [
            "--run-id",
            run_id,
            "--trace",
            str(trace),
            "--json-output",
            str(dossier_json),
            "--markdown-output",
            str(dossier_markdown),
            "--death-csv",
            str(death_csv),
            "--regression-output",
            str(regressions_json),
        ]
    )
    comparison_json = None
    baseline = previous_dossier(
        stage,
        dossier_json,
        runtime_report_dir=runtime_report_dir,
        difficulty_key=difficulty.key,
    )
    if baseline is not None:
        comparison_json = prefix.with_suffix(".comparison.json")
        before = json.loads(baseline.read_text(encoding="utf-8"))
        after = json.loads(dossier_json.read_text(encoding="utf-8"))
        comparison_json.write_text(
            json.dumps(
                compare_dossiers(before, after),
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )
    return TrialArtifacts(
        run_id=run_id,
        trace=trace,
        summary=trace.with_suffix(".summary.json"),
        dossier_json=dossier_json,
        dossier_markdown=dossier_markdown,
        death_csv=death_csv,
        regressions_json=regressions_json,
        comparison_json=comparison_json,
        run_note=run_note,
        session_json=session_json,
    )
