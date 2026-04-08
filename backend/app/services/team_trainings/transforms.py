from __future__ import annotations

from typing import Any

import pandas as pd

from ...schemas import (
    TeamTrainingListItem,
    TeamTrainingsSummary,
    TeamTrainingYearOption,
)
from ..service_reference import SERVICE_REFERENCE_DATE


def _resolve_selected_year(available_years: list[int], year: int | None) -> int:
    if year is not None:
        return year
    if SERVICE_REFERENCE_DATE.year in available_years:
        return SERVICE_REFERENCE_DATE.year
    if available_years:
        return available_years[-1]
    return SERVICE_REFERENCE_DATE.year


def _session_duration_minutes(start_at: Any, end_at: Any) -> int | None:
    if start_at is None or end_at is None or pd.isna(start_at) or pd.isna(end_at):
        return None

    start_ts = pd.Timestamp(start_at)
    end_ts = pd.Timestamp(end_at)
    if pd.isna(start_ts) or pd.isna(end_ts) or end_ts <= start_ts:
        return None

    return int(round((end_ts - start_ts).total_seconds() / 60.0))


def _rounded_average(values: pd.Series, digits: int) -> float | None:
    numeric_values = pd.to_numeric(values, errors="coerce").dropna()
    if numeric_values.empty:
        return None
    return float(round(float(numeric_values.mean()), digits))


def _nullable_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    return str(value)


def _dedupe_trainings(trainings: pd.DataFrame) -> pd.DataFrame:
    if trainings.empty:
        return trainings

    dedupe_columns = [
        "training_date",
        "session_name",
        "training_type",
        "training_focus",
        "intensity_level",
        "coach_name",
        "location",
        "start_at",
        "end_at",
    ]
    # Normalized workbook loads can keep multiple ids for the same visible session,
    # so the list view dedupes on the fields the frontend actually shows.
    return (
        trainings.sort_values(["training_id"], ascending=[False])
        .drop_duplicates(subset=dedupe_columns, keep="first")
        .reset_index(drop=True)
    )


def _prepare_trainings_frame(trainings: pd.DataFrame) -> pd.DataFrame:
    if trainings.empty:
        return trainings.copy()

    prepared = trainings.copy()
    prepared["training_date"] = pd.to_datetime(prepared["training_date"], errors="coerce")
    prepared["start_at"] = pd.to_datetime(prepared["start_at"], errors="coerce")
    prepared["end_at"] = pd.to_datetime(prepared["end_at"], errors="coerce")
    prepared["participant_count"] = pd.to_numeric(prepared["participant_count"], errors="coerce")
    prepared["total_distance"] = pd.to_numeric(prepared["total_distance"], errors="coerce")
    prepared = prepared[prepared["training_date"].notna()].copy()
    prepared = _dedupe_trainings(prepared)
    prepared["session_duration_min"] = [
        _session_duration_minutes(start_at, end_at)
        for start_at, end_at in zip(prepared["start_at"], prepared["end_at"], strict=False)
    ]
    prepared["year"] = prepared["training_date"].dt.year.astype(int)
    return prepared.sort_values(
        ["training_date", "start_at", "training_id"],
        ascending=[False, False, False],
    )


def _build_trainings_summary(selected: pd.DataFrame) -> TeamTrainingsSummary:
    high_intensity_mask = selected["intensity_level"].isin(["high", "very_high"])
    return TeamTrainingsSummary(
        training_count=int(len(selected)),
        high_intensity_count=int(high_intensity_mask.sum()),
        medium_intensity_count=int((selected["intensity_level"] == "medium").sum()),
        low_intensity_count=int((selected["intensity_level"] == "low").sum()),
        average_duration_min=_rounded_average(selected["session_duration_min"], 1),
        average_participant_count=_rounded_average(selected["participant_count"], 1),
        average_total_distance=_rounded_average(selected["total_distance"], 2),
    )


def _build_year_options(available_years: list[int]) -> list[TeamTrainingYearOption]:
    return [TeamTrainingYearOption(year=item, label=f"{item} Season") for item in available_years]


def _serialize_training_items(selected: pd.DataFrame) -> list[TeamTrainingListItem]:
    return [
        TeamTrainingListItem(
            training_id=str(row.training_id),
            training_date=pd.Timestamp(row.training_date).date(),
            session_name=str(row.session_name),
            training_type=str(row.training_type),
            training_focus=_nullable_text(row.training_focus),
            intensity_level=_nullable_text(row.intensity_level),
            coach_name=_nullable_text(row.coach_name),
            location=_nullable_text(row.location),
            start_at=pd.Timestamp(row.start_at).to_pydatetime() if pd.notna(row.start_at) else None,
            end_at=pd.Timestamp(row.end_at).to_pydatetime() if pd.notna(row.end_at) else None,
            session_duration_min=None if pd.isna(row.session_duration_min) else int(row.session_duration_min),
            participant_count=None if pd.isna(row.participant_count) else int(row.participant_count),
            total_distance=None if pd.isna(row.total_distance) else float(round(float(row.total_distance), 2)),
        )
        for row in selected.itertuples(index=False)
    ]


__all__ = [
    "_build_trainings_summary",
    "_build_year_options",
    "_prepare_trainings_frame",
    "_resolve_selected_year",
    "_serialize_training_items",
]
