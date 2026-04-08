from __future__ import annotations

from typing import Any

import pandas as pd

from .queries import TEAM_NAME
from .shared import _result_label, _safe_float, _safe_int, _score_label


def _split_minutes(
    *,
    started: bool,
    sub_in_minute: int | None,
    sub_out_minute: int | None,
    minutes_played: int,
) -> tuple[int, int]:
    if minutes_played <= 0:
        return 0, 0

    # Substitute appearances frequently lack one boundary, so recover a reasonable
    # first-half/second-half split from the available timeline fields.
    start_minute = 0 if started else (sub_in_minute or max(0, 90 - minutes_played))
    if sub_out_minute is not None:
        end_minute = sub_out_minute
    else:
        end_minute = min(90, start_minute + minutes_played)
    if end_minute < start_minute:
        end_minute = start_minute + minutes_played

    first_half = max(0, min(end_minute, 45) - min(start_minute, 45))
    second_half = max(0, min(end_minute, 90) - max(start_minute, 45))
    total = first_half + second_half
    if total != minutes_played:
        second_half = max(0, minutes_played - first_half)
    return first_half, second_half


def _build_match_performance_records(match_frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in match_frame.itertuples(index=False):
        started = row.start_position is not None
        sub_in_minute = _safe_int(row.substitute_in)
        sub_out_minute = _safe_int(row.substitute_out)
        minutes_played = _safe_int(row.minutes_played) or 0
        first_half_minutes, second_half_minutes = _split_minutes(
            started=started,
            sub_in_minute=sub_in_minute,
            sub_out_minute=sub_out_minute,
            minutes_played=minutes_played,
        )
        pass_success_pct = None
        if row.pass_accuracy is not None and not pd.isna(row.pass_accuracy):
            pass_success_pct = round(float(row.pass_accuracy) * 100.0, 1)
        goals = _safe_int(row.goals) or 0
        assists = _safe_int(row.assists) or 0
        shots = _safe_int(row.shots) or 0
        shots_on_target = _safe_int(row.shots_on_target) or 0
        key_passes = _safe_int(row.key_passes) or 0
        pass_attempts = _safe_int(row.passes_attempted) or 0
        pass_success = _safe_int(row.passes_completed) or 0
        dribble_attempts = _safe_float(row.take_ons_attempted)
        dribble_success = _safe_float(row.take_ons_succeeded)
        tackles_won = _safe_int(row.tackles_succeeded) or 0
        interceptions = _safe_int(row.interceptions) or 0
        clearings = _safe_int(row.clearances) or 0
        saves = _safe_int(row.saves) or 0
        aerial_duels_won = _safe_int(row.aerial_duels_won) or 0
        ground_duels_won = _safe_int(row.ground_duels_won) or 0
        aerial_duels_lost = _safe_int(row.aerial_duels_lost) or 0
        ground_duels_lost = _safe_int(row.ground_duels_lost) or 0
        yellow_cards = _safe_int(row.yellow_cards) or 0
        red_cards = _safe_int(row.red_cards) or 0
        dribble_success_pct = None
        if dribble_attempts is not None and dribble_attempts > 0:
            dribble_success_pct = round(((dribble_success or 0.0) / dribble_attempts) * 100.0, 1)
        elif dribble_success is not None and dribble_success > 0:
            dribble_success_pct = 100.0

        records.append(
            {
                "analysis_id": str(row.match_player_id),
                "player_id": str(row.player_id),
                "match_id": str(row.match_id),
                "match_type": row.match_type,
                "season_id": str(row.season_id),
                "season_year": int(row.season_year),
                "match_no": int(row.match_no),
                "match_date": row.match_date.date(),
                "team_name": TEAM_NAME,
                "opponent": str(row.opponent_team),
                "venue": str(row.stadium_name),
                "result": _result_label(row.goals_for, row.goals_against),
                "score": _score_label(row.goals_for, row.goals_against),
                "match_label": f"MD {int(row.match_no)}",
                "name": str(row.player_name),
                "position": row.registered_position,
                "position_played": row.position_played or row.registered_position,
                "appearance_type": "선발" if started else "교체",
                "started": "Y" if started else "N",
                "minutes_played": minutes_played,
                "first_half_minutes": first_half_minutes,
                "second_half_minutes": second_half_minutes,
                "sub_in_minute": sub_in_minute,
                "sub_out_minute": sub_out_minute,
                "goals": goals,
                "assists": assists,
                "goal_contrib": goals + assists,
                "shots": shots,
                "shots_on_target": shots_on_target,
                "key_passes": key_passes,
                "pass_attempts": pass_attempts,
                "pass_success": pass_success,
                "pass_success_pct": pass_success_pct,
                "dribble_attempts": int(round(dribble_attempts or 0)),
                "dribble_success": int(round(dribble_success or 0)),
                "dribble_success_pct": dribble_success_pct,
                "tackles_won": tackles_won,
                "interceptions": interceptions,
                "clearings": clearings,
                "saves": saves,
                "duels_won": aerial_duels_won + ground_duels_won,
                "duels_lost": aerial_duels_lost + ground_duels_lost,
                "yellow_cards": yellow_cards,
                "red_cards": red_cards,
                "play_time_min": _safe_float(row.play_time_min, 1),
                "total_distance": _safe_float(row.total_distance, 2),
                "avg_speed": _safe_float(row.avg_speed, 1),
                "max_speed": _safe_float(row.max_speed, 1),
                "sprint_distance": _safe_float(row.sprint_distance, 1),
                "accel_count": _safe_int(row.accel_count),
                "decel_count": _safe_int(row.decel_count),
                "hi_accel_count": _safe_int(row.hi_accel_count),
                "hi_decel_count": _safe_int(row.hi_decel_count),
                "cod_count": _safe_int(row.cod_count),
                "distance_0_15_min": _safe_float(row.distance_0_15_min, 2),
                "distance_15_30_min": _safe_float(row.distance_15_30_min, 2),
                "distance_30_45_min": _safe_float(row.distance_30_45_min, 2),
                "distance_45_60_min": _safe_float(row.distance_45_60_min, 2),
                "distance_60_75_min": _safe_float(row.distance_60_75_min, 2),
                "distance_75_90_min": _safe_float(row.distance_75_90_min, 2),
                "distance_speed_0_5": _safe_float(row.distance_speed_0_5, 2),
                "distance_speed_5_10": _safe_float(row.distance_speed_5_10, 2),
                "distance_speed_10_15": _safe_float(row.distance_speed_10_15, 2),
                "distance_speed_15_20": _safe_float(row.distance_speed_15_20, 2),
                "distance_speed_20_25": _safe_float(row.distance_speed_20_25, 2),
                "distance_speed_25_plus": _safe_float(row.distance_speed_25_plus, 2),
                "distance_total_km": _safe_float(row.total_distance, 2),
                "distance_high_speed_m": _safe_float(row.distance_high_speed_m, 1),
                "max_speed_kmh": _safe_float(row.max_speed, 1),
                "sprint_count": _safe_int(row.sprint_count),
                "acceleration_count": _safe_int(row.accel_count),
                "deceleration_count": _safe_int(row.decel_count),
                "player_load": _safe_float(row.player_load, 1),
                "impact_score": _safe_float(row.impact_score, 3) or 0.0,
            }
        )
    return records


def _build_match_gps_summary(match_frame: pd.DataFrame) -> list[dict[str, Any]]:
    if match_frame.empty:
        return []

    rows: list[dict[str, Any]] = []
    grouped = match_frame.groupby(
        ["match_id", "season_id", "season_year", "match_no", "match_date", "opponent_team", "stadium_name", "goals_for", "goals_against"],
        sort=False,
    )
    for key, group in grouped:
        (
            match_id,
            season_id,
            season_year,
            match_no,
            match_date,
            opponent_team,
            stadium_name,
            goals_for,
            goals_against,
        ) = key
        active = group[group["minutes_played"].fillna(0) > 0].copy()
        denominator = active["minutes_played"].replace(0, pd.NA)
        distance_p90 = ((active["total_distance"] / denominator) * 90).dropna()
        high_speed_p90 = ((active["distance_high_speed_m"] / denominator) * 90).dropna()
        sprint_p90 = ((active["sprint_count"] / denominator) * 90).dropna()
        accel_p90 = ((active["accel_count"] / denominator) * 90).dropna()
        decel_p90 = ((active["decel_count"] / denominator) * 90).dropna()
        load_p90 = ((active["player_load"] / denominator) * 90).dropna()

        rows.append(
            {
                "match_id": str(match_id),
                "season_id": str(season_id),
                "season_year": int(season_year),
                "match_no": int(match_no),
                "match_date": pd.Timestamp(match_date).date(),
                "match_label": f"MD {int(match_no)}",
                "opponent": str(opponent_team),
                "venue": str(stadium_name),
                "result": _result_label(goals_for, goals_against),
                "active_players": int(active["player_id"].nunique()),
                "total_distance_km": round(float(group["total_distance"].fillna(0).sum()), 2),
                "total_high_speed_m": int(round(float(group["distance_high_speed_m"].fillna(0).sum()))),
                "peak_max_speed_kmh": round(float(group["max_speed"].fillna(0).max()), 1),
                "avg_max_speed_kmh": round(float(active["max_speed"].dropna().mean()), 2) if not active["max_speed"].dropna().empty else 0.0,
                "total_sprint_count": int(round(float(group["sprint_count"].fillna(0).sum()))),
                "total_acceleration_count": int(round(float(group["accel_count"].fillna(0).sum()))),
                "total_deceleration_count": int(round(float(group["decel_count"].fillna(0).sum()))),
                "total_player_load": round(float(group["player_load"].fillna(0).sum()), 1),
                "distance_total_p90": round(float(distance_p90.mean()), 2) if not distance_p90.empty else 0.0,
                "high_speed_m_p90": round(float(high_speed_p90.mean()), 2) if not high_speed_p90.empty else 0.0,
                "sprint_count_p90": round(float(sprint_p90.mean()), 2) if not sprint_p90.empty else 0.0,
                "acceleration_count_p90": round(float(accel_p90.mean()), 2) if not accel_p90.empty else 0.0,
                "deceleration_count_p90": round(float(decel_p90.mean()), 2) if not decel_p90.empty else 0.0,
                "player_load_p90": round(float(load_p90.mean()), 2) if not load_p90.empty else 0.0,
            }
        )

    return sorted(rows, key=lambda item: (item["match_date"], item["match_id"]), reverse=True)


__all__ = [
    "_build_match_gps_summary",
    "_build_match_performance_records",
]
