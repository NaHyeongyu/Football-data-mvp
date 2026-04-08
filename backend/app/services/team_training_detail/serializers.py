from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from .queries import NON_DISPLAY_TRAINING_NOTES, TRAINING_LEADER_SPECS


def _sanitize_training_note(value: Any) -> str | None:
    text = _nullable_text(value)
    if text is None:
        return None

    normalized = text.strip()
    if not normalized or normalized in NON_DISPLAY_TRAINING_NOTES:
        return None
    return normalized


def _prepare_training_players(player_frame: pd.DataFrame) -> pd.DataFrame:
    if player_frame.empty:
        return player_frame.copy()

    frame = player_frame.copy()
    numeric_columns = [
        "jersey_number",
        "play_time_min",
        "total_distance",
        "avg_speed",
        "distance_0_15_min",
        "distance_15_30_min",
        "distance_30_45_min",
        "distance_45_60_min",
        "distance_60_75_min",
        "distance_75_90_min",
        "max_speed",
        "sprint_count",
        "sprint_distance",
        "distance_speed_0_5",
        "distance_speed_5_10",
        "distance_speed_10_15",
        "distance_speed_15_20",
        "distance_speed_20_25",
        "distance_speed_25_plus",
        "accel_count",
        "decel_count",
        "hi_accel_count",
        "hi_decel_count",
        "cod_count",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame.sort_values(
        ["total_distance", "sprint_count", "play_time_min", "jersey_number", "name"],
        ascending=[False, False, False, True, True],
    ).reset_index(drop=True)


def _build_session_duration_minutes(start_at: Any, end_at: Any) -> int | None:
    if start_at is None or end_at is None or pd.isna(start_at) or pd.isna(end_at):
        return None

    start_ts = pd.Timestamp(start_at)
    end_ts = pd.Timestamp(end_at)
    if pd.isna(start_ts) or pd.isna(end_ts) or end_ts <= start_ts:
        return None

    return int(round((end_ts - start_ts).total_seconds() / 60.0))


def _build_training_summary(
    training_meta_row: dict[str, Any],
    players: pd.DataFrame,
) -> dict[str, Any]:
    session_duration_min = _build_session_duration_minutes(
        training_meta_row.get("start_at"),
        training_meta_row.get("end_at"),
    )
    if players.empty:
        return {
            "participant_count": 0,
            "session_duration_min": session_duration_min,
            "average_play_time_min": None,
            "total_distance": None,
            "average_distance": None,
            "total_sprint_count": 0,
            "average_avg_speed": None,
            "average_max_speed": None,
            "total_accel_count": 0,
            "total_decel_count": 0,
            "total_hi_accel_count": 0,
            "total_hi_decel_count": 0,
            "total_cod_count": 0,
        }

    return {
        "participant_count": int(players["player_id"].nunique()),
        "session_duration_min": session_duration_min,
        "average_play_time_min": _rounded_mean(players["play_time_min"]),
        "total_distance": _rounded_sum(players["total_distance"]),
        "average_distance": _rounded_mean(players["total_distance"]),
        "total_sprint_count": _int_sum(players["sprint_count"]),
        "average_avg_speed": _rounded_mean(players["avg_speed"]),
        "average_max_speed": _rounded_mean(players["max_speed"]),
        "total_accel_count": _int_sum(players["accel_count"]),
        "total_decel_count": _int_sum(players["decel_count"]),
        "total_hi_accel_count": _int_sum(players["hi_accel_count"]),
        "total_hi_decel_count": _int_sum(players["hi_decel_count"]),
        "total_cod_count": _int_sum(players["cod_count"]),
    }


def _build_training_leaders(players: pd.DataFrame) -> list[dict[str, Any]]:
    if players.empty:
        return []

    leaders: list[dict[str, Any]] = []
    for metric_key, label, unit in TRAINING_LEADER_SPECS:
        ranked = players.loc[players[metric_key].notna()].copy()
        if ranked.empty:
            continue
        ranked = ranked.sort_values(
            [metric_key, "play_time_min", "jersey_number"],
            ascending=[False, False, True],
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


def _serialize_training_players(players: pd.DataFrame) -> list[dict[str, Any]]:
    if players.empty:
        return []

    return [
        {
            "training_gps_id": str(row["training_gps_id"]),
            "player_id": str(row["player_id"]),
            "name": str(row["name"]),
            "jersey_number": int(row["jersey_number"]),
            "position": str(row["position"]),
            "play_time_min": _rounded_value(row.get("play_time_min")),
            "total_distance": _rounded_value(row.get("total_distance")),
            "avg_speed": _rounded_value(row.get("avg_speed")),
            "distance_0_15_min": _rounded_value(row.get("distance_0_15_min")),
            "distance_15_30_min": _rounded_value(row.get("distance_15_30_min")),
            "distance_30_45_min": _rounded_value(row.get("distance_30_45_min")),
            "distance_45_60_min": _rounded_value(row.get("distance_45_60_min")),
            "distance_60_75_min": _rounded_value(row.get("distance_60_75_min")),
            "distance_75_90_min": _rounded_value(row.get("distance_75_90_min")),
            "max_speed": _rounded_value(row.get("max_speed")),
            "sprint_count": _nullable_int(row.get("sprint_count")),
            "sprint_distance": _rounded_value(row.get("sprint_distance")),
            "distance_speed_0_5": _rounded_value(row.get("distance_speed_0_5")),
            "distance_speed_5_10": _rounded_value(row.get("distance_speed_5_10")),
            "distance_speed_10_15": _rounded_value(row.get("distance_speed_10_15")),
            "distance_speed_15_20": _rounded_value(row.get("distance_speed_15_20")),
            "distance_speed_20_25": _rounded_value(row.get("distance_speed_20_25")),
            "distance_speed_25_plus": _rounded_value(row.get("distance_speed_25_plus")),
            "accel_count": _nullable_int(row.get("accel_count")),
            "decel_count": _nullable_int(row.get("decel_count")),
            "hi_accel_count": _nullable_int(row.get("hi_accel_count")),
            "hi_decel_count": _nullable_int(row.get("hi_decel_count")),
            "cod_count": _nullable_int(row.get("cod_count")),
        }
        for row in players.to_dict("records")
    ]


def _rounded_sum(values: pd.Series) -> float | None:
    if values.dropna().empty:
        return None
    return float(round(values.fillna(0).sum(), 2))


def _rounded_mean(values: pd.Series) -> float | None:
    values = values.dropna()
    if values.empty:
        return None
    return float(round(values.mean(), 2))


def _int_sum(values: pd.Series) -> int:
    if values.dropna().empty:
        return 0
    return int(round(values.fillna(0).sum()))


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


def _nullable_datetime(value: Any) -> datetime | None:
    if value is None or pd.isna(value):
        return None
    return pd.Timestamp(value).to_pydatetime()


__all__ = [
    "_build_training_leaders",
    "_build_training_summary",
    "_nullable_datetime",
    "_nullable_text",
    "_prepare_training_players",
    "_sanitize_training_note",
    "_serialize_training_players",
]
