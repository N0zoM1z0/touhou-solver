"""Pure menu plan for the original TH08 Practice Start flow."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PracticeStage:
    key: str
    label: str
    menu_index: int
    route_index: int


@dataclass(frozen=True)
class PracticeDifficulty:
    key: str
    label: str
    menu_index: int


@dataclass(frozen=True)
class MenuTap:
    key: str
    purpose: str
    wait_after_ms: int


PRACTICE_STAGES = (
    PracticeStage("1", "Stage 1", 0, 0),
    PracticeStage("2", "Stage 2", 1, 1),
    PracticeStage("3", "Stage 3", 2, 2),
    PracticeStage("4a", "Stage 4A", 3, 3),
    PracticeStage("4b", "Stage 4B", 4, 4),
    PracticeStage("5", "Stage 5", 5, 5),
    PracticeStage("6a", "Stage 6A", 6, 6),
    PracticeStage("6b", "Stage 6B", 7, 7),
)

PRACTICE_DIFFICULTIES = (
    PracticeDifficulty("easy", "Easy", 0),
    PracticeDifficulty("normal", "Normal", 1),
    PracticeDifficulty("hard", "Hard", 2),
    PracticeDifficulty("lunatic", "Lunatic", 3),
)

_STAGES_BY_KEY = {stage.key: stage for stage in PRACTICE_STAGES}
_DIFFICULTIES_BY_KEY = {
    difficulty.key: difficulty
    for difficulty in PRACTICE_DIFFICULTIES
}
DEFAULT_PRACTICE_DIFFICULTY = _DIFFICULTIES_BY_KEY["lunatic"]


def forward_menu_steps(current: int, target: int, option_count: int) -> int:
    """Return bounded Down presses from a native cursor index to its target."""

    if option_count <= 0:
        raise ValueError("option_count must be positive")
    if not 0 <= current < option_count:
        raise ValueError(f"current index {current} outside 0..{option_count - 1}")
    if not 0 <= target < option_count:
        raise ValueError(f"target index {target} outside 0..{option_count - 1}")
    return (target - current) % option_count


def parse_practice_stage(value: str) -> PracticeStage:
    normalized = value.strip().lower().replace("stage", "").replace("-", "")
    try:
        return _STAGES_BY_KEY[normalized]
    except KeyError as exc:
        choices = ", ".join(stage.key for stage in PRACTICE_STAGES)
        raise ValueError(f"unknown practice stage {value!r}; choices: {choices}") from exc


def parse_practice_difficulty(value: str) -> PracticeDifficulty:
    normalized = value.strip().lower()
    try:
        return _DIFFICULTIES_BY_KEY[normalized]
    except KeyError as exc:
        choices = ", ".join(
            difficulty.key for difficulty in PRACTICE_DIFFICULTIES
        )
        raise ValueError(
            f"unknown practice difficulty {value!r}; choices: {choices}"
        ) from exc


def build_practice_menu_plan(
    stage: PracticeStage,
    *,
    tap_gap_ms: int,
    screen_settle_ms: int,
    difficulty: PracticeDifficulty = DEFAULT_PRACTICE_DIFFICULTY,
) -> tuple[MenuTap, ...]:
    """Stop at the selected stage; the waiting agent sends the final confirm."""

    if tap_gap_ms <= 0 or screen_settle_ms <= 0:
        raise ValueError("menu timing must be positive")
    taps = [
        MenuTap("down", "main-menu Practice Start (2/4)", tap_gap_ms),
        MenuTap("down", "main-menu Practice Start (3/4)", tap_gap_ms),
        MenuTap("down", "main-menu Practice Start (4/4)", tap_gap_ms),
        MenuTap("confirm", "enter Practice Start", screen_settle_ms),
        MenuTap(
            "confirm",
            f"accept native-verified {difficulty.label}",
            screen_settle_ms,
        ),
        MenuTap("right", "team Sakuya/Remilia (2/3)", tap_gap_ms),
        MenuTap("right", "team Sakuya/Remilia (3/3)", tap_gap_ms),
        MenuTap("confirm", "accept native-verified Sakuya/Remilia", screen_settle_ms),
    ]
    for index in range(stage.menu_index):
        wait = screen_settle_ms if index + 1 == stage.menu_index else tap_gap_ms
        taps.append(
            MenuTap(
                "down",
                f"select {stage.label} ({index + 1}/{stage.menu_index})",
                wait,
            )
        )
    return tuple(taps)
