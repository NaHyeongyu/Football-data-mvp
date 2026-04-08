from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from ..pipelines.match_score_pipeline import prepare_objective_match_scores
from ..service_reference import SERVICE_REFERENCE_DATE
from .queries import FRONTEND_MAX_SEASON_YEAR, FRONTEND_MIN_SEASON_YEAR


def _safe_float(value: Any, digits: int | None = None) -> float | None:
    if value is None or pd.isna(value):
        return None
    numeric = float(value)
    return round(numeric, digits) if digits is not None else numeric


def _safe_int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(round(float(value)))


def _season_year_for_date(value: Any) -> int:
    timestamp = pd.Timestamp(value)
    return int(timestamp.year if timestamp.month >= 3 else timestamp.year - 1)


def _season_id_for_date(value: Any) -> str:
    return f"S{_season_year_for_date(value)}"


def _is_supported_season_year(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    season_year = int(value)
    return FRONTEND_MIN_SEASON_YEAR <= season_year <= FRONTEND_MAX_SEASON_YEAR


def _filter_supported_season_frame(frame: pd.DataFrame, *, date_column: str | None = None) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    filtered = frame.copy()
    if "season_year" not in filtered.columns:
        if date_column is None:
            raise ValueError("date_column is required when season_year is missing")
        filtered[date_column] = pd.to_datetime(filtered[date_column], errors="coerce")
        filtered = filtered[filtered[date_column].notna()].copy()
        filtered["season_year"] = filtered[date_column].apply(_season_year_for_date)

    return filtered[filtered["season_year"].apply(_is_supported_season_year)].copy()


def _position_group(position: str | None) -> str | None:
    if not position:
        return None

    normalized = position.upper()
    if normalized == "GK":
        return "GK"
    if normalized in {"CB", "LB", "RB", "WB", "LWB", "RWB", "DF"}:
        return "DF"
    if normalized in {"DM", "CM", "AM", "LM", "RM", "LW", "RW", "MF"}:
        return "MF"
    if normalized in {"ST", "CF", "FW"}:
        return "FW"
    return normalized


def _age_today(date_of_birth: Any, reference_date: date = SERVICE_REFERENCE_DATE) -> float | None:
    if date_of_birth is None or pd.isna(date_of_birth):
        return None
    years = (pd.Timestamp(reference_date) - pd.Timestamp(date_of_birth)).days / 365.25
    return round(years, 1)


def _grade_from_age(age_today: float | None) -> int | None:
    if age_today is None:
        return None
    return max(1, min(3, int(age_today) - 15))


def _result_label(goals_for: Any, goals_against: Any) -> str:
    scored = int(goals_for or 0)
    conceded = int(goals_against or 0)
    if scored > conceded:
        return "승"
    if scored < conceded:
        return "패"
    return "무"


def _score_label(goals_for: Any, goals_against: Any) -> str:
    return f"{int(goals_for or 0)} - {int(goals_against or 0)}"


def _compute_match_player_load_series(frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype="float64")

    total_distance = pd.to_numeric(frame["total_distance"], errors="coerce")
    play_time_min = pd.to_numeric(frame["play_time_min"], errors="coerce")
    sprint_count = pd.to_numeric(frame["sprint_count"], errors="coerce")
    hi_accel_count = pd.to_numeric(frame["hi_accel_count"], errors="coerce")
    hi_decel_count = pd.to_numeric(frame["hi_decel_count"], errors="coerce")
    max_speed = pd.to_numeric(frame["max_speed"], errors="coerce")

    base_load = (
        total_distance.fillna(0.0) * 20.0
        + play_time_min.fillna(0.0) * 0.55
        + sprint_count.fillna(0.0) * 3.4
        + hi_accel_count.fillna(0.0) * 1.8
        + hi_decel_count.fillna(0.0) * 1.8
        + max_speed.fillna(0.0) * 0.22
    )
    has_signal = total_distance.notna() | play_time_min.notna() | sprint_count.notna()
    return (base_load * 1.12).round(1).where(has_signal)


def _match_no_map(match_frame: pd.DataFrame) -> dict[str, int]:
    if match_frame.empty:
        return {}

    unique_matches = (
        match_frame[["match_id", "match_date", "season_year"]]
        .drop_duplicates()
        .sort_values(["season_year", "match_date", "match_id"], ascending=[True, True, True])
    )
    result: dict[str, int] = {}
    for _, season_group in unique_matches.groupby("season_year", sort=True):
        for index, row in enumerate(season_group.itertuples(index=False), start=1):
            result[str(row.match_id)] = index
    return result


def _prepare_match_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    prepared = frame.copy()
    prepared["match_date"] = pd.to_datetime(prepared["match_date"], errors="coerce")
    prepared = prepared[prepared["match_date"].notna()].copy()
    prepared["season_year"] = prepared["match_date"].apply(_season_year_for_date)
    prepared["season_id"] = prepared["match_date"].apply(_season_id_for_date)
    prepared["player_load"] = _compute_match_player_load_series(prepared)
    prepared["distance_high_speed_m"] = pd.to_numeric(prepared["sprint_distance"], errors="coerce").round(1)
    prepared = prepare_objective_match_scores(prepared)
    prepared["impact_score"] = prepared["match_score"].apply(
        lambda value: round(float(value) / 25.0, 3) if value is not None and not pd.isna(value) else 0.0,
    )
    prepared["match_no"] = prepared["match_id"].map(_match_no_map(prepared)).astype(int)
    return prepared.sort_values(["match_date", "match_player_id"], ascending=[False, False]).copy()


def _prepare_physical_tests_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    prepared = frame.copy()
    prepared["test_date"] = pd.to_datetime(prepared["test_date"], errors="coerce")
    prepared = prepared[prepared["test_date"].notna()].copy()
    prepared["season_year"] = prepared["test_date"].apply(_season_year_for_date)
    prepared["season_id"] = prepared["test_date"].apply(_season_id_for_date)
    return _filter_supported_season_frame(prepared)


__all__ = [
    "_age_today",
    "_filter_supported_season_frame",
    "_grade_from_age",
    "_position_group",
    "_prepare_match_frame",
    "_prepare_physical_tests_frame",
    "_result_label",
    "_safe_float",
    "_safe_int",
    "_score_label",
    "_season_id_for_date",
    "_season_year_for_date",
]
