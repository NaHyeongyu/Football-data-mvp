from __future__ import annotations

from ...schemas import TeamTrainingListResponse, TeamTrainingsSummary
from ..frame_loader import fetch_frame as _fetch_frame
from ..service_reference import SERVICE_REFERENCE_DATE
from .queries import TEAM_TRAININGS_LIST_QUERY
from .transforms import (
    _build_trainings_summary,
    _build_year_options,
    _prepare_trainings_frame,
    _resolve_selected_year,
    _serialize_training_items,
)


def build_team_trainings(year: int | None = None) -> TeamTrainingListResponse:
    trainings = _prepare_trainings_frame(_fetch_frame(TEAM_TRAININGS_LIST_QUERY, (SERVICE_REFERENCE_DATE,)))
    if trainings.empty:
        selected_year = year or SERVICE_REFERENCE_DATE.year
        return TeamTrainingListResponse(
            reference_date=SERVICE_REFERENCE_DATE,
            selected_year=selected_year,
            available_years=[],
            summary=TeamTrainingsSummary(
                training_count=0,
                high_intensity_count=0,
                medium_intensity_count=0,
                low_intensity_count=0,
                average_duration_min=None,
                average_participant_count=None,
                average_total_distance=None,
            ),
            trainings=[],
        )

    available_years = sorted(trainings["year"].dropna().astype(int).unique().tolist())
    selected_year = _resolve_selected_year(available_years, year)
    selected = trainings.loc[trainings["year"] == selected_year].copy()

    return TeamTrainingListResponse(
        reference_date=SERVICE_REFERENCE_DATE,
        selected_year=selected_year,
        available_years=_build_year_options(available_years),
        summary=_build_trainings_summary(selected),
        trainings=_serialize_training_items(selected),
    )


__all__ = ["build_team_trainings"]
