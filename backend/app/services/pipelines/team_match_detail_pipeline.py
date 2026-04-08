from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .match_score_pipeline import prepare_objective_match_scores


LEADER_SPECS: list[tuple[str, str, str | None]] = [
    ("match_score", "경기 점수", "pt"),
    ("total_distance", "총 거리", "km"),
    ("sprint_count", "스프린트", "회"),
    ("key_passes", "키패스", "회"),
]


def prepare_match_detail_players(player_frame: pd.DataFrame) -> pd.DataFrame:
    if player_frame.empty:
        return player_frame.copy()

    frame = player_frame.copy()
    numeric_columns = [
        "jersey_number",
        "minutes_played",
        "substitute_in",
        "substitute_out",
        "goals",
        "assists",
        "shots",
        "shots_on_target",
        "key_passes",
        "pass_accuracy",
        "recoveries",
        "interceptions",
        "mistakes",
        "yellow_cards",
        "red_cards",
        "aerial_duels_won",
        "aerial_duels_total",
        "ground_duels_won",
        "ground_duels_total",
        "total_distance",
        "play_time_min",
        "avg_speed",
        "distance_0_15_min",
        "distance_15_30_min",
        "distance_30_45_min",
        "distance_45_60_min",
        "distance_60_75_min",
        "distance_75_90_min",
        "sprint_count",
        "sprint_distance",
        "distance_speed_0_5",
        "distance_speed_5_10",
        "distance_speed_10_15",
        "distance_speed_15_20",
        "distance_speed_20_25",
        "distance_speed_25_plus",
        "cod_count",
        "max_speed",
        "accel_count",
        "decel_count",
        "hi_accel_count",
        "hi_decel_count",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    total_duels = frame["aerial_duels_total"].fillna(0) + frame["ground_duels_total"].fillna(0)
    duels_won = frame["aerial_duels_won"].fillna(0) + frame["ground_duels_won"].fillna(0)
    frame["duel_win_rate"] = np.where(total_duels > 0, duels_won / total_duels, np.nan)
    frame["starter_flag"] = frame["start_position"].notna()
    frame["substitute_used_flag"] = frame["substitute_in"].notna()

    scored = prepare_objective_match_scores(frame)
    scored = scored.sort_values(
        ["match_score", "minutes_played", "jersey_number", "name"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)
    return scored


def build_match_detail_summary(scored_players: pd.DataFrame) -> dict[str, Any]:
    if scored_players.empty:
        return {
            "team_average_match_score": None,
            "efficiency_score": None,
            "player_count": 0,
            "starter_count": 0,
            "substitute_used_count": 0,
            "average_minutes": None,
            "total_distance": None,
            "average_distance": None,
            "total_sprint_count": 0,
            "average_max_speed": None,
        }

    team_average_match_score = float(round(scored_players["match_score"].mean(), 2))
    average_minutes = float(round(scored_players["minutes_played"].mean(), 1))
    total_distance = float(round(scored_players["total_distance"].fillna(0).sum(), 2))
    average_distance = float(round(scored_players["total_distance"].fillna(0).mean(), 2))
    total_sprint_count = int(scored_players["sprint_count"].fillna(0).sum())
    max_speed_values = scored_players["max_speed"].dropna()
    average_max_speed = (
        float(round(max_speed_values.mean(), 2)) if not max_speed_values.empty else None
    )
    efficiency_score = (
        float(round(team_average_match_score / average_minutes * 90.0, 2))
        if average_minutes > 0
        else None
    )

    return {
        "team_average_match_score": team_average_match_score,
        "efficiency_score": efficiency_score,
        "player_count": int(scored_players["player_id"].nunique()),
        "starter_count": int(scored_players["starter_flag"].sum()),
        "substitute_used_count": int(scored_players["substitute_used_flag"].sum()),
        "average_minutes": average_minutes,
        "total_distance": total_distance,
        "average_distance": average_distance,
        "total_sprint_count": total_sprint_count,
        "average_max_speed": average_max_speed,
    }


def build_match_detail_team_stats(match_meta_row: dict[str, Any]) -> dict[str, Any]:
    duels_total = int(match_meta_row.get("duels_total") or 0)
    duels_won = int(match_meta_row.get("duels_won") or 0)
    duel_win_rate = float(round(duels_won / duels_total, 4)) if duels_total > 0 else None

    return {
        "assists": int(match_meta_row.get("assists") or 0),
        "shots": int(match_meta_row.get("shots") or 0),
        "shots_on_target": int(match_meta_row.get("shots_on_target") or 0),
        "key_passes": int(match_meta_row.get("key_passes") or 0),
        "pass_accuracy": _rounded_ratio(match_meta_row.get("pass_accuracy")),
        "crosses_attempted": int(match_meta_row.get("crosses_attempted") or 0),
        "crosses_succeeded": int(match_meta_row.get("crosses_succeeded") or 0),
        "cross_accuracy": _rounded_ratio(match_meta_row.get("cross_accuracy")),
        "duels_won": duels_won,
        "duels_total": duels_total,
        "duel_win_rate": duel_win_rate,
        "interceptions": int(match_meta_row.get("interceptions") or 0),
        "recoveries": int(match_meta_row.get("recoveries") or 0),
        "mistakes": int(match_meta_row.get("mistakes") or 0),
    }


def build_match_detail_leaders(scored_players: pd.DataFrame) -> list[dict[str, Any]]:
    if scored_players.empty:
        return []

    leaders: list[dict[str, Any]] = []
    for metric_key, label, unit in LEADER_SPECS:
        ranked = scored_players.loc[scored_players[metric_key].notna()].copy()
        if ranked.empty:
            continue
        ranked = ranked.sort_values(
            [metric_key, "match_score", "minutes_played", "jersey_number"],
            ascending=[False, False, False, True],
        )
        top = ranked.iloc[0]
        leaders.append(
            {
                "metric_key": metric_key,
                "label": label,
                "player_id": str(top["player_id"]),
                "name": str(top["name"]),
                "jersey_number": int(top["jersey_number"]),
                "position": str(top["position"]),
                "value": float(round(float(top[metric_key]), 2)),
                "unit": unit,
            }
        )
    return leaders


def serialize_match_players(scored_players: pd.DataFrame) -> list[dict[str, Any]]:
    if scored_players.empty:
        return []

    return [
        {
            "match_player_id": str(row["match_player_id"]),
            "player_id": str(row["player_id"]),
            "name": str(row["name"]),
            "jersey_number": int(row["jersey_number"]),
            "position": str(row["position"]),
            "start_position": _nullable_text(row.get("start_position")),
            "substitute_in": _nullable_int(row.get("substitute_in")),
            "substitute_out": _nullable_int(row.get("substitute_out")),
            "minutes_played": int(row["minutes_played"]),
            "goals": int(row["goals"]),
            "assists": int(row["assists"]),
            "shots": int(row["shots"]),
            "shots_on_target": int(row["shots_on_target"]),
            "key_passes": int(row["key_passes"]),
            "pass_accuracy": _rounded_ratio(row.get("pass_accuracy")),
            "duel_win_rate": _rounded_ratio(row.get("duel_win_rate")),
            "recoveries": int(row["recoveries"]),
            "interceptions": int(row["interceptions"]),
            "mistakes": int(row["mistakes"]),
            "yellow_cards": int(row["yellow_cards"]),
            "red_cards": int(row["red_cards"]),
            "total_distance": _rounded_value(row.get("total_distance")),
            "play_time_min": _nullable_int(row.get("play_time_min")),
            "avg_speed": _rounded_value(row.get("avg_speed")),
            "distance_0_15_min": _rounded_value(row.get("distance_0_15_min")),
            "distance_15_30_min": _rounded_value(row.get("distance_15_30_min")),
            "distance_30_45_min": _rounded_value(row.get("distance_30_45_min")),
            "distance_45_60_min": _rounded_value(row.get("distance_45_60_min")),
            "distance_60_75_min": _rounded_value(row.get("distance_60_75_min")),
            "distance_75_90_min": _rounded_value(row.get("distance_75_90_min")),
            "sprint_count": _nullable_int(row.get("sprint_count")),
            "sprint_distance": _rounded_value(row.get("sprint_distance")),
            "distance_speed_0_5": _rounded_value(row.get("distance_speed_0_5")),
            "distance_speed_5_10": _rounded_value(row.get("distance_speed_5_10")),
            "distance_speed_10_15": _rounded_value(row.get("distance_speed_10_15")),
            "distance_speed_15_20": _rounded_value(row.get("distance_speed_15_20")),
            "distance_speed_20_25": _rounded_value(row.get("distance_speed_20_25")),
            "distance_speed_25_plus": _rounded_value(row.get("distance_speed_25_plus")),
            "cod_count": _nullable_int(row.get("cod_count")),
            "max_speed": _rounded_value(row.get("max_speed")),
            "accel_count": _nullable_int(row.get("accel_count")),
            "decel_count": _nullable_int(row.get("decel_count")),
            "hi_accel_count": _nullable_int(row.get("hi_accel_count")),
            "hi_decel_count": _nullable_int(row.get("hi_decel_count")),
            "match_score": _rounded_value(row.get("match_score")),
            "match_score_band": _nullable_text(row.get("match_score_band")),
        }
        for row in scored_players.to_dict("records")
    ]


def _rounded_ratio(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(round(float(value), 4))


def _rounded_value(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(round(float(value), 2))


def _nullable_int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(value)


def _nullable_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    return str(value)
