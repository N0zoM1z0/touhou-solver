"""Scene transitions, auto-confirm cadence, and shadow input-clock helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass

from touhou_control.input_clock import (
    SemanticClockEvent,
    SemanticClockObservation,
    SemanticInputClockTracker,
)


SHOT = 0x01
INPUT_CLOCK_SHADOW_ROLE = "shadow_no_input_or_epoch_authority"


@dataclass
class AutoConfirmPulse:
    """Create fresh Z edges after a sustained projectile-free interval."""

    interval_frames: int
    idle_frames: int
    eligible_since: int | None = None
    next_release_frame: int = 0
    released: bool = False

    def apply(
        self,
        *,
        frame: int,
        eligible: bool,
        mask: int,
    ) -> tuple[int, str | None]:
        if self.released:
            self.released = False
            self.next_release_frame = frame + self.interval_frames
            if not eligible:
                self.eligible_since = None
            return mask | SHOT, "press"
        if self.interval_frames <= 0:
            return mask, None
        if not eligible:
            self.eligible_since = None
            return mask, None
        if self.eligible_since is None:
            self.eligible_since = frame
        if (
            frame - self.eligible_since < self.idle_frames
            or frame < self.next_release_frame
        ):
            return mask, None
        self.released = True
        return mask & ~SHOT, "release"

    def frozen_pulse_due(
        self,
        *,
        now: float,
        last_progress: float,
        last_pulse: float,
        eligible: bool,
    ) -> bool:
        if self.interval_frames <= 0 or not eligible:
            return False
        frame_seconds = 1.0 / 60.0
        return (
            now - last_progress >= self.idle_frames * frame_seconds
            and now - last_pulse
            >= max(0.05, self.interval_frames * frame_seconds)
        )

    def mark_full_pulse(self, *, frame: int) -> None:
        self.released = False
        self.next_release_frame = frame + self.interval_frames


def auto_confirm_eligible(
    *,
    player_phase: int,
    bomb_active: bool,
    active_bullets: int,
    active_lasers: int,
) -> bool:
    """Allow residual items; only live hazards make a Z edge unsafe."""

    return (
        player_phase in (0, 3)
        and not bomb_active
        and active_bullets == 0
        and active_lasers == 0
    )


def frozen_auto_confirm_eligible(*, bomb_active: bool) -> bool:
    """A frozen timeline makes hazards inert; only exclude active Bomb."""

    return not bomb_active


def semantic_clock_observation(
    sample: dict[str, object],
    *,
    fallback_frame: int,
    context: object,
) -> SemanticClockObservation:
    player_after = sample.get("player_after")
    input_after = sample.get("input_after")
    position = None
    active_input = None
    if isinstance(player_after, dict):
        x = player_after.get("x")
        y = player_after.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            position = (float(x), float(y))
    if isinstance(input_after, dict):
        current = input_after.get("current")
        if isinstance(current, int):
            active_input = current
    manager_frame = sample.get("manager_frame_after")
    monotonic_ns = sample.get("monotonic_end_ns")
    semantic_active = sample.get("native_manager_clock_blocked")
    return SemanticClockObservation(
        monotonic_ns=(
            int(monotonic_ns)
            if isinstance(monotonic_ns, int)
            else time.perf_counter_ns()
        ),
        physical_frame=(
            int(manager_frame)
            if isinstance(manager_frame, int)
            else fallback_frame
        ),
        semantic_active=(
            semantic_active if isinstance(semantic_active, bool) else None
        ),
        context=context,
        position=position,
        active_input=active_input,
    )


def serialize_semantic_clock_observation(
    observation: SemanticClockObservation,
) -> dict[str, object]:
    return {
        "monotonic_ns": observation.monotonic_ns,
        "physical_frame": observation.physical_frame,
        "semantic_active": observation.semantic_active,
        "context": observation.context,
        "position": observation.position,
        "active_input": observation.active_input,
    }


def serialize_semantic_clock_event(
    event: SemanticClockEvent,
) -> dict[str, object]:
    return {
        "kind": "input_clock_shadow_episode",
        "role": INPUT_CLOCK_SHADOW_ROLE,
        "status": event.kind,
        "episode_id": event.episode_id,
        "frame": event.start.physical_frame,
        "current_frame": event.observation.physical_frame,
        "reason": event.reason,
        "pulse_count": event.pulse_count,
        "duration_ns": event.duration_ns,
        "displacement": event.displacement,
        "start": serialize_semantic_clock_observation(event.start),
        "observation": serialize_semantic_clock_observation(
            event.observation
        ),
    }


def input_clock_message_key(
    sample: dict[str, object],
) -> tuple[object, ...]:
    return (
        sample.get("read_valid"),
        sample.get("frscreen_impl_pointer_after"),
        sample.get("msg_state_after"),
        sample.get("native_manager_clock_blocked"),
        sample.get("scripted_update_freeze_after"),
    )


@dataclass(frozen=True)
class SceneGuardDecision:
    status: str
    current_stage: int
    transition_from_stage: int | None
    expected_stage: int | None
    inactive_seconds: float
    entered: bool = False


@dataclass
class GameplaySceneGuard:
    """Distinguish a stage-resource transition from final scene unload."""

    stage_successors: dict[int, int]
    transition_timeout_seconds: float
    terminal_grace_seconds: float
    last_active_stage: int | None = None
    inactive_since: float | None = None
    transition_from_stage: int | None = None

    def observe(
        self,
        *,
        gameplay_active: bool,
        current_stage: int,
        now: float,
    ) -> SceneGuardDecision:
        if gameplay_active:
            was_inactive = self.inactive_since is not None
            inactive_seconds = (
                now - self.inactive_since
                if self.inactive_since is not None
                else 0.0
            )
            transition_from = self.transition_from_stage
            expected_stage = self.stage_successors.get(transition_from)
            if self.last_active_stage is None or was_inactive:
                self.last_active_stage = current_stage
            self.inactive_since = None
            self.transition_from_stage = None
            return SceneGuardDecision(
                status="resumed" if was_inactive else "active",
                current_stage=current_stage,
                transition_from_stage=transition_from,
                expected_stage=expected_stage,
                inactive_seconds=inactive_seconds,
            )

        entered = self.inactive_since is None
        if entered:
            self.inactive_since = now
            self.transition_from_stage = (
                self.last_active_stage
                if self.last_active_stage is not None
                else current_stage
            )
        assert self.inactive_since is not None
        transition_from = self.transition_from_stage
        expected_stage = self.stage_successors.get(transition_from)
        inactive_seconds = now - self.inactive_since
        if expected_stage is not None:
            status = (
                "stage_transition_timeout"
                if inactive_seconds >= self.transition_timeout_seconds
                else "stage_transition"
            )
        else:
            status = (
                "route_complete"
                if inactive_seconds >= self.terminal_grace_seconds
                else "terminal_unload"
            )
        return SceneGuardDecision(
            status=status,
            current_stage=current_stage,
            transition_from_stage=transition_from,
            expected_stage=expected_stage,
            inactive_seconds=inactive_seconds,
            entered=entered,
        )


@dataclass(frozen=True)
class SceneClockCoordinator:
    auto_confirm: AutoConfirmPulse
    scene_guard: GameplaySceneGuard
    input_clock_tracker: SemanticInputClockTracker | None

    @classmethod
    def create(
        cls,
        *,
        auto_confirm_interval_frames: int,
        auto_confirm_idle_frames: int,
        stage_successors: dict[int, int],
        transition_timeout_seconds: float,
        terminal_grace_seconds: float,
        input_clock_shadow: bool,
    ) -> SceneClockCoordinator:
        return cls(
            auto_confirm=AutoConfirmPulse(
                interval_frames=auto_confirm_interval_frames,
                idle_frames=auto_confirm_idle_frames,
            ),
            scene_guard=GameplaySceneGuard(
                stage_successors=stage_successors,
                transition_timeout_seconds=transition_timeout_seconds,
                terminal_grace_seconds=terminal_grace_seconds,
            ),
            input_clock_tracker=(
                SemanticInputClockTracker()
                if input_clock_shadow
                else None
            ),
        )


__all__ = [
    "AutoConfirmPulse",
    "GameplaySceneGuard",
    "INPUT_CLOCK_SHADOW_ROLE",
    "SceneClockCoordinator",
    "SceneGuardDecision",
    "auto_confirm_eligible",
    "frozen_auto_confirm_eligible",
    "input_clock_message_key",
    "semantic_clock_observation",
    "serialize_semantic_clock_event",
    "serialize_semantic_clock_observation",
]
