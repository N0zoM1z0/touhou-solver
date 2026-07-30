"""TH08 enemy contact and shot-damage gates conditioned on player mode.

The original ``LocalPipelineRoot`` APIs remain as a restricted atomic-pickup
baseline.  CE-0193 rejects that abstraction for multi-key physical writes.
The ordered-input decision APIs below preserve per-key transaction prefixes
and the native priority-9-before-priority-17 publication order.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable, Mapping

from th08_option_model import Route2FocusState
from touhou_control.local_pipeline_oracle import (
    LocalPipelineBranch,
    LocalPipelineRoot,
    enumerate_local_pipeline_branches,
)
from touhou_control.ordered_input_transaction_oracle import (
    AsynchronousOrderedInputIssueBranch,
    OrderedInputBelief,
    OrderedInputExactState,
    OrderedInputIssueBranch,
    advance_ordered_input_state,
    issue_ordered_input_belief_asynchronously,
    issue_ordered_input_belief,
)

ENEMY_ACTIVE_FLAG = 0x00000001
ENEMY_CONTACT_ENABLED_FLAG = 0x00000004
ENEMY_MANAGER_BLOCKING_FLAGS = 0x00000830
ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG = 0x00000040
ENEMY_SECONDARY_CHARACTER_SYNC_FLAG = 0x00000100
ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG = 0x00000800
BOMB_INPUT_BIT = 0x02
FOCUS_INPUT_BIT = 0x04

Route2EnemyModeStateKey = tuple[int, bool, int]


@dataclass(frozen=True)
class EnemyModeProjection:
    """One enemy's native flag gates after the priority-11 mode sync."""

    raw_flags: int
    projected_flags: int
    secondary_character_synchronized: bool
    manager_gate_open: bool
    contact_eligible: bool
    player_shot_damage_eligible: bool


@dataclass(frozen=True)
class Route2EnemyModeBody:
    """One predicted enemy identity and flags at a contact-gate epoch."""

    identity: int
    raw_flags: int

    def __post_init__(self) -> None:
        if type(self.identity) is not int or self.identity < 0:
            raise ValueError("enemy identity must be a nonnegative integer")
        if type(self.raw_flags) is not int or not 0 <= self.raw_flags <= 0xFFFFFFFF:
            raise ValueError("enemy flags must fit in one unsigned 32-bit word")


@dataclass(frozen=True)
class Route2ModeBodyProjection:
    """One body after the priority-11 secondary-character synchronization."""

    identity: int
    projection: EnemyModeProjection


@dataclass(frozen=True)
class Route2ModeHazardFrame:
    """Mode-conditioned body gates for one physical player/enemy update."""

    physical_step: int
    active_action: str
    active_mask: int
    mode_state_before: Route2EnemyModeStateKey
    mode_state_after: Route2EnemyModeStateKey
    body_projections: tuple[Route2ModeBodyProjection, ...]
    contact_body_ids: tuple[int, ...]
    player_shot_damage_body_ids: tuple[int, ...]


@dataclass(frozen=True)
class Route2ModeHazardBranch:
    """One exact hidden pickup history with its causal mode/body sequence."""

    pipeline_branch: LocalPipelineBranch
    frames: tuple[Route2ModeHazardFrame, ...]


@dataclass(frozen=True)
class Route2ModeObservationKey:
    """Observable mode augmentation for one future controller decision."""

    base_observation: Hashable
    physical_step: int
    active_action: str
    held_desired_action: str
    mode_state: Route2EnemyModeStateKey


@dataclass(frozen=True)
class Route2ModeObservationClass:
    """Hidden pickup branches merged before the next maximization."""

    key: Route2ModeObservationKey
    hidden_branches: tuple[Route2ModeHazardBranch, ...]


@dataclass(frozen=True)
class Route2ModeDecisionBranch:
    """One exact pickup/cadence branch ending at a controller observation."""

    cadence_frames: int
    hazard_branch: Route2ModeHazardBranch
    successor_pipeline_root: LocalPipelineRoot
    successor_mode_state: Route2EnemyModeStateKey


@dataclass(frozen=True)
class Route2ModeDecisionObservationClass:
    """One non-clairvoyant successor information set."""

    key: Route2ModeObservationKey
    successor_pipeline_root: LocalPipelineRoot
    hidden_branches: tuple[Route2ModeDecisionBranch, ...]


@dataclass(frozen=True)
class Route2OrderedModeHazardBranch:
    """One exact ordered-input publication and causal mode/body history."""

    issue_branch: OrderedInputIssueBranch
    frames: tuple[Route2ModeHazardFrame, ...]
    input_states_after_publication: tuple[OrderedInputExactState, ...]


@dataclass(frozen=True)
class Route2OrderedModeDecisionBranch:
    """One ordered-input/cadence branch at the next controller observation."""

    cadence_frames: int
    hazard_branch: Route2OrderedModeHazardBranch
    successor_input_state: OrderedInputExactState
    successor_mode_state: Route2EnemyModeStateKey


@dataclass(frozen=True)
class Route2OrderedModeObservationKey:
    """Observed actuator masks and native mode fields after one cadence."""

    base_observation: Hashable
    physical_step: int
    active_mask: int
    held_desired_mask: int
    mode_state: Route2EnemyModeStateKey


@dataclass(frozen=True)
class Route2OrderedModeDecisionObservationClass:
    """Hidden ordered transaction states merged before the next choice."""

    key: Route2OrderedModeObservationKey
    successor_input_belief: OrderedInputBelief
    hidden_branches: tuple[Route2OrderedModeDecisionBranch, ...]


@dataclass(frozen=True)
class Route2AsyncOrderedModeHazardBranch:
    """One asynchronous issue/cadence history in native callback order."""

    issue_branch: AsynchronousOrderedInputIssueBranch
    frames: tuple[Route2ModeHazardFrame, ...]
    post_dispatch_input_states_after_publication: tuple[
        OrderedInputExactState, ...
    ]


@dataclass(frozen=True)
class Route2AsyncOrderedModeDecisionBranch:
    """One asynchronous issue branch at the next controller observation."""

    cadence_frames: int
    hazard_branch: Route2AsyncOrderedModeHazardBranch
    successor_input_state: OrderedInputExactState
    successor_mode_state: Route2EnemyModeStateKey


@dataclass(frozen=True)
class Route2AsyncOrderedModeDecisionObservationClass:
    """One non-clairvoyant asynchronous successor information set."""

    key: Route2OrderedModeObservationKey
    successor_input_belief: OrderedInputBelief
    hidden_branches: tuple[Route2AsyncOrderedModeDecisionBranch, ...]


@dataclass(frozen=True)
class _Route2OrderedPartial:
    mode_state: Route2EnemyModeStateKey
    input_state: OrderedInputExactState
    frames: tuple[Route2ModeHazardFrame, ...]
    input_states_after_publication: tuple[OrderedInputExactState, ...]


def route2_enemy_mode_state_key(
    state: Route2FocusState,
) -> Route2EnemyModeStateKey:
    """Return the player fields that determine all future enemy-mode gates.

    Option positions and timers do not affect the enemy bit-0x800 sync.  The
    exact focus byte is retained because the native initializer's value 2 and
    the steady focused value 1 have different next-update behavior.
    """

    return (
        state.focus_logic_value,
        state.remilia_character_active,
        state.transition_counter,
    )


def _validate_route2_enemy_mode_state_key(
    state: Route2EnemyModeStateKey,
) -> Route2EnemyModeStateKey:
    if (
        not isinstance(state, tuple)
        or len(state) != 3
        or type(state[0]) is not int
        or not 0 <= state[0] <= 0xFF
        or type(state[1]) is not bool
        or type(state[2]) is not int
        or state[2] < 0
    ):
        raise ValueError(
            "mode state must be (u8 focus, bool secondary, nonnegative counter)"
        )
    return state


def step_route2_enemy_mode_state(
    state: Route2EnemyModeStateKey,
    *,
    focused: bool,
) -> Route2EnemyModeStateKey:
    """Apply the priority-9 player mode transition for one physical update."""

    if type(focused) is not bool:
        raise ValueError("focused must be a Boolean")
    focus_value, secondary_active, counter = _validate_route2_enemy_mode_state_key(
        state
    )
    if focused:
        counter = counter + 1 if focus_value == 1 else 0
        if counter >= 7:
            secondary_active = True
        focus_value = 1
    else:
        counter = 0 if focus_value != 0 else counter + 1
        if counter >= 7:
            secondary_active = False
        focus_value = 0
    return focus_value, secondary_active, counter


def project_enemy_mode(
    flags: int,
    *,
    secondary_character_active: bool,
) -> EnemyModeProjection:
    """Apply the shipped player-mode sync and separate the two native gates.

    The enemy manager calls the sync helper only for active enemies carrying
    bit 0x100.  That helper mirrors ``player[+5] & 1`` into enemy bit 0x800.
    The later manager gate excludes 0x10, 0x20, and 0x800 before evaluating
    contact bit 0x04 and player-shot-damage bit 0x40 independently.
    """

    if not 0 <= flags <= 0xFFFFFFFF:
        raise ValueError("enemy flags must fit in one unsigned 32-bit word")

    synchronized = bool(
        flags & ENEMY_ACTIVE_FLAG and flags & ENEMY_SECONDARY_CHARACTER_SYNC_FLAG
    )
    projected = flags
    if synchronized:
        if secondary_character_active:
            projected |= ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG
        else:
            projected &= ~ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG

    manager_gate_open = bool(
        projected & ENEMY_ACTIVE_FLAG and not projected & ENEMY_MANAGER_BLOCKING_FLAGS
    )
    return EnemyModeProjection(
        raw_flags=flags,
        projected_flags=projected,
        secondary_character_synchronized=synchronized,
        manager_gate_open=manager_gate_open,
        contact_eligible=bool(
            manager_gate_open and projected & ENEMY_CONTACT_ENABLED_FLAG
        ),
        player_shot_damage_eligible=bool(
            manager_gate_open and projected & ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG
        ),
    )


def project_route2_enemy_mode(
    flags: int,
    *,
    focus_state: Route2FocusState,
) -> EnemyModeProjection:
    """Project one enemy against the current route-2 delayed character byte."""

    return project_enemy_mode(
        flags,
        secondary_character_active=focus_state.remilia_character_active,
    )


def project_route2_mode_pipeline_branches(
    *,
    pipeline_root: LocalPipelineRoot,
    selected_action: str,
    action_masks: Mapping[str, int],
    delay_frames: tuple[int, ...],
    initial_mode_state: Route2EnemyModeStateKey,
    enemy_flag_frames: tuple[tuple[Route2EnemyModeBody, ...], ...],
) -> tuple[Route2ModeHazardBranch, ...]:
    """Compose restricted atomic pickup histories with mode/body updates.

    ``enemy_flag_frames`` is the exogenous predicted body/flag schedule at
    each contact-gate epoch.  For active bit-0x100 bodies, bit 0x800 is
    overwritten by the post-player mode state exactly as in the shipped
    priority-11 callback.  This function does not project positions, births,
    ECL flags, damage, cadence, or future controller decisions.

    This API is retained for old differential fixtures.  It treats one
    complete-mask issue as one atomic old/final transition and therefore has
    no physical authority for multi-key writes after CE-0193.  Use
    ``project_route2_ordered_mode_decision_branches`` for the corrected
    ordered transaction primitive.
    """

    state = _validate_route2_enemy_mode_state_key(initial_mode_state)
    if not enemy_flag_frames:
        raise ValueError("mode projection requires a nonempty frame schedule")
    normalized_masks: dict[str, int] = {}
    for action, mask in action_masks.items():
        if not action or type(mask) is not int or not 0 <= mask <= 0xFFFFFFFF:
            raise ValueError("action masks require nonempty names and u32 masks")
        if mask & BOMB_INPUT_BIT:
            raise ValueError("route-2 mode projection requires hard no-Bomb masks")
        normalized_masks[action] = mask
    if not normalized_masks:
        raise ValueError("at least one action mask is required")
    required_actions = {
        pipeline_root.active_action,
        pipeline_root.held_desired_action,
        selected_action,
    }
    if pipeline_root.pending_action is not None:
        required_actions.add(pipeline_root.pending_action)
    missing_actions = required_actions - normalized_masks.keys()
    if missing_actions:
        raise ValueError(f"missing complete action masks: {sorted(missing_actions)}")
    for frame in enemy_flag_frames:
        identities = tuple(body.identity for body in frame)
        if len(set(identities)) != len(identities):
            raise ValueError("enemy identities must be unique within one frame")

    pipeline_branches = enumerate_local_pipeline_branches(
        root=pipeline_root,
        selected_action=selected_action,
        delay_frames=delay_frames,
        horizon_frames=len(enemy_flag_frames),
    )
    result: list[Route2ModeHazardBranch] = []
    for pipeline_branch in pipeline_branches:
        mode_state = state
        projected_frames: list[Route2ModeHazardFrame] = []
        for physical_step, (active_action, bodies) in enumerate(
            zip(
                pipeline_branch.active_actions,
                enemy_flag_frames,
                strict=True,
            ),
            start=1,
        ):
            try:
                active_mask = normalized_masks[active_action]
            except KeyError as error:
                raise ValueError(
                    f"active action {active_action!r} has no complete mask"
                ) from error
            before = mode_state
            mode_state = step_route2_enemy_mode_state(
                before,
                focused=bool(active_mask & FOCUS_INPUT_BIT),
            )
            projections = tuple(
                Route2ModeBodyProjection(
                    identity=body.identity,
                    projection=project_enemy_mode(
                        body.raw_flags,
                        secondary_character_active=mode_state[1],
                    ),
                )
                for body in bodies
            )
            projected_frames.append(
                Route2ModeHazardFrame(
                    physical_step=physical_step,
                    active_action=active_action,
                    active_mask=active_mask,
                    mode_state_before=before,
                    mode_state_after=mode_state,
                    body_projections=projections,
                    contact_body_ids=tuple(
                        body.identity
                        for body in projections
                        if body.projection.contact_eligible
                    ),
                    player_shot_damage_body_ids=tuple(
                        body.identity
                        for body in projections
                        if body.projection.player_shot_damage_eligible
                    ),
                )
            )
        result.append(
            Route2ModeHazardBranch(
                pipeline_branch=pipeline_branch,
                frames=tuple(projected_frames),
            )
        )
    return tuple(result)


def _successor_pipeline_root(
    *,
    root: LocalPipelineRoot,
    branch: LocalPipelineBranch,
    physical_steps: int,
) -> LocalPipelineRoot:
    if physical_steps <= 0:
        raise ValueError("physical steps must be positive")
    selected = branch.selected_action
    if not branch.write_required:
        if (
            root.pending_action is not None
            and branch.older_remaining is not None
            and branch.older_remaining <= physical_steps
        ):
            return LocalPipelineRoot(
                active_action=root.pending_action,
                held_desired_action=root.pending_action,
            )
        if root.pending_action is None:
            return LocalPipelineRoot(
                active_action=root.active_action,
                held_desired_action=root.active_action,
            )
        assert branch.older_remaining is not None
        return LocalPipelineRoot(
            active_action=root.active_action,
            held_desired_action=root.pending_action,
            pending_action=root.pending_action,
            remaining_delay_support=(branch.older_remaining - physical_steps,),
        )

    assert branch.new_delay is not None
    if branch.new_delay <= physical_steps:
        return LocalPipelineRoot(
            active_action=selected,
            held_desired_action=selected,
        )
    active_action = root.active_action
    if (
        root.pending_action is not None
        and branch.older_remaining is not None
        and branch.older_remaining <= physical_steps
    ):
        active_action = root.pending_action
    if active_action == selected:
        return LocalPipelineRoot(
            active_action=selected,
            held_desired_action=selected,
        )
    return LocalPipelineRoot(
        active_action=active_action,
        held_desired_action=selected,
        pending_action=selected,
        remaining_delay_support=(branch.new_delay - physical_steps,),
    )


def project_route2_mode_decision_branches(
    *,
    pipeline_root: LocalPipelineRoot,
    selected_action: str,
    action_masks: Mapping[str, int],
    delay_frames: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    initial_mode_state: Route2EnemyModeStateKey,
    enemy_flag_frames: tuple[tuple[Route2EnemyModeBody, ...], ...],
) -> tuple[Route2ModeDecisionBranch, ...]:
    """Enumerate the restricted atomic recursive-cadence primitive.

    Each returned branch ends at one possible next controller observation.
    Calling this function again with an observation class's merged successor
    root is the recursive construction; cadence is sampled again on every
    call.  The body schedule must cover the largest cadence branch.  CE-0193
    rejects this API for physical multi-key pickup authority; it remains an
    explicit baseline for historical scalar/native fixtures.
    """

    if (
        not decision_frame_support
        or tuple(sorted(set(decision_frame_support))) != decision_frame_support
        or decision_frame_support[0] <= 0
    ):
        raise ValueError("decision-frame support must be sorted, unique, and positive")
    if len(enemy_flag_frames) < decision_frame_support[-1]:
        raise ValueError("body schedule does not cover cadence support")

    branches: list[Route2ModeDecisionBranch] = []
    for cadence_frames in decision_frame_support:
        hazard_branches = project_route2_mode_pipeline_branches(
            pipeline_root=pipeline_root,
            selected_action=selected_action,
            action_masks=action_masks,
            delay_frames=delay_frames,
            initial_mode_state=initial_mode_state,
            enemy_flag_frames=enemy_flag_frames[:cadence_frames],
        )
        for hazard_branch in hazard_branches:
            branches.append(
                Route2ModeDecisionBranch(
                    cadence_frames=cadence_frames,
                    hazard_branch=hazard_branch,
                    successor_pipeline_root=_successor_pipeline_root(
                        root=pipeline_root,
                        branch=hazard_branch.pipeline_branch,
                        physical_steps=cadence_frames,
                    ),
                    successor_mode_state=(hazard_branch.frames[-1].mode_state_after),
                )
            )
    return tuple(branches)


def _ordered_action_masks(
    action_masks: Mapping[str, int],
    *,
    supported_mask: int,
) -> tuple[dict[str, int], dict[int, str]]:
    if type(supported_mask) is not int or not 0 <= supported_mask <= 0xFFFF:
        raise ValueError("supported input mask must fit in one u16 word")
    normalized: dict[str, int] = {}
    inverse: dict[int, str] = {}
    for action, mask in action_masks.items():
        if not action or type(mask) is not int or not 0 <= mask <= 0xFFFF:
            raise ValueError("action masks require nonempty names and u16 masks")
        if mask & ~supported_mask:
            raise ValueError(f"action {action!r} contains unsupported input bits")
        if mask & BOMB_INPUT_BIT:
            raise ValueError("route-2 mode projection requires hard no-Bomb masks")
        if mask in inverse:
            raise ValueError("ordered complete-mask action mapping must be injective")
        normalized[action] = mask
        inverse[mask] = action
    if not normalized:
        raise ValueError("at least one action mask is required")
    return normalized, inverse


def _validate_enemy_flag_frames(
    enemy_flag_frames: tuple[tuple[Route2EnemyModeBody, ...], ...],
) -> None:
    for frame in enemy_flag_frames:
        identities = tuple(body.identity for body in frame)
        if len(set(identities)) != len(identities):
            raise ValueError("enemy identities must be unique within one frame")


def _ordered_mode_hazard_frame(
    *,
    physical_step: int,
    active_action: str,
    active_mask: int,
    mode_state: Route2EnemyModeStateKey,
    bodies: tuple[Route2EnemyModeBody, ...],
) -> tuple[Route2ModeHazardFrame, Route2EnemyModeStateKey]:
    after = step_route2_enemy_mode_state(
        mode_state,
        focused=bool(active_mask & FOCUS_INPUT_BIT),
    )
    projections = tuple(
        Route2ModeBodyProjection(
            identity=body.identity,
            projection=project_enemy_mode(
                body.raw_flags,
                secondary_character_active=after[1],
            ),
        )
        for body in bodies
    )
    return (
        Route2ModeHazardFrame(
            physical_step=physical_step,
            active_action=active_action,
            active_mask=active_mask,
            mode_state_before=mode_state,
            mode_state_after=after,
            body_projections=projections,
            contact_body_ids=tuple(
                body.identity
                for body in projections
                if body.projection.contact_eligible
            ),
            player_shot_damage_body_ids=tuple(
                body.identity
                for body in projections
                if body.projection.player_shot_damage_eligible
            ),
        ),
        after,
    )


def project_route2_ordered_mode_decision_branches(
    *,
    input_belief: OrderedInputBelief,
    selected_action: str,
    action_masks: Mapping[str, int],
    supported_mask: int,
    delay_frames: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    initial_mode_state: Route2EnemyModeStateKey,
    enemy_flag_frames: tuple[tuple[Route2EnemyModeBody, ...], ...],
) -> tuple[Route2OrderedModeDecisionBranch, ...]:
    """Compose ordered input pickup with priority-9/11 mode/body semantics.

    One controller choice is issued uniformly across the input belief.
    During each physical update, priority 9 consumes the currently published
    active mask and advances the delayed player mode; priority 11 projects
    the enemy body gates; only then does the priority-17 publication boundary
    expose one nature-selected ordered transaction prefix for the next
    update.  The body schedule is exogenous and must cover every cadence.

    Nature may stutter or advance through any non-final ordered prefix until
    the declared final-completion deadline.  Because the exact Win32
    queue/poll phase and its mapping to physical frames remain unbounded, this
    primitive is conservative offline evidence and has no live authority.
    """

    state = _validate_route2_enemy_mode_state_key(initial_mode_state)
    if (
        not decision_frame_support
        or tuple(sorted(set(decision_frame_support))) != decision_frame_support
        or decision_frame_support[0] <= 0
    ):
        raise ValueError("decision-frame support must be sorted, unique, and positive")
    if len(enemy_flag_frames) < decision_frame_support[-1]:
        raise ValueError("body schedule does not cover cadence support")
    _validate_enemy_flag_frames(enemy_flag_frames)
    normalized_masks, inverse_masks = _ordered_action_masks(
        action_masks,
        supported_mask=supported_mask,
    )
    try:
        selected_mask = normalized_masks[selected_action]
    except KeyError as error:
        raise ValueError(
            f"missing selected action mask: {selected_action!r}"
        ) from error

    issue_branches = issue_ordered_input_belief(
        input_belief,
        selected_mask=selected_mask,
        delay_support=delay_frames,
        supported_mask=supported_mask,
        forbidden_mask=BOMB_INPUT_BIT,
    )
    for issue_branch in issue_branches:
        successor = issue_branch.successor_state
        required_masks = (
            issue_branch.source_state.active_mask,
            issue_branch.source_state.held_desired_mask,
            *issue_branch.source_state.queued_masks,
            successor.active_mask,
            successor.held_desired_mask,
            *successor.queued_masks,
        )
        missing_masks = tuple(
            sorted({mask for mask in required_masks if mask not in inverse_masks})
        )
        if missing_masks:
            formatted = ", ".join(f"{mask:#06x}" for mask in missing_masks)
            raise ValueError(
                "ordered transaction reached complete masks without action "
                f"identities: {formatted}"
            )
    results: list[Route2OrderedModeDecisionBranch] = []
    for cadence_frames in decision_frame_support:
        for issue_branch in issue_branches:
            partials = (
                _Route2OrderedPartial(
                    mode_state=state,
                    input_state=issue_branch.successor_state,
                    frames=(),
                    input_states_after_publication=(),
                ),
            )
            for physical_step in range(1, cadence_frames + 1):
                next_partials: list[_Route2OrderedPartial] = []
                bodies = enemy_flag_frames[physical_step - 1]
                for partial in partials:
                    try:
                        active_action = inverse_masks[partial.input_state.active_mask]
                    except KeyError as error:
                        raise ValueError(
                            "ordered transaction reached a complete mask without "
                            f"an action identity: "
                            f"{partial.input_state.active_mask:#06x}"
                        ) from error
                    frame, next_mode_state = _ordered_mode_hazard_frame(
                        physical_step=physical_step,
                        active_action=active_action,
                        active_mask=partial.input_state.active_mask,
                        mode_state=partial.mode_state,
                        bodies=bodies,
                    )
                    for next_input_state in advance_ordered_input_state(
                        partial.input_state
                    ):
                        next_partials.append(
                            _Route2OrderedPartial(
                                mode_state=next_mode_state,
                                input_state=next_input_state,
                                frames=partial.frames + (frame,),
                                input_states_after_publication=(
                                    partial.input_states_after_publication
                                    + (next_input_state,)
                                ),
                            )
                        )
                partials = tuple(next_partials)

            for partial in partials:
                hazard_branch = Route2OrderedModeHazardBranch(
                    issue_branch=issue_branch,
                    frames=partial.frames,
                    input_states_after_publication=(
                        partial.input_states_after_publication
                    ),
                )
                results.append(
                    Route2OrderedModeDecisionBranch(
                        cadence_frames=cadence_frames,
                        hazard_branch=hazard_branch,
                        successor_input_state=partial.input_state,
                        successor_mode_state=partial.mode_state,
                    )
                )
    return tuple(results)


def project_route2_async_ordered_mode_decision_branches(
    *,
    input_belief: OrderedInputBelief,
    selected_action: str,
    action_masks: Mapping[str, int],
    supported_mask: int,
    post_dispatch_delay_frames: tuple[int, ...],
    dispatch_callback_count_support: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    initial_mode_state: Route2EnemyModeStateKey,
    enemy_flag_frames: tuple[tuple[Route2EnemyModeBody, ...], ...],
) -> tuple[Route2AsyncOrderedModeDecisionBranch, ...]:
    """Compose callbacks during issue with priority-9/11/17 physical order.

    Dispatch callbacks consume physical cadence steps. On each such step,
    priority 9 consumes the active mask recorded before that callback,
    priority 11 projects body gates, and only then does priority 17 publish
    the issue branch's monotone path mask. Remaining cadence steps begin from
    the exact post-dispatch actuator state.

    Independent callback-count/cadence supports are conservatively combined
    only when the issue callback count fits within the total cadence. Their
    physical joint automaton and finite support authority remain open.
    """

    state = _validate_route2_enemy_mode_state_key(initial_mode_state)
    if (
        not decision_frame_support
        or tuple(sorted(set(decision_frame_support))) != decision_frame_support
        or decision_frame_support[0] <= 0
    ):
        raise ValueError(
            "decision-frame support must be sorted, unique, and positive"
        )
    if len(enemy_flag_frames) < decision_frame_support[-1]:
        raise ValueError("body schedule does not cover cadence support")
    _validate_enemy_flag_frames(enemy_flag_frames)
    normalized_masks, inverse_masks = _ordered_action_masks(
        action_masks,
        supported_mask=supported_mask,
    )
    try:
        selected_mask = normalized_masks[selected_action]
    except KeyError as error:
        raise ValueError(
            f"missing selected action mask: {selected_action!r}"
        ) from error

    issue_branches = issue_ordered_input_belief_asynchronously(
        input_belief,
        selected_mask=selected_mask,
        post_dispatch_delay_support=post_dispatch_delay_frames,
        dispatch_callback_count_support=dispatch_callback_count_support,
        supported_mask=supported_mask,
        forbidden_mask=BOMB_INPUT_BIT,
    )
    for issue_branch in issue_branches:
        source = issue_branch.source_state
        successor = issue_branch.successor_state
        required_masks = (
            source.active_mask,
            source.held_desired_mask,
            *source.queued_masks,
            *issue_branch.active_masks_consumed_during_dispatch,
            *issue_branch.publications_during_dispatch,
            successor.active_mask,
            successor.held_desired_mask,
            *successor.queued_masks,
        )
        missing_masks = tuple(
            sorted({mask for mask in required_masks if mask not in inverse_masks})
        )
        if missing_masks:
            formatted = ", ".join(
                f"{mask:#06x}" for mask in missing_masks
            )
            raise ValueError(
                "asynchronous ordered transaction reached complete masks "
                f"without action identities: {formatted}"
            )

    results: list[Route2AsyncOrderedModeDecisionBranch] = []
    for cadence_frames in decision_frame_support:
        for issue_branch in issue_branches:
            dispatch_frames = issue_branch.dispatch_callback_count
            if dispatch_frames > cadence_frames:
                continue
            mode_state = state
            frames: tuple[Route2ModeHazardFrame, ...] = ()
            for offset, active_mask in enumerate(
                issue_branch.active_masks_consumed_during_dispatch,
                start=1,
            ):
                frame, mode_state = _ordered_mode_hazard_frame(
                    physical_step=offset,
                    active_action=inverse_masks[active_mask],
                    active_mask=active_mask,
                    mode_state=mode_state,
                    bodies=enemy_flag_frames[offset - 1],
                )
                frames += (frame,)

            partials = (
                _Route2OrderedPartial(
                    mode_state=mode_state,
                    input_state=issue_branch.successor_state,
                    frames=frames,
                    input_states_after_publication=(),
                ),
            )
            for physical_step in range(
                dispatch_frames + 1,
                cadence_frames + 1,
            ):
                next_partials: list[_Route2OrderedPartial] = []
                bodies = enemy_flag_frames[physical_step - 1]
                for partial in partials:
                    active_mask = partial.input_state.active_mask
                    frame, next_mode_state = _ordered_mode_hazard_frame(
                        physical_step=physical_step,
                        active_action=inverse_masks[active_mask],
                        active_mask=active_mask,
                        mode_state=partial.mode_state,
                        bodies=bodies,
                    )
                    for next_input_state in advance_ordered_input_state(
                        partial.input_state
                    ):
                        next_partials.append(
                            _Route2OrderedPartial(
                                mode_state=next_mode_state,
                                input_state=next_input_state,
                                frames=partial.frames + (frame,),
                                input_states_after_publication=(
                                    partial.input_states_after_publication
                                    + (next_input_state,)
                                ),
                            )
                        )
                partials = tuple(next_partials)

            for partial in partials:
                hazard_branch = Route2AsyncOrderedModeHazardBranch(
                    issue_branch=issue_branch,
                    frames=partial.frames,
                    post_dispatch_input_states_after_publication=(
                        partial.input_states_after_publication
                    ),
                )
                results.append(
                    Route2AsyncOrderedModeDecisionBranch(
                        cadence_frames=cadence_frames,
                        hazard_branch=hazard_branch,
                        successor_input_state=partial.input_state,
                        successor_mode_state=partial.mode_state,
                    )
                )
    if not results:
        raise ValueError(
            "asynchronous issue/cadence supports have no compatible history"
        )
    return tuple(results)


def merge_route2_async_ordered_mode_decision_observation_classes(
    branches: tuple[Route2AsyncOrderedModeDecisionBranch, ...],
    *,
    base_observation: Callable[
        [Route2AsyncOrderedModeDecisionBranch, Route2ModeHazardFrame],
        Hashable,
    ],
) -> tuple[Route2AsyncOrderedModeDecisionObservationClass, ...]:
    """Merge asynchronous hidden histories by the full next observation."""

    if not branches:
        raise ValueError(
            "at least one asynchronous ordered decision branch is required"
        )
    grouped: dict[
        Route2OrderedModeObservationKey,
        list[Route2AsyncOrderedModeDecisionBranch],
    ] = {}
    for branch in branches:
        frame = branch.hazard_branch.frames[-1]
        base = base_observation(branch, frame)
        try:
            hash(base)
        except TypeError as error:
            raise ValueError("base observation must be hashable") from error
        successor = branch.successor_input_state
        key = Route2OrderedModeObservationKey(
            base_observation=base,
            physical_step=branch.cadence_frames,
            active_mask=successor.active_mask,
            held_desired_mask=successor.held_desired_mask,
            mode_state=branch.successor_mode_state,
        )
        grouped.setdefault(key, []).append(branch)

    return tuple(
        Route2AsyncOrderedModeDecisionObservationClass(
            key=key,
            successor_input_belief=OrderedInputBelief.from_states(
                branch.successor_input_state for branch in hidden
            ),
            hidden_branches=tuple(hidden),
        )
        for key, hidden in grouped.items()
    )


def merge_route2_ordered_mode_decision_observation_classes(
    branches: tuple[Route2OrderedModeDecisionBranch, ...],
    *,
    base_observation: Callable[
        [Route2OrderedModeDecisionBranch, Route2ModeHazardFrame],
        Hashable,
    ],
) -> tuple[Route2OrderedModeDecisionObservationClass, ...]:
    """Merge hidden queue/deadline states by the full next observation."""

    if not branches:
        raise ValueError("at least one ordered decision branch is required")
    grouped: dict[
        Route2OrderedModeObservationKey,
        list[Route2OrderedModeDecisionBranch],
    ] = {}
    for branch in branches:
        frame = branch.hazard_branch.frames[-1]
        base = base_observation(branch, frame)
        try:
            hash(base)
        except TypeError as error:
            raise ValueError("base observation must be hashable") from error
        successor = branch.successor_input_state
        key = Route2OrderedModeObservationKey(
            base_observation=base,
            physical_step=branch.cadence_frames,
            active_mask=successor.active_mask,
            held_desired_mask=successor.held_desired_mask,
            mode_state=branch.successor_mode_state,
        )
        grouped.setdefault(key, []).append(branch)

    return tuple(
        Route2OrderedModeDecisionObservationClass(
            key=key,
            successor_input_belief=OrderedInputBelief.from_states(
                branch.successor_input_state for branch in hidden
            ),
            hidden_branches=tuple(hidden),
        )
        for key, hidden in grouped.items()
    )


def merge_route2_mode_observation_classes(
    branches: tuple[Route2ModeHazardBranch, ...],
    *,
    physical_step: int,
    base_observation: Callable[
        [Route2ModeHazardBranch, Route2ModeHazardFrame],
        Hashable,
    ],
) -> tuple[Route2ModeObservationClass, ...]:
    """Merge only histories indistinguishable at a future decision.

    The caller-supplied base observation must already include every observable
    non-mode field, including physical position/time and immutable hazard
    version.  Native active input, held desired input, and player +3/+5/+8 are
    then appended here.  Hidden pickup delays never appear in the key.
    """

    if not branches:
        raise ValueError("at least one mode branch is required")
    if physical_step <= 0:
        raise ValueError("physical step must be positive")
    grouped: dict[
        Route2ModeObservationKey,
        list[Route2ModeHazardBranch],
    ] = {}
    for branch in branches:
        if physical_step > len(branch.frames):
            raise ValueError("physical step exceeds a mode branch horizon")
        frame = branch.frames[physical_step - 1]
        base = base_observation(branch, frame)
        try:
            hash(base)
        except TypeError as error:
            raise ValueError("base observation must be hashable") from error
        key = Route2ModeObservationKey(
            base_observation=base,
            physical_step=physical_step,
            active_action=frame.active_action,
            held_desired_action=branch.pipeline_branch.selected_action,
            mode_state=frame.mode_state_after,
        )
        grouped.setdefault(key, []).append(branch)
    return tuple(
        Route2ModeObservationClass(
            key=key,
            hidden_branches=tuple(hidden),
        )
        for key, hidden in grouped.items()
    )


def merge_route2_mode_decision_observation_classes(
    branches: tuple[Route2ModeDecisionBranch, ...],
    *,
    base_observation: Callable[
        [Route2ModeDecisionBranch, Route2ModeHazardFrame],
        Hashable,
    ],
) -> tuple[Route2ModeDecisionObservationClass, ...]:
    """Merge exact next-decision branches by the full available observation."""

    if not branches:
        raise ValueError("at least one decision branch is required")
    grouped: dict[
        Route2ModeObservationKey,
        list[Route2ModeDecisionBranch],
    ] = {}
    for branch in branches:
        frame = branch.hazard_branch.frames[-1]
        base = base_observation(branch, frame)
        try:
            hash(base)
        except TypeError as error:
            raise ValueError("base observation must be hashable") from error
        successor = branch.successor_pipeline_root
        key = Route2ModeObservationKey(
            base_observation=base,
            physical_step=branch.cadence_frames,
            active_action=successor.active_action,
            held_desired_action=successor.held_desired_action,
            mode_state=branch.successor_mode_state,
        )
        grouped.setdefault(key, []).append(branch)

    result: list[Route2ModeDecisionObservationClass] = []
    for key, hidden in grouped.items():
        if key.active_action == key.held_desired_action:
            successor_root = LocalPipelineRoot(
                active_action=key.active_action,
                held_desired_action=key.held_desired_action,
            )
        else:
            remaining_support = tuple(
                sorted(
                    {
                        remaining
                        for branch in hidden
                        for remaining in (
                            branch.successor_pipeline_root.remaining_delay_support
                        )
                    }
                )
            )
            successor_root = LocalPipelineRoot(
                active_action=key.active_action,
                held_desired_action=key.held_desired_action,
                pending_action=key.held_desired_action,
                remaining_delay_support=remaining_support,
            )
        result.append(
            Route2ModeDecisionObservationClass(
                key=key,
                successor_pipeline_root=successor_root,
                hidden_branches=tuple(hidden),
            )
        )
    return tuple(result)


__all__ = [
    "BOMB_INPUT_BIT",
    "ENEMY_ACTIVE_FLAG",
    "ENEMY_CONTACT_ENABLED_FLAG",
    "ENEMY_MANAGER_BLOCKING_FLAGS",
    "ENEMY_PLAYER_SHOT_DAMAGE_ENABLED_FLAG",
    "ENEMY_SECONDARY_CHARACTER_BLOCK_FLAG",
    "ENEMY_SECONDARY_CHARACTER_SYNC_FLAG",
    "FOCUS_INPUT_BIT",
    "EnemyModeProjection",
    "Route2AsyncOrderedModeDecisionBranch",
    "Route2AsyncOrderedModeDecisionObservationClass",
    "Route2AsyncOrderedModeHazardBranch",
    "Route2EnemyModeBody",
    "Route2EnemyModeStateKey",
    "Route2ModeBodyProjection",
    "Route2ModeDecisionBranch",
    "Route2ModeDecisionObservationClass",
    "Route2ModeHazardBranch",
    "Route2ModeHazardFrame",
    "Route2ModeObservationClass",
    "Route2ModeObservationKey",
    "Route2OrderedModeDecisionBranch",
    "Route2OrderedModeDecisionObservationClass",
    "Route2OrderedModeHazardBranch",
    "Route2OrderedModeObservationKey",
    "merge_route2_async_ordered_mode_decision_observation_classes",
    "merge_route2_ordered_mode_decision_observation_classes",
    "merge_route2_mode_observation_classes",
    "merge_route2_mode_decision_observation_classes",
    "project_enemy_mode",
    "project_route2_enemy_mode",
    "project_route2_async_ordered_mode_decision_branches",
    "project_route2_mode_pipeline_branches",
    "project_route2_mode_decision_branches",
    "project_route2_ordered_mode_decision_branches",
    "route2_enemy_mode_state_key",
    "step_route2_enemy_mode_state",
]
