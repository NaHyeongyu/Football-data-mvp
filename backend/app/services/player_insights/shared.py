from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from ..frame_loader import fetch_frame as _fetch_frame
from ..pipelines.match_score_pipeline import prepare_objective_match_scores


PLAYER_BASE_QUERY = """
SELECT
    player_id,
    name,
    primary_position::text AS primary_position,
    status::text AS status
FROM football.players
"""


MATCH_INSIGHTS_QUERY = """
SELECT
    pms.match_player_id,
    pms.player_id,
    m.match_date,
    pms.minutes_played,
    pms.goals,
    pms.assists,
    pms.shots_on_target,
    pms.key_passes,
    pms.pass_accuracy,
    pms.mistakes,
    pms.yellow_cards,
    pms.red_cards,
    pms.aerial_duels_won,
    pms.aerial_duels_total,
    pms.ground_duels_won,
    pms.ground_duels_total,
    mgs.total_distance,
    mgs.max_speed,
    mgs.sprint_count
FROM football.player_match_stats AS pms
JOIN football.matches AS m
    ON m.match_id = pms.match_id
LEFT JOIN football.match_gps_stats AS mgs
    ON mgs.match_id = pms.match_id
   AND mgs.player_id = pms.player_id
"""


EVALUATIONS_QUERY = """
SELECT
    player_id,
    evaluation_date,
    technical,
    tactical,
    physical,
    mental,
    coach_comment
FROM football.evaluations
ORDER BY player_id, evaluation_date
"""


COUNSELING_QUERY = """
SELECT
    player_id,
    counseling_date,
    topic::text AS topic,
    summary
FROM football.counseling_notes
ORDER BY player_id, counseling_date
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


POSITIVE_COMMENT_KEYWORDS = ("좋아지고", "향상", "우수", "안정", "자신감 회복", "회복")
NEGATIVE_COMMENT_KEYWORDS = ("개선 필요", "저하", "부족", "미흡", "불안", "기복")
MAX_REASON_COUNT = 3


@dataclass(frozen=True)
class ReadinessSourceFrames:
    players: pd.DataFrame
    match_stats: pd.DataFrame
    evaluations: pd.DataFrame
    counseling: pd.DataFrame


@dataclass(frozen=True)
class DevelopmentSourceFrames:
    players: pd.DataFrame
    match_stats: pd.DataFrame
    evaluations: pd.DataFrame
    physical_profiles: pd.DataFrame


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
        raise RuntimeError("No dated records were found to build the player insight snapshot.")

    return max(candidates)


def _build_match_frame(match_stats: pd.DataFrame, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    if match_stats.empty:
        return match_stats.copy()

    frame = match_stats.copy()
    frame["match_date"] = pd.to_datetime(frame["match_date"], errors="coerce")
    frame = frame[frame["match_date"].notna() & (frame["match_date"] <= snapshot_ts)].copy()
    # Objective match scores collapse raw stat lines into one comparable form metric.
    frame = prepare_objective_match_scores(frame)
    frame["form_index"] = frame["match_score"]
    return frame


def _score_text_signal(text: str, positive_keywords: tuple[str, ...], negative_keywords: tuple[str, ...]) -> float:
    score = 0.0
    normalized = text.strip()
    if not normalized:
        return score
    for keyword in positive_keywords:
        if keyword in normalized:
            score += 1.0
    for keyword in negative_keywords:
        if keyword in normalized:
            score -= 1.2
    return score


def _optional_float(value: Any, digits: int | None = None) -> float | None:
    if pd.isna(value):
        return None
    number = float(value)
    return round(number, digits) if digits is not None else number


def _optional_int(value: Any) -> int | None:
    if pd.isna(value):
        return None
    return int(value)


def _optional_date(value: Any) -> date | None:
    if pd.isna(value):
        return None
    return pd.Timestamp(value).date()


def _rank_percentile(values: pd.Series) -> pd.Series:
    if values.dropna().empty:
        return pd.Series(np.nan, index=values.index, dtype=float)
    return values.rank(method="average", pct=True).fillna(0.0)


def _merge_player_features(players: pd.DataFrame, *feature_frames: pd.DataFrame) -> pd.DataFrame:
    report = players.copy()
    for frame in feature_frames:
        report = report.merge(frame, on="player_id", how="left")
    return report


def _top_reason_messages(reasons: list[tuple[float, str]], fallback: str) -> list[str]:
    if not reasons:
        return [fallback]
    ordered = sorted(reasons, key=lambda item: item[0], reverse=True)
    return [message for _, message in ordered[:MAX_REASON_COUNT]]


def _filter_ranked_report(
    report: pd.DataFrame,
    band_column: str,
    band_value: str | None,
    sort_columns: list[str],
    limit: int | None,
) -> pd.DataFrame:
    filtered = report
    if band_value:
        filtered = filtered[filtered[band_column] == band_value.lower()].copy()
    filtered = filtered.sort_values(sort_columns, ascending=[False, False, False, True])
    if limit is not None:
        filtered = filtered.head(limit)
    return filtered


def _load_readiness_source_frames() -> ReadinessSourceFrames:
    return ReadinessSourceFrames(
        players=_fetch_frame(PLAYER_BASE_QUERY),
        match_stats=_fetch_frame(MATCH_INSIGHTS_QUERY),
        evaluations=_fetch_frame(EVALUATIONS_QUERY),
        counseling=_fetch_frame(COUNSELING_QUERY),
    )


def _load_development_source_frames() -> DevelopmentSourceFrames:
    return DevelopmentSourceFrames(
        players=_fetch_frame(PLAYER_BASE_QUERY),
        match_stats=_fetch_frame(MATCH_INSIGHTS_QUERY),
        evaluations=_fetch_frame(EVALUATIONS_QUERY),
        physical_profiles=_fetch_frame(PHYSICAL_PROFILES_QUERY),
    )


def _compute_match_form_features(players: pd.DataFrame, match_frame: pd.DataFrame) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    columns = {
        "recent_form_index": np.nan,
        "previous_form_index": np.nan,
        "form_delta": np.nan,
        "recent_match_count": 0,
        "recent_match_minutes_avg": np.nan,
        "recent_distance_avg": np.nan,
        "previous_distance_avg": np.nan,
        "recent_sprint_avg": np.nan,
        "previous_sprint_avg": np.nan,
        "recent_max_speed_avg": np.nan,
        "previous_max_speed_avg": np.nan,
        "latest_match_date": pd.NaT,
        "match_form_score": 0.0,
    }
    for column, default in columns.items():
        base[column] = default

    if match_frame.empty:
        return base

    # Compare the latest five appearances against the prior five to capture current level and direction.
    recent = match_frame.loc[match_frame["match_rank"] <= 5].copy()
    previous = match_frame.loc[(match_frame["match_rank"] >= 6) & (match_frame["match_rank"] <= 10)].copy()

    recent_agg = recent.groupby("player_id").agg(
        recent_form_index=("form_index", "mean"),
        recent_match_count=("form_index", "size"),
        recent_match_minutes_avg=("minutes_played", "mean"),
        recent_distance_avg=("total_distance", "mean"),
        recent_sprint_avg=("sprint_count", "mean"),
        recent_max_speed_avg=("max_speed", "mean"),
        latest_match_date=("match_date", "max"),
    )
    previous_agg = previous.groupby("player_id").agg(
        previous_form_index=("form_index", "mean"),
        previous_distance_avg=("total_distance", "mean"),
        previous_sprint_avg=("sprint_count", "mean"),
        previous_max_speed_avg=("max_speed", "mean"),
    )

    base = base.merge(recent_agg, on="player_id", how="left", suffixes=("", "_recent"))
    base = base.merge(previous_agg, on="player_id", how="left", suffixes=("", "_previous"))

    for column in recent_agg.columns:
        merged = f"{column}_recent"
        if merged in base.columns:
            base[column] = base[merged].combine_first(base[column])
            base = base.drop(columns=[merged])
    for column in previous_agg.columns:
        merged = f"{column}_previous"
        if merged in base.columns:
            base[column] = base[merged].combine_first(base[column])
            base = base.drop(columns=[merged])

    base["form_delta"] = base["recent_form_index"] - base["previous_form_index"]
    form_signal = _rank_percentile(base["recent_form_index"])
    trend_signal = np.clip((base["form_delta"].fillna(0.0) + 6.0) / 18.0, 0, 1)
    minutes_signal = np.clip(base["recent_match_minutes_avg"].fillna(0.0) / 75.0, 0, 1)
    activity_signal = np.clip(base["recent_match_count"].fillna(0.0) / 4.0, 0, 1)

    base["match_form_score"] = np.round(
        np.clip(
            0.5 * form_signal
            + 0.25 * trend_signal
            + 0.15 * minutes_signal
            + 0.1 * activity_signal,
            0,
            1,
        )
        * 45.0,
        2,
    )
    base["recent_match_count"] = base["recent_match_count"].fillna(0).astype(int)
    return base


def _compute_evaluation_features(players: pd.DataFrame, evaluations: pd.DataFrame) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    base["latest_evaluation_average"] = np.nan
    base["previous_evaluation_average"] = np.nan
    base["evaluation_delta"] = np.nan
    base["latest_evaluation_date"] = pd.NaT
    base["comment_signal"] = 0.0
    base["evaluation_score"] = 0.0

    if evaluations.empty:
        return base

    frame = evaluations.copy()
    frame["evaluation_date"] = pd.to_datetime(frame["evaluation_date"], errors="coerce")
    for column in ["technical", "tactical", "physical", "mental"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["evaluation_average"] = frame[["technical", "tactical", "physical", "mental"]].mean(axis=1)
    frame = frame.sort_values(["player_id", "evaluation_date"], ascending=[True, False]).copy()

    latest = frame.groupby("player_id").head(1).copy()
    latest["comment_signal"] = latest["coach_comment"].fillna("").apply(
        lambda text: _score_text_signal(
            text,
            positive_keywords=POSITIVE_COMMENT_KEYWORDS,
            negative_keywords=NEGATIVE_COMMENT_KEYWORDS,
        )
    )
    previous = frame.loc[frame.groupby("player_id").cumcount() == 1, ["player_id", "evaluation_average"]].rename(
        columns={"evaluation_average": "previous_evaluation_average"}
    )

    latest_indexed = latest.set_index("player_id")
    previous_indexed = previous.set_index("player_id")
    base["latest_evaluation_average"] = base["player_id"].map(latest_indexed["evaluation_average"])
    base["latest_evaluation_date"] = base["player_id"].map(latest_indexed["evaluation_date"])
    base["comment_signal"] = base["player_id"].map(latest_indexed["comment_signal"]).fillna(0.0)
    base["previous_evaluation_average"] = base["player_id"].map(previous_indexed["previous_evaluation_average"])
    base["evaluation_delta"] = base["latest_evaluation_average"] - base["previous_evaluation_average"]

    # Evaluation scoring blends level, short-term trend, and the tone of the latest coach note.
    eval_percentile = _rank_percentile(base["latest_evaluation_average"])
    trend_signal = np.clip((base["evaluation_delta"].fillna(0.0) + 4.0) / 12.0, 0, 1)
    comment_signal = np.clip((base["comment_signal"].fillna(0.0) + 2.0) / 4.0, 0, 1)
    base["evaluation_score"] = np.round(
        np.clip(
            0.65 * eval_percentile
            + 0.25 * trend_signal
            + 0.1 * comment_signal,
            0,
            1,
        )
        * 35.0,
        2,
    )
    return base
