#!/usr/bin/env python3
"""Incremental integrated TH08 simulator assembled in native frame order."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from deterministic_sim import DeterministicFrameExecutor, EventContext
from state_trace import FloatEncoding, ProjectionField, StateProjection
from th08_ecl import EclFile
from th08_enemy_spawn_lifecycle import (
    InitialEnemyVmExecutor,
    Route2TimelineSpawnLifecycleStep,
    execute_route2_timeline_spawn_lifecycles,
)
from th08_future_body_identity import Route2SlotLifetimeLedger
from th08_hostile_bullet_pool import (
    HostileBulletPoolState,
    HostileBulletPoolStep,
    HostileBulletSpawnRequest,
    step_hostile_bullet_pool,
)
from th08_item_model import ItemResources
from th08_item_pool import (
    ItemPoolConfig,
    ItemPoolState,
    ItemPoolStep,
    ItemSpawnRequest,
    initial_item_pool_state,
    step_item_pool,
)
from th08_laser_pool import (
    LaserPoolState,
    LaserPoolStep,
    LaserSpawnRequest,
    step_laser_pool,
)
from th08_player_model import BombProfile, predeath_countdown_frames
from th08_rng import Th08Rng
from th08_route2_player_runtime import (
    BombStartKind,
    PlayerPhase,
    Route2PlayerState,
    initial_route2_player_state,
    step_route2_player,
)
from th08_timeline_model import (
    StageTimelineState,
    StageTimelineStep,
    TimelineExternalState,
    initial_stage_timeline_state,
    step_stage_timelines,
)
from th08_update_order import PLAYBACK_EXTENDED, TH08_FRAME_SCHEDULE


@dataclass(frozen=True)
class Th08Route2FrameControl:
    input_mask: int
    bomb_start: BombStartKind | None = None
    time_scale: float = 1.0
    timeline_external: TimelineExternalState = field(
        default_factory=TimelineExternalState
    )
    item_spawns_before_update: tuple[ItemSpawnRequest, ...] = ()
    hostile_bullet_spawns_before_update: tuple[HostileBulletSpawnRequest, ...] = ()
    laser_spawns_before_update: tuple[LaserSpawnRequest, ...] = ()
    global_scatter_timer_negative: bool = False
    player_hit_context: PlayerHitContext | None = None


@dataclass(frozen=True)
class PlayerHitContext:
    team_meter_left_at_least_right: bool
    spell_state_active: bool
    stage_load_index: int


@dataclass(frozen=True)
class LaserPlayerConfig:
    hitbox_half_width: float = 2.0
    hitbox_half_height: float = 2.0


@dataclass(frozen=True)
class HostileBulletPlayerConfig:
    hitbox_half_width: float = 2.0
    hitbox_half_height: float = 2.0
    auxiliary_half_width: float = 6.0
    auxiliary_half_height: float = 6.0


@dataclass(frozen=True)
class Th08Route2SimulationState:
    published_input_mask: int
    player: Route2PlayerState
    last_effective_focus: bool = False
    last_movement_applied: bool = False
    last_bomb_started: BombProfile | None = None
    last_bomb_ended: BombProfile | None = None
    timeline_program: EclFile | None = None
    timeline: StageTimelineState | None = None
    active_timeline_difficulty_mask: int = 0
    last_timeline_step: StageTimelineStep | None = None
    enemy_lifetime_ledger: Route2SlotLifetimeLedger | None = None
    initial_enemy_vm_executor: InitialEnemyVmExecutor | None = None
    last_timeline_spawn_lifecycle: (
        Route2TimelineSpawnLifecycleStep | None
    ) = None
    gameplay_rng_state: int = 0
    gameplay_rng_calls: int = 0
    item_pool: ItemPoolState | None = None
    item_config: ItemPoolConfig | None = None
    last_item_step: ItemPoolStep | None = None
    hostile_bullet_pool: HostileBulletPoolState | None = None
    hostile_bullet_player_config: HostileBulletPlayerConfig | None = None
    last_hostile_bullet_step: HostileBulletPoolStep | None = None
    laser_pool: LaserPoolState | None = None
    laser_player_config: LaserPlayerConfig | None = None
    last_laser_step: LaserPoolStep | None = None


def initial_route2_simulation_state(**player_kwargs: object) -> Th08Route2SimulationState:
    return Th08Route2SimulationState(
        published_input_mask=0,
        player=initial_route2_player_state(**player_kwargs),
    )


def initial_route2_stage_simulation_state(
    ecl: EclFile,
    *,
    rng_seed: int,
    active_timeline_difficulty_mask: int,
    item_resources: ItemResources | None = None,
    item_config: ItemPoolConfig | None = None,
    hostile_bullet_player_config: HostileBulletPlayerConfig | None = None,
    laser_player_config: LaserPlayerConfig | None = None,
    initial_enemy_vm_executor: InitialEnemyVmExecutor | None = None,
    initial_enemy_active_slots: tuple[int, ...] = (),
    root_physical_update: int = 0,
    **player_kwargs: object,
) -> Th08Route2SimulationState:
    """Initialize the replay/player/timeline slice without inventing enemy VM state."""

    if not 0 <= active_timeline_difficulty_mask <= 0xFF:
        raise ValueError("active timeline difficulty mask must fit in one byte")
    if (item_resources is None) != (item_config is None):
        raise ValueError("item resources and item config must be supplied together")
    if initial_enemy_vm_executor is None and initial_enemy_active_slots:
        raise ValueError(
            "initial enemy slots require an initial-VM executor"
        )
    if item_resources is not None:
        requested_bombs = player_kwargs.get("bombs", item_resources.bombs)
        if requested_bombs != item_resources.bombs:
            raise ValueError("player and item-resource Bomb stock must agree")
        player_kwargs["bombs"] = item_resources.bombs
    return replace(
        initial_route2_simulation_state(**player_kwargs),
        timeline_program=ecl,
        timeline=initial_stage_timeline_state(ecl, rng_seed=rng_seed),
        active_timeline_difficulty_mask=active_timeline_difficulty_mask,
        gameplay_rng_state=rng_seed,
        enemy_lifetime_ledger=(
            Route2SlotLifetimeLedger.from_root_active_slots(
                root_physical_update=root_physical_update,
                active_slots=initial_enemy_active_slots,
            )
            if initial_enemy_vm_executor is not None
            else None
        ),
        initial_enemy_vm_executor=initial_enemy_vm_executor,
        item_pool=(
            initial_item_pool_state(item_resources)
            if item_resources is not None
            else None
        ),
        item_config=item_config,
        hostile_bullet_pool=(
            HostileBulletPoolState()
            if hostile_bullet_player_config is not None
            else None
        ),
        hostile_bullet_player_config=hostile_bullet_player_config,
        laser_pool=LaserPoolState() if laser_player_config is not None else None,
        laser_player_config=laser_player_config,
    )


def _publish_replay_input(
    state: Th08Route2SimulationState,
    control: Th08Route2FrameControl,
    _context: EventContext,
) -> Th08Route2SimulationState:
    return replace(state, published_input_mask=control.input_mask & 0xFFFF)


def _step_player_input_movement(
    state: Th08Route2SimulationState,
    control: Th08Route2FrameControl,
    _context: EventContext,
) -> Th08Route2SimulationState:
    bomb_start = control.bomb_start
    if (
        bomb_start is None
        and state.player.phase is PlayerPhase.DEAD
        and state.player.state_timer_elapsed > 0
        and state.player.bomb is None
        and state.player.bombs > 0
        and state.published_input_mask & 0x02
    ):
        bomb_start = BombStartKind.DEATHBOMB
    result = step_route2_player(
        state.player,
        input_mask=state.published_input_mask,
        bomb_start=bomb_start,
        time_scale=control.time_scale,
    )
    item_pool = state.item_pool
    if item_pool is not None and item_pool.resources.bombs != result.state.bombs:
        item_pool = replace(
            item_pool,
            resources=replace(item_pool.resources, bombs=result.state.bombs),
        )
    return replace(
        state,
        player=result.state,
        item_pool=item_pool,
        last_effective_focus=result.effective_focus,
        last_movement_applied=result.movement_applied,
        last_bomb_started=result.bomb_started,
        last_bomb_ended=result.bomb_ended,
    )


def _step_stage_timeline(
    state: Th08Route2SimulationState,
    control: Th08Route2FrameControl,
    _context: EventContext,
) -> Th08Route2SimulationState:
    if state.timeline_program is None or state.timeline is None:
        raise RuntimeError("stage timeline handler requires an initialized ECL program")
    timeline = replace(
        state.timeline,
        rng_state=state.gameplay_rng_state,
        rng_calls=state.gameplay_rng_calls,
    )
    result = step_stage_timelines(
        state.timeline_program,
        timeline,
        active_difficulty_mask=state.active_timeline_difficulty_mask,
        external=control.timeline_external,
    )
    spawn_lifecycle = None
    enemy_lifetime_ledger = state.enemy_lifetime_ledger
    if enemy_lifetime_ledger is not None:
        if state.initial_enemy_vm_executor is None:
            raise RuntimeError(
                "enemy lifetime ledger requires an initial-VM executor"
            )
        spawn_lifecycle = execute_route2_timeline_spawn_lifecycles(
            enemy_lifetime_ledger,
            next_physical_update=(
                enemy_lifetime_ledger.current_physical_update + 1
            ),
            spawns=result.spawns,
            initial_vm_executor=state.initial_enemy_vm_executor,
        )
        enemy_lifetime_ledger = spawn_lifecycle.lifecycle.successor
    return replace(
        state,
        timeline=result.state,
        last_timeline_step=result,
        enemy_lifetime_ledger=enemy_lifetime_ledger,
        last_timeline_spawn_lifecycle=spawn_lifecycle,
        gameplay_rng_state=result.state.rng_state,
        gameplay_rng_calls=result.state.rng_calls,
    )


def _step_item_manager(
    state: Th08Route2SimulationState,
    control: Th08Route2FrameControl,
    _context: EventContext,
) -> Th08Route2SimulationState:
    if state.item_pool is None or state.item_config is None:
        raise RuntimeError("item handler requires initialized item state and config")
    if state.item_pool.resources.bombs != state.player.bombs:
        raise RuntimeError("player and item-resource Bomb stock diverged before item pass")
    rng = Th08Rng(state.gameplay_rng_state, state.gameplay_rng_calls)
    result = step_item_pool(
        state.item_pool,
        spawns_before_update=control.item_spawns_before_update,
        player_x=state.player.x,
        player_y=state.player.y,
        player_state=int(state.player.phase),
        focused=state.last_effective_focus,
        config=state.item_config,
        rng=rng,
        time_scale=control.time_scale,
        timer_scale=control.time_scale,
        global_scatter_timer_negative=control.global_scatter_timer_negative,
    )
    return replace(
        state,
        player=replace(state.player, bombs=result.state.resources.bombs),
        item_pool=result.state,
        last_item_step=result,
        gameplay_rng_state=rng.state,
        gameplay_rng_calls=rng.calls,
    )


def _step_laser_manager(
    state: Th08Route2SimulationState,
    control: Th08Route2FrameControl,
    _context: EventContext,
) -> Th08Route2SimulationState:
    if state.laser_pool is None or state.laser_player_config is None:
        raise RuntimeError("laser handler requires initialized laser state and config")
    result = step_laser_pool(
        state.laser_pool,
        spawns_before_update=control.laser_spawns_before_update,
        player_x=state.player.x,
        player_y=state.player.y,
        player_half_width=state.laser_player_config.hitbox_half_width,
        player_half_height=state.laser_player_config.hitbox_half_height,
        player_state=int(state.player.phase),
        time_scale=control.time_scale,
    )
    player = _apply_hostile_hit(state.player, control) if result.hit else state.player
    return replace(
        state,
        player=player,
        laser_pool=result.state,
        last_laser_step=result,
    )


def _apply_hostile_hit(
    player: Route2PlayerState, control: Th08Route2FrameControl
) -> Route2PlayerState:
    if player.phase is not PlayerPhase.NORMAL:
        return player
    if control.player_hit_context is None:
        raise RuntimeError("a hostile hit requires PlayerHitContext")
    countdown = predeath_countdown_frames(
        player.bombs,
        team_meter_left_at_least_right=(
            control.player_hit_context.team_meter_left_at_least_right
        ),
        spell_state_active=control.player_hit_context.spell_state_active,
        stage_load_index=control.player_hit_context.stage_load_index,
    )
    return replace(
        player,
        phase=PlayerPhase.DEAD,
        state_timer_elapsed=countdown,
        state_timer_fraction=0.0,
    )


def _step_hostile_bullet_manager(
    state: Th08Route2SimulationState,
    control: Th08Route2FrameControl,
    _context: EventContext,
) -> Th08Route2SimulationState:
    if (
        state.hostile_bullet_pool is None
        or state.hostile_bullet_player_config is None
    ):
        raise RuntimeError(
            "hostile-bullet handler requires initialized bullet state and config"
        )
    config = state.hostile_bullet_player_config
    result = step_hostile_bullet_pool(
        state.hostile_bullet_pool,
        spawns_before_update=control.hostile_bullet_spawns_before_update,
        player_x=state.player.x,
        player_y=state.player.y,
        player_hitbox_half_width=config.hitbox_half_width,
        player_hitbox_half_height=config.hitbox_half_height,
        player_aux_half_width=config.auxiliary_half_width,
        player_aux_half_height=config.auxiliary_half_height,
        player_state=int(state.player.phase),
    )
    player = _apply_hostile_hit(state.player, control) if result.hit else state.player
    return replace(
        state,
        player=player,
        hostile_bullet_pool=result.state,
        last_hostile_bullet_step=result,
    )


def route2_player_executor(
    *, mode: str = PLAYBACK_EXTENDED
) -> DeterministicFrameExecutor[
    Th08Route2SimulationState, Th08Route2FrameControl
]:
    """Build the currently integrated replay-input plus player subset."""

    return DeterministicFrameExecutor(
        schedule=TH08_FRAME_SCHEDULE,
        mode=mode,
        handlers={
            "replay_publish_input": _publish_replay_input,
            "player_input_movement": _step_player_input_movement,
        },
        event_keys=("replay_publish_input", "player_input_movement"),
    )


def route2_stage_executor(
    *, mode: str = PLAYBACK_EXTENDED
) -> DeterministicFrameExecutor[
    Th08Route2SimulationState, Th08Route2FrameControl
]:
    """Build the replay/player/stage-timeline slice in native event order."""

    return DeterministicFrameExecutor(
        schedule=TH08_FRAME_SCHEDULE,
        mode=mode,
        handlers={
            "replay_publish_input": _publish_replay_input,
            "player_input_movement": _step_player_input_movement,
            "stage_timeline_step": _step_stage_timeline,
        },
        event_keys=(
            "replay_publish_input",
            "player_input_movement",
            "stage_timeline_step",
        ),
    )


def route2_stage_item_executor(
    *, mode: str = PLAYBACK_EXTENDED
) -> DeterministicFrameExecutor[
    Th08Route2SimulationState, Th08Route2FrameControl
]:
    """Build replay/player/timeline/item execution with one shared RNG state."""

    return DeterministicFrameExecutor(
        schedule=TH08_FRAME_SCHEDULE,
        mode=mode,
        handlers={
            "replay_publish_input": _publish_replay_input,
            "player_input_movement": _step_player_input_movement,
            "stage_timeline_step": _step_stage_timeline,
            "item_manager_update": _step_item_manager,
        },
        event_keys=(
            "replay_publish_input",
            "player_input_movement",
            "stage_timeline_step",
            "item_manager_update",
        ),
    )


def route2_stage_item_laser_executor(
    *, mode: str = PLAYBACK_EXTENDED
) -> DeterministicFrameExecutor[
    Th08Route2SimulationState, Th08Route2FrameControl
]:
    """Build the integrated slice through laser contact in native event order.

    Hostile bullets remain an explicit missing event between item and laser.
    Supplying laser spawns models allocations made by the earlier enemy pass.
    """

    return DeterministicFrameExecutor(
        schedule=TH08_FRAME_SCHEDULE,
        mode=mode,
        handlers={
            "replay_publish_input": _publish_replay_input,
            "player_input_movement": _step_player_input_movement,
            "stage_timeline_step": _step_stage_timeline,
            "item_manager_update": _step_item_manager,
            "laser_motion_collision_graze": _step_laser_manager,
        },
        event_keys=(
            "replay_publish_input",
            "player_input_movement",
            "stage_timeline_step",
            "item_manager_update",
            "laser_motion_collision_graze",
        ),
    )


def route2_stage_item_projectile_executor(
    *, mode: str = PLAYBACK_EXTENDED
) -> DeterministicFrameExecutor[
    Th08Route2SimulationState, Th08Route2FrameControl
]:
    """Build the integrated player/timeline/item/bullet/laser execution slice."""

    return DeterministicFrameExecutor(
        schedule=TH08_FRAME_SCHEDULE,
        mode=mode,
        handlers={
            "replay_publish_input": _publish_replay_input,
            "player_input_movement": _step_player_input_movement,
            "stage_timeline_step": _step_stage_timeline,
            "item_manager_update": _step_item_manager,
            "hostile_bullet_transform_motion_collision_graze": (
                _step_hostile_bullet_manager
            ),
            "laser_motion_collision_graze": _step_laser_manager,
        },
        event_keys=(
            "replay_publish_input",
            "player_input_movement",
            "stage_timeline_step",
            "item_manager_update",
            "hostile_bullet_transform_motion_collision_graze",
            "laser_motion_collision_graze",
        ),
    )


TH08_ROUTE2_PLAYER_PROJECTION = StateProjection(
    (
        ProjectionField("input", ("published_input_mask",)),
        ProjectionField("player.frame", ("player", "frame_index")),
        ProjectionField(
            "player.x",
            ("player", "x"),
            FloatEncoding.BINARY32_BITS,
        ),
        ProjectionField(
            "player.y",
            ("player", "y"),
            FloatEncoding.BINARY32_BITS,
        ),
        ProjectionField("player.phase", ("player", "phase")),
        ProjectionField("player.bombs", ("player", "bombs")),
        ProjectionField(
            "player.focus_logic",
            ("player", "focus", "focus_logic_value"),
        ),
        ProjectionField("effective_focus", ("last_effective_focus",)),
        ProjectionField("movement_applied", ("last_movement_applied",)),
    )
)
