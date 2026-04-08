from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from ..frame_loader import fetch_frame as _fetch_frame


PLAYER_BASE_QUERY = """
SELECT
    player_id,
    name,
    primary_position::text AS primary_position,
    status::text AS status
FROM football.players
"""


TRAINING_LOAD_QUERY = """
SELECT
    tgs.player_id,
    t.training_date AS session_date,
    'training'::text AS session_source,
    t.training_type::text AS training_type,
    t.intensity_level::text AS intensity_level,
    tgs.total_distance,
    tgs.play_time_min,
    tgs.sprint_count,
    tgs.hi_accel_count,
    tgs.hi_decel_count,
    tgs.max_speed
FROM football.training_gps_stats AS tgs
JOIN football.trainings AS t
    ON t.training_id = tgs.training_id
"""


MATCH_LOAD_QUERY = """
SELECT
    mgs.player_id,
    m.match_date AS session_date,
    'match'::text AS session_source,
    NULL::text AS training_type,
    NULL::text AS intensity_level,
    mgs.total_distance,
    COALESCE(pms.minutes_played, mgs.play_time_min)::double precision AS play_time_min,
    mgs.sprint_count,
    mgs.hi_accel_count,
    mgs.hi_decel_count,
    mgs.max_speed,
    pms.minutes_played
FROM football.match_gps_stats AS mgs
JOIN football.matches AS m
    ON m.match_id = mgs.match_id
LEFT JOIN football.player_match_stats AS pms
    ON pms.match_id = mgs.match_id
   AND pms.player_id = mgs.player_id
"""


PHYSICAL_PROFILES_QUERY = """
SELECT
    player_id,
    created_at,
    weight_kg,
    body_fat_percentage,
    muscle_mass_kg
FROM football.physical_profiles
ORDER BY player_id, created_at
"""


INJURIES_QUERY = """
SELECT
    player_id,
    injury_id,
    injury_date,
    injury_type,
    injury_part,
    severity_level::text AS severity_level,
    status::text AS injury_status,
    expected_return_date,
    actual_return_date,
    notes
FROM football.injuries
ORDER BY player_id, injury_date
"""


COUNSELING_NOTES_QUERY = """
SELECT
    player_id,
    counseling_date,
    topic::text AS topic,
    summary
FROM football.counseling_notes
ORDER BY player_id, counseling_date
"""


SYMPTOM_KEYWORDS = (
    "pain",
    "discomfort",
    "tightness",
    "tight",
    "soreness",
    "sore",
    "stiffness",
    "통증",
    "불편",
    "뻐근",
    "요통",
)

REPORT_SORT_COLUMNS = ["overall_risk_score", "injury_history_score", "symptom_score", "load_score", "name"]
MAX_REASON_COUNT = 3


@dataclass(frozen=True)
class InjuryRiskSourceFrames:
    players: pd.DataFrame
    training_load: pd.DataFrame
    match_load: pd.DataFrame
    physical_profiles: pd.DataFrame
    injuries: pd.DataFrame
    counseling_notes: pd.DataFrame


def _contains_symptom_keywords(*values: Any) -> bool:
    for value in values:
        if pd.isna(value):
            continue
        text = str(value).strip().lower()
        if text and any(keyword in text for keyword in SYMPTOM_KEYWORDS):
            return True
    return False


def _optional_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _optional_date(value: Any) -> date | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    if hasattr(value, "date"):
        return value.date()
    return None


def _optional_float(value: Any, digits: int | None = None) -> float | None:
    if value is None or pd.isna(value):
        return None
    number = float(value)
    return round(number, digits) if digits is not None else number


def _optional_int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(value)


def _top_reason_messages(reasons: list[tuple[float, str]], fallback: str) -> list[str]:
    if not reasons:
        return [fallback]
    ordered = sorted(reasons, key=lambda item: item[0], reverse=True)
    return [message for _, message in ordered[:MAX_REASON_COUNT]]


def _filter_ranked_report(report: pd.DataFrame, risk_band: str | None, limit: int | None) -> pd.DataFrame:
    filtered = report
    if risk_band:
        filtered = filtered[filtered["risk_band"] == risk_band.lower()].copy()
    filtered = filtered.sort_values(REPORT_SORT_COLUMNS, ascending=[False, False, False, False, True])
    if limit is not None:
        filtered = filtered.head(limit)
    return filtered


def _load_injury_risk_source_frames() -> InjuryRiskSourceFrames:
    return InjuryRiskSourceFrames(
        players=_fetch_frame(PLAYER_BASE_QUERY),
        training_load=_fetch_frame(TRAINING_LOAD_QUERY),
        match_load=_fetch_frame(MATCH_LOAD_QUERY),
        physical_profiles=_fetch_frame(PHYSICAL_PROFILES_QUERY),
        injuries=_fetch_frame(INJURIES_QUERY),
        counseling_notes=_fetch_frame(COUNSELING_NOTES_QUERY),
    )


def _resolve_snapshot_date(as_of_date: date | None, frames: list[tuple[pd.DataFrame, str]]) -> pd.Timestamp:
    if as_of_date is not None:
        return pd.Timestamp(as_of_date)

    candidates: list[pd.Timestamp] = []
    for frame, column in frames:
        if frame.empty or column not in frame.columns:
            continue
        values = pd.to_datetime(frame[column], errors="coerce").dropna()
        if not values.empty:
            candidates.append(values.max().normalize())

    if not candidates:
        raise RuntimeError("No dated records were found to build an injury-risk snapshot.")

    return max(candidates)


def _resolve_load_snapshot_date(
    training_load: pd.DataFrame,
    match_load: pd.DataFrame,
    snapshot_ts: pd.Timestamp,
) -> pd.Timestamp:
    session_candidates: list[pd.Timestamp] = []
    for frame in [training_load, match_load]:
        if not frame.empty and "session_date" in frame.columns:
            values = pd.to_datetime(frame["session_date"], errors="coerce").dropna()
            if not values.empty:
                session_candidates.append(values.max().normalize())

    if not session_candidates:
        return snapshot_ts

    return min(snapshot_ts, max(session_candidates))


def _build_session_frame(training_load: pd.DataFrame, match_load: pd.DataFrame, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    intensity_multiplier = {"low": 0.88, "medium": 1.0, "high": 1.15}

    training = training_load.copy()
    training["session_date"] = pd.to_datetime(training["session_date"], errors="coerce")
    training["play_time_min"] = pd.to_numeric(training["play_time_min"], errors="coerce").fillna(0.0)
    training["total_distance"] = pd.to_numeric(training["total_distance"], errors="coerce").fillna(0.0)
    training["sprint_count"] = pd.to_numeric(training["sprint_count"], errors="coerce").fillna(0.0)
    training["hi_accel_count"] = pd.to_numeric(training["hi_accel_count"], errors="coerce").fillna(0.0)
    training["hi_decel_count"] = pd.to_numeric(training["hi_decel_count"], errors="coerce").fillna(0.0)
    training["max_speed"] = pd.to_numeric(training["max_speed"], errors="coerce").fillna(0.0)
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
    matches["session_date"] = pd.to_datetime(matches["session_date"], errors="coerce")
    matches["play_time_min"] = pd.to_numeric(matches["play_time_min"], errors="coerce").fillna(0.0)
    matches["minutes_played"] = pd.to_numeric(matches["minutes_played"], errors="coerce").fillna(0.0)
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
                    "training_type",
                    "intensity_level",
                    "session_load",
                    "total_distance",
                    "play_time_min",
                    "sprint_count",
                    "max_speed",
                ]
            ],
            matches[
                [
                    "player_id",
                    "session_date",
                    "session_source",
                    "training_type",
                    "intensity_level",
                    "session_load",
                    "total_distance",
                    "play_time_min",
                    "sprint_count",
                    "max_speed",
                ]
            ],
        ],
        ignore_index=True,
    )

    sessions = sessions[sessions["session_date"].notna()].copy()
    sessions = sessions[sessions["session_date"] <= snapshot_ts]
    sessions["days_ago"] = (snapshot_ts - sessions["session_date"]).dt.days
    return sessions


def _compute_load_features(players: pd.DataFrame, sessions: pd.DataFrame, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    base["acute_distance_7d"] = 0.0
    base["chronic_distance_baseline"] = np.nan
    base["distance_ratio"] = np.nan
    base["sprint_count_baseline"] = np.nan
    if sessions.empty:
        base["acute_load_7d"] = 0.0
        base["chronic_load_baseline"] = np.nan
        base["acute_chronic_ratio"] = np.nan
        base["acute_load_percentile"] = np.nan
        base["high_intensity_sessions_7d"] = 0
        base["match_minutes_7d"] = 0
        base["sprint_count_7d"] = 0
        base["load_score"] = 0.0
        base["load_direction"] = None
        return base

    recent_7d = sessions.loc[sessions["days_ago"] <= 6].copy()
    baseline_window = sessions.loc[(sessions["days_ago"] >= 7) & (sessions["days_ago"] <= 27)].copy()
    fallback_window = sessions.loc[sessions["days_ago"] <= 27].copy()

    acute_7d = recent_7d.groupby("player_id")["session_load"].sum()
    baseline_21d = baseline_window.groupby("player_id")["session_load"].sum()
    fallback_28d = fallback_window.groupby("player_id")["session_load"].sum()

    base["acute_load_7d"] = base["player_id"].map(acute_7d).fillna(0.0)
    baseline = base["player_id"].map(baseline_21d / 3.0)
    fallback = base["player_id"].map(fallback_28d / 4.0)
    base["chronic_load_baseline"] = baseline.where(baseline.fillna(0) > 0, fallback)
    base["acute_chronic_ratio"] = np.where(
        base["chronic_load_baseline"].fillna(0) > 0,
        base["acute_load_7d"] / base["chronic_load_baseline"],
        np.nan,
    )

    acute_distance_7d = recent_7d.groupby("player_id")["total_distance"].sum()
    baseline_distance_21d = baseline_window.groupby("player_id")["total_distance"].sum()
    fallback_distance_28d = fallback_window.groupby("player_id")["total_distance"].sum()
    base["acute_distance_7d"] = base["player_id"].map(acute_distance_7d).fillna(0.0)
    distance_baseline = base["player_id"].map(baseline_distance_21d / 3.0)
    distance_fallback = base["player_id"].map(fallback_distance_28d / 4.0)
    base["chronic_distance_baseline"] = distance_baseline.where(distance_baseline.fillna(0) > 0, distance_fallback)
    base["distance_ratio"] = np.where(
        base["chronic_distance_baseline"].fillna(0) > 0,
        base["acute_distance_7d"] / base["chronic_distance_baseline"],
        np.nan,
    )

    recent_training = sessions.loc[(sessions["session_source"] == "training") & (sessions["days_ago"] <= 6)]
    high_sessions = recent_training.loc[recent_training["intensity_level"] == "high"].groupby("player_id").size()
    base["high_intensity_sessions_7d"] = base["player_id"].map(high_sessions).fillna(0).astype(int)

    recent_matches = sessions.loc[(sessions["session_source"] == "match") & (sessions["days_ago"] <= 6)]
    match_minutes = recent_matches.groupby("player_id")["play_time_min"].sum()
    base["match_minutes_7d"] = base["player_id"].map(match_minutes).fillna(0).round().astype(int)
    sprint_counts = recent_7d.groupby("player_id")["sprint_count"].sum()
    base["sprint_count_7d"] = base["player_id"].map(sprint_counts).fillna(0).round().astype(int)
    baseline_sprint_21d = baseline_window.groupby("player_id")["sprint_count"].sum()
    fallback_sprint_28d = fallback_window.groupby("player_id")["sprint_count"].sum()
    sprint_baseline = base["player_id"].map(baseline_sprint_21d / 3.0)
    sprint_fallback = base["player_id"].map(fallback_sprint_28d / 4.0)
    base["sprint_count_baseline"] = sprint_baseline.where(sprint_baseline.fillna(0) > 0, sprint_fallback)
    base["sprint_ratio"] = np.where(
        base["sprint_count_baseline"].fillna(0) > 0,
        base["sprint_count_7d"] / base["sprint_count_baseline"],
        np.nan,
    )

    active_load = base.loc[base["acute_load_7d"] > 0, "acute_load_7d"]
    if active_load.empty:
        base["acute_load_percentile"] = np.nan
    else:
        base["acute_load_percentile"] = np.where(
            base["acute_load_7d"] > 0,
            base["acute_load_7d"].rank(method="average", pct=True) * 100.0,
            np.nan,
        )

    active_sprint = base.loc[base["sprint_count_7d"] > 0, "sprint_count_7d"]
    if active_sprint.empty:
        sprint_percentile = pd.Series(np.nan, index=base.index, dtype=float)
    else:
        sprint_percentile = pd.Series(
            np.where(
                base["sprint_count_7d"] > 0,
                base["sprint_count_7d"].rank(method="average", pct=True) * 100.0,
                np.nan,
            ),
            index=base.index,
            dtype=float,
        )

    ratio = base["acute_chronic_ratio"].astype(float)
    distance_ratio = pd.to_numeric(base["distance_ratio"], errors="coerce")
    sprint_ratio = pd.to_numeric(base["sprint_ratio"], errors="coerce")
    non_gk_mask = base["player_id"].map(players.set_index("player_id")["primary_position"]).ne("GK").fillna(True)

    overload_signal = np.clip((ratio - 1.15) / 0.35, 0, 1)
    underload_signal = np.where(
        non_gk_mask,
        np.maximum(
            np.clip((0.88 - ratio) / 0.22, 0, 1),
            np.clip((0.9 - distance_ratio) / 0.22, 0, 1),
        ),
        0.0,
    )
    acute_load_signal = np.clip((base["acute_load_percentile"].fillna(0.0) - 72.0) / 28.0, 0, 1)
    sprint_volume_signal = np.clip((sprint_percentile.fillna(0.0) - 75.0) / 25.0, 0, 1)
    sprint_spike_signal = np.where(
        (base["sprint_count_baseline"].fillna(0.0) >= 18.0) & (base["sprint_count_7d"] >= 35),
        np.clip((sprint_ratio - 1.15) / 0.3, 0, 1),
        0.0,
    )
    high_intensity_signal = np.clip((base["high_intensity_sessions_7d"] - 2) / 2, 0, 1)
    minutes_signal = np.clip((base["match_minutes_7d"] - 120) / 120, 0, 1)

    # Load risk blends spike, drop, and absolute exposure so both overload and sudden de-loading surface.
    combined_load_signal = np.clip(
        0.3 * np.nan_to_num(np.maximum(overload_signal, underload_signal), nan=0.0)
        + 0.2 * acute_load_signal
        + 0.2 * np.nan_to_num(sprint_spike_signal, nan=0.0)
        + 0.12 * sprint_volume_signal
        + 0.1 * high_intensity_signal
        + 0.08 * minutes_signal,
        0,
        1,
    )
    base["load_score"] = np.round(combined_load_signal * 36.0, 2)

    base["load_direction"] = np.select(
        [
            (ratio >= 1.22) | (sprint_ratio >= 1.25),
            non_gk_mask & ((ratio <= 0.82) | (distance_ratio <= 0.82)),
        ],
        ["spike", "drop"],
        default="stable",
    )
    return base
