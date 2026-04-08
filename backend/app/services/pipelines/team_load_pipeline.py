from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def build_session_load_frame(
    training_load: pd.DataFrame,
    match_load: pd.DataFrame,
    snapshot_ts: pd.Timestamp,
) -> pd.DataFrame:
    training = training_load.copy()
    if not training.empty:
        training["session_date"] = pd.to_datetime(training["session_date"], errors="coerce")
        training["play_time_min"] = pd.to_numeric(training["play_time_min"], errors="coerce").fillna(0.0)
        training["total_distance"] = pd.to_numeric(training["total_distance"], errors="coerce").fillna(0.0)
        training["sprint_count"] = pd.to_numeric(training["sprint_count"], errors="coerce").fillna(0.0)
        training["hi_accel_count"] = pd.to_numeric(training["hi_accel_count"], errors="coerce").fillna(0.0)
        training["hi_decel_count"] = pd.to_numeric(training["hi_decel_count"], errors="coerce").fillna(0.0)
        training["max_speed"] = pd.to_numeric(training["max_speed"], errors="coerce").fillna(0.0)
        intensity_multiplier = {"low": 0.88, "medium": 1.0, "high": 1.15}
        training["intensity_multiplier"] = training["intensity_level"].map(intensity_multiplier).fillna(1.0)
        training["session_load"] = (
            training["total_distance"] * 18.0
            + training["play_time_min"] * 0.45
            + training["sprint_count"] * 3.0
            + training["hi_accel_count"] * 1.4
            + training["hi_decel_count"] * 1.4
            + training["max_speed"] * 0.18
        ) * training["intensity_multiplier"]

    matches = match_load.copy()
    if not matches.empty:
        matches["session_date"] = pd.to_datetime(matches["session_date"], errors="coerce")
        matches["play_time_min"] = pd.to_numeric(matches["play_time_min"], errors="coerce").fillna(0.0)
        matches["total_distance"] = pd.to_numeric(matches["total_distance"], errors="coerce").fillna(0.0)
        matches["sprint_count"] = pd.to_numeric(matches["sprint_count"], errors="coerce").fillna(0.0)
        matches["hi_accel_count"] = pd.to_numeric(matches["hi_accel_count"], errors="coerce").fillna(0.0)
        matches["hi_decel_count"] = pd.to_numeric(matches["hi_decel_count"], errors="coerce").fillna(0.0)
        matches["max_speed"] = pd.to_numeric(matches["max_speed"], errors="coerce").fillna(0.0)
        matches["session_load"] = (
            matches["total_distance"] * 20.0
            + matches["play_time_min"] * 0.55
            + matches["sprint_count"] * 3.4
            + matches["hi_accel_count"] * 1.8
            + matches["hi_decel_count"] * 1.8
            + matches["max_speed"] * 0.22
        ) * 1.12

    sessions = pd.concat(
        [
            training[
                [
                    "player_id",
                    "session_date",
                    "session_source",
                    "session_load",
                    "play_time_min",
                    "sprint_count",
                    "total_distance",
                ]
            ]
            if not training.empty
            else pd.DataFrame(
                columns=[
                    "player_id",
                    "session_date",
                    "session_source",
                    "session_load",
                    "play_time_min",
                    "sprint_count",
                    "total_distance",
                ]
            ),
            matches[
                [
                    "player_id",
                    "session_date",
                    "session_source",
                    "session_load",
                    "play_time_min",
                    "sprint_count",
                    "total_distance",
                ]
            ]
            if not matches.empty
            else pd.DataFrame(
                columns=[
                    "player_id",
                    "session_date",
                    "session_source",
                    "session_load",
                    "play_time_min",
                    "sprint_count",
                    "total_distance",
                ]
            ),
        ],
        ignore_index=True,
    )
    sessions = sessions[sessions["session_date"].notna()].copy()
    sessions = sessions[sessions["session_date"] <= snapshot_ts].copy()
    sessions["days_ago"] = (snapshot_ts - sessions["session_date"]).dt.days
    return sessions


def summarize_player_load_status(players: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    base["acute_load_7d"] = 0.0
    base["chronic_load_baseline"] = np.nan
    base["acute_chronic_ratio"] = np.nan
    base["sprint_count_7d"] = 0
    base["total_distance_7d"] = 0.0
    base["load_direction"] = "stable"
    base["spike_flag"] = False
    base["drop_flag"] = False

    if sessions.empty:
        return base

    acute_7d = sessions.loc[sessions["days_ago"] <= 6].groupby("player_id")["session_load"].sum()
    baseline_21d = sessions.loc[(sessions["days_ago"] >= 7) & (sessions["days_ago"] <= 27)].groupby("player_id")["session_load"].sum()
    fallback_28d = sessions.loc[sessions["days_ago"] <= 27].groupby("player_id")["session_load"].sum()
    sprint_7d = sessions.loc[sessions["days_ago"] <= 6].groupby("player_id")["sprint_count"].sum()
    distance_7d = sessions.loc[sessions["days_ago"] <= 6].groupby("player_id")["total_distance"].sum()

    base["acute_load_7d"] = base["player_id"].map(acute_7d).fillna(0.0)
    baseline = base["player_id"].map(baseline_21d / 3.0)
    fallback = base["player_id"].map(fallback_28d / 4.0)
    base["chronic_load_baseline"] = baseline.where(baseline.fillna(0) > 0, fallback)
    base["acute_chronic_ratio"] = np.where(
        base["chronic_load_baseline"].fillna(0) > 0,
        base["acute_load_7d"] / base["chronic_load_baseline"],
        np.nan,
    )
    base["sprint_count_7d"] = base["player_id"].map(sprint_7d).fillna(0).round().astype(int)
    base["total_distance_7d"] = base["player_id"].map(distance_7d).fillna(0.0)
    ratio = base["acute_chronic_ratio"].astype(float)
    base["load_direction"] = np.select(
        [ratio >= 1.22, ratio <= 0.78],
        ["spike", "drop"],
        default="stable",
    )
    base["spike_flag"] = ratio >= 1.22
    base["drop_flag"] = ratio <= 0.78
    return base


def build_team_load_trend(
    players: pd.DataFrame,
    sessions: pd.DataFrame,
    player_load_status: pd.DataFrame,
) -> dict[str, Any]:
    if sessions.empty:
        return {
            "load_7d": 0.0,
            "load_14d": 0.0,
            "load_28d": 0.0,
            "match_load_share_28d": 0.0,
            "training_load_share_28d": 0.0,
            "average_sprint_exposure_7d": 0.0,
            "average_total_distance_7d": 0.0,
            "load_spike_player_count": 0,
            "load_drop_player_count": 0,
            "trend_points": [],
        }

    recent_7d = sessions.loc[sessions["days_ago"] <= 6].copy()
    recent_14d = sessions.loc[sessions["days_ago"] <= 13].copy()
    recent_28d = sessions.loc[sessions["days_ago"] <= 27].copy()

    load_7d = float(round(recent_7d["session_load"].sum(), 2))
    load_14d = float(round(recent_14d["session_load"].sum(), 2))
    load_28d = float(round(recent_28d["session_load"].sum(), 2))

    source_totals = recent_28d.groupby("session_source")["session_load"].sum()
    total_28d = float(source_totals.sum())
    match_share = float(round((source_totals.get("match", 0.0) / total_28d) * 100.0, 2)) if total_28d > 0 else 0.0
    training_share = float(round((source_totals.get("training", 0.0) / total_28d) * 100.0, 2)) if total_28d > 0 else 0.0

    roster_size = max(int(len(players)), 1)
    average_sprint_exposure_7d = float(round(player_load_status["sprint_count_7d"].sum() / roster_size, 2))
    average_total_distance_7d = float(round(player_load_status["total_distance_7d"].sum() / roster_size, 2))

    trend_points_frame = (
        recent_28d.groupby(["session_date", "session_source"], as_index=False)
        .agg(
            total_load=("session_load", "sum"),
            sprint_count=("sprint_count", "sum"),
            total_distance=("total_distance", "sum"),
        )
        .sort_values(["session_date", "session_source"])
    )
    trend_points = [
        {
            "session_date": point["session_date"].date(),
            "session_source": point["session_source"],
            "total_load": float(round(point["total_load"], 2)),
            "sprint_count": int(round(point["sprint_count"])),
            "total_distance": float(round(point["total_distance"], 2)),
        }
        for point in trend_points_frame.to_dict("records")
    ]

    return {
        "load_7d": load_7d,
        "load_14d": load_14d,
        "load_28d": load_28d,
        "match_load_share_28d": match_share,
        "training_load_share_28d": training_share,
        "average_sprint_exposure_7d": average_sprint_exposure_7d,
        "average_total_distance_7d": average_total_distance_7d,
        "load_spike_player_count": int(player_load_status["spike_flag"].sum()),
        "load_drop_player_count": int(player_load_status["drop_flag"].sum()),
        "trend_points": trend_points,
    }
