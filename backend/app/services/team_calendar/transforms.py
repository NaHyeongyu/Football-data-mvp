from __future__ import annotations

from datetime import date

import pandas as pd

from ...schemas import (
    TeamCalendarEvent,
    TeamCalendarMonthOption,
    TeamCalendarSummary,
)
from .queries import EVENT_COLUMNS


def _dedupe_training_events(trainings: pd.DataFrame) -> pd.DataFrame:
    if trainings.empty:
        return trainings

    dedupe_columns = [
        "event_date",
        "start_at",
        "end_at",
        "title",
        "category",
        "detail",
        "location",
        "intensity_level",
        "coach_name",
    ]
    # Workbook normalization can leave logically identical training rows with different ids,
    # so the calendar dedupes by visible event attributes.
    return (
        trainings.sort_values(["event_id"], ascending=[False])
        .drop_duplicates(subset=dedupe_columns, keep="first")
        .reset_index(drop=True)
    )


def _month_label(year: int, month: int) -> str:
    return f"{year}년 {month:02d}월"


def _resolve_selected_month(
    available_months: list[tuple[int, int]],
    reference_date: date,
    year: int | None,
    month: int | None,
) -> tuple[int, int]:
    if year is not None and month is not None:
        return year, month

    if (reference_date.year, reference_date.month) in available_months:
        return reference_date.year, reference_date.month

    eligible_months = [
        month_tuple
        for month_tuple in available_months
        if month_tuple <= (reference_date.year, reference_date.month)
    ]
    if eligible_months:
        return eligible_months[-1]

    return reference_date.year, reference_date.month


def _merge_event_frames(matches: pd.DataFrame, trainings: pd.DataFrame) -> pd.DataFrame:
    frames = [frame for frame in [matches, trainings] if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=EVENT_COLUMNS)

    events = pd.concat(
        [frame.dropna(axis=1, how="all") for frame in frames],
        ignore_index=True,
        sort=False,
    ).reindex(columns=EVENT_COLUMNS)
    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
    events["start_at"] = pd.to_datetime(events["start_at"], errors="coerce")
    events["end_at"] = pd.to_datetime(events["end_at"], errors="coerce")
    return events[events["event_date"].notna()].copy()


def _build_calendar_summary(selected_events: pd.DataFrame) -> TeamCalendarSummary:
    return TeamCalendarSummary(
        total_event_count=int(len(selected_events)),
        match_count=int((selected_events["event_type"] == "match").sum()),
        official_match_count=int(
            ((selected_events["event_type"] == "match") & (selected_events["category"] == "공식")).sum()
        ),
        practice_match_count=int(
            ((selected_events["event_type"] == "match") & (selected_events["category"] == "연습")).sum()
        ),
        training_count=int((selected_events["event_type"] == "training").sum()),
        high_intensity_training_count=int(
            ((selected_events["event_type"] == "training") & (selected_events["intensity_level"] == "high")).sum()
        ),
    )


def _build_month_options(available_months: list[tuple[int, int]]) -> list[TeamCalendarMonthOption]:
    return [
        TeamCalendarMonthOption(
            year=option_year,
            month=option_month,
            label=_month_label(option_year, option_month),
        )
        for option_year, option_month in available_months
    ]


def _serialize_event_rows(selected_events: pd.DataFrame) -> list[TeamCalendarEvent]:
    return [
        TeamCalendarEvent(
            event_id=str(row.event_id),
            event_type=str(row.event_type),
            event_date=pd.Timestamp(row.event_date).date(),
            start_at=(pd.Timestamp(row.start_at).to_pydatetime() if pd.notna(row.start_at) else None),
            end_at=(pd.Timestamp(row.end_at).to_pydatetime() if pd.notna(row.end_at) else None),
            title=str(row.title),
            category=str(row.category),
            detail=str(row.detail) if pd.notna(row.detail) else None,
            location=str(row.location) if pd.notna(row.location) else None,
            opponent_team=str(row.opponent_team) if pd.notna(row.opponent_team) else None,
            intensity_level=str(row.intensity_level) if pd.notna(row.intensity_level) else None,
            coach_name=str(row.coach_name) if pd.notna(row.coach_name) else None,
            score_for=int(row.score_for) if pd.notna(row.score_for) else None,
            score_against=int(row.score_against) if pd.notna(row.score_against) else None,
        )
        for row in selected_events.itertuples(index=False)
    ]


__all__ = [
    "_build_calendar_summary",
    "_build_month_options",
    "_dedupe_training_events",
    "_merge_event_frames",
    "_month_label",
    "_resolve_selected_month",
    "_serialize_event_rows",
]
