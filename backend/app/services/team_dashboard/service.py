from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from ...schemas import (
    InjuryPartDistributionItem,
    PositionAvailabilityItem,
    PositionBalanceItem,
    PositionDevelopmentItem,
    TeamAvailabilityBoard,
    TeamDevelopmentTrend,
    TeamLoadTrend,
    TeamLoadTrendPoint,
    TeamMatchFormBoard,
    TeamMatchFormItem,
    TeamMedicalOverview,
    TeamOverviewResponse,
)
from ..frame_loader import fetch_frame as _fetch_frame
from ..pipelines.match_score_pipeline import prepare_objective_match_scores
from ..pipelines.position_balance_pipeline import build_position_balance
from ..pipelines.recent_form_pipeline import summarize_recent_form
from ..pipelines.team_availability_pipeline import build_team_availability_board
from ..pipelines.team_development_pipeline import build_team_development_trend
from ..pipelines.team_load_pipeline import build_session_load_frame, build_team_load_trend, summarize_player_load_status
from ..pipelines.team_match_form_pipeline import build_team_match_form
from ..pipelines.team_medical_pipeline import build_team_medical_overview
from .queries import (
    INJURIES_QUERY,
    MATCH_LOAD_QUERY,
    PHYSICAL_PROFILES_QUERY,
    ROSTER_QUERY,
    TEAM_MATCHES_QUERY,
    TRAINING_LOAD_QUERY,
)
from .snapshot import _resolve_load_snapshot_date, _resolve_snapshot_date


def _serialize_match_form_item(item: dict[str, Any] | None) -> TeamMatchFormItem | None:
    if item is None:
        return None
    return TeamMatchFormItem(**item)


def build_team_overview(as_of_date: date | None = None) -> TeamOverviewResponse:
    players = _fetch_frame(ROSTER_QUERY)
    injuries = _fetch_frame(INJURIES_QUERY)
    training_load = _fetch_frame(TRAINING_LOAD_QUERY)
    match_load = _fetch_frame(MATCH_LOAD_QUERY)
    match_stats = _fetch_frame(TEAM_MATCHES_QUERY)
    physical_profiles = _fetch_frame(PHYSICAL_PROFILES_QUERY)

    snapshot_ts = _resolve_snapshot_date(
        as_of_date=as_of_date,
        training_load=training_load,
        match_load=match_load,
        match_stats=match_stats,
        physical_profiles=physical_profiles,
        injuries=injuries,
    )
    load_snapshot_ts = _resolve_load_snapshot_date(training_load, match_load, snapshot_ts)

    sessions = build_session_load_frame(training_load, match_load, load_snapshot_ts)
    player_load_status = summarize_player_load_status(players, sessions)
    availability_board_data, position_availability = build_team_availability_board(
        players=players,
        injuries=injuries,
        player_load_status=player_load_status,
        snapshot_ts=snapshot_ts,
    )
    load_board_data = build_team_load_trend(players=players, sessions=sessions, player_load_status=player_load_status)

    match_stats["match_date"] = pd.to_datetime(match_stats["match_date"], errors="coerce")
    match_stats = match_stats[match_stats["match_date"].notna() & (match_stats["match_date"] <= snapshot_ts)].copy()
    scored_matches = prepare_objective_match_scores(match_stats)
    match_form_data, team_matches = build_team_match_form(scored_matches)
    position_balance_data = build_position_balance(scored_matches, position_availability, team_matches)

    form_summary = summarize_recent_form(scored_matches)
    medical_data = build_team_medical_overview(injuries, snapshot_ts)
    development_data = build_team_development_trend(
        players=players,
        physical_profiles=physical_profiles,
        form_summary=form_summary,
        snapshot_ts=snapshot_ts,
    )

    return TeamOverviewResponse(
        snapshot_date=snapshot_ts.date(),
        availability=TeamAvailabilityBoard(
            available_count=availability_board_data["available_count"],
            managed_count=availability_board_data["managed_count"],
            injured_count=availability_board_data["injured_count"],
            scheduled_return_count=availability_board_data["scheduled_return_count"],
            positions=[PositionAvailabilityItem(**item) for item in availability_board_data["positions"]],
        ),
        load=TeamLoadTrend(
            load_7d=load_board_data["load_7d"],
            load_14d=load_board_data["load_14d"],
            load_28d=load_board_data["load_28d"],
            match_load_share_28d=load_board_data["match_load_share_28d"],
            training_load_share_28d=load_board_data["training_load_share_28d"],
            average_sprint_exposure_7d=load_board_data["average_sprint_exposure_7d"],
            average_total_distance_7d=load_board_data["average_total_distance_7d"],
            load_spike_player_count=load_board_data["load_spike_player_count"],
            load_drop_player_count=load_board_data["load_drop_player_count"],
            trend_points=[TeamLoadTrendPoint(**point) for point in load_board_data["trend_points"]],
        ),
        match_form=TeamMatchFormBoard(
            recent_5_match_score=match_form_data["recent_5_match_score"],
            previous_5_match_score=match_form_data["previous_5_match_score"],
            form_delta=match_form_data["form_delta"],
            latest_match_score=match_form_data["latest_match_score"],
            best_match=_serialize_match_form_item(match_form_data["best_match"]),
            worst_match=_serialize_match_form_item(match_form_data["worst_match"]),
            recent_matches=[TeamMatchFormItem(**item) for item in match_form_data["recent_matches"]],
        ),
        position_balance=[PositionBalanceItem(**item) for item in position_balance_data],
        medical=TeamMedicalOverview(
            injuries_last_180d=medical_data["injuries_last_180d"],
            reinjury_count_365d=medical_data["reinjury_count_365d"],
            returns_last_14d_count=medical_data["returns_last_14d_count"],
            current_rehab_count=medical_data["current_rehab_count"],
            injury_parts=[InjuryPartDistributionItem(**item) for item in medical_data["injury_parts"]],
        ),
        development=TeamDevelopmentTrend(
            average_body_fat_delta=development_data["average_body_fat_delta"],
            average_muscle_mass_delta=development_data["average_muscle_mass_delta"],
            season_start_body_fat_delta=development_data["season_start_body_fat_delta"],
            season_start_muscle_mass_delta=development_data["season_start_muscle_mass_delta"],
            rising_players_count=development_data["rising_players_count"],
            falling_players_count=development_data["falling_players_count"],
            positions=[PositionDevelopmentItem(**item) for item in development_data["positions"]],
        ),
    )


__all__ = ["build_team_overview"]
