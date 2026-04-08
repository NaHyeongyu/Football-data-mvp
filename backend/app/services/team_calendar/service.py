from __future__ import annotations

from datetime import date

import pandas as pd

from ...schemas import TeamCalendarResponse
from ..frame_loader import fetch_frame as _fetch_frame
from ..service_reference import SERVICE_REFERENCE_DATE
from .queries import MATCH_CALENDAR_QUERY, TRAINING_CALENDAR_QUERY
from .transforms import (
    _build_calendar_summary,
    _build_month_options,
    _dedupe_training_events,
    _merge_event_frames,
    _month_label,
    _resolve_selected_month,
    _serialize_event_rows,
)


def build_team_calendar(
    year: int | None = None,
    month: int | None = None,
    reference_date: date = SERVICE_REFERENCE_DATE,
) -> TeamCalendarResponse:
    matches = _fetch_frame(MATCH_CALENDAR_QUERY, (reference_date,))
    trainings = _dedupe_training_events(_fetch_frame(TRAINING_CALENDAR_QUERY, (reference_date,)))
    events = _merge_event_frames(matches, trainings)

    available_months = sorted(
        {(value.year, value.month) for value in pd.to_datetime(events["event_date"], errors="coerce").dropna()}
    )
    selected_year, selected_month = _resolve_selected_month(
        available_months=available_months,
        reference_date=reference_date,
        year=year,
        month=month,
    )

    selected_events = events[
        (events["event_date"].dt.year == selected_year)
        & (events["event_date"].dt.month == selected_month)
    ].copy()
    selected_events = selected_events.sort_values(
        by=["event_date", "start_at", "event_type", "title"],
        na_position="last",
    )

    return TeamCalendarResponse(
        reference_date=reference_date,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_label=_month_label(selected_year, selected_month),
        available_months=_build_month_options(available_months),
        summary=_build_calendar_summary(selected_events),
        events=_serialize_event_rows(selected_events),
    )


__all__ = ["build_team_calendar"]
