from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from ..schemas import (
    TeamCalendarResponse,
    TeamMatchDetailResponse,
    TeamMatchListResponse,
    TeamOverviewResponse,
    TeamTrainingDetailResponse,
    TeamTrainingListResponse,
)
from ..services.team_calendar import build_team_calendar
from ..services.team_dashboard import build_team_overview
from ..services.team_match_detail import get_team_match_detail
from ..services.team_matches import build_team_matches
from ..services.team_training_detail import get_team_training_detail
from ..services.team_trainings import build_team_trainings


router = APIRouter(prefix="/api/team", tags=["team"])


@router.get("/overview", response_model=TeamOverviewResponse)
def get_team_overview(
    as_of_date: date | None = Query(default=None, description="Snapshot date. Defaults to the latest date in the dataset."),
) -> TeamOverviewResponse:
    return build_team_overview(as_of_date=as_of_date)


@router.get("/calendar", response_model=TeamCalendarResponse)
def get_team_calendar(
    year: int | None = Query(default=None, ge=2023, le=2025),
    month: int | None = Query(default=None, ge=1, le=12),
) -> TeamCalendarResponse:
    return build_team_calendar(year=year, month=month)


@router.get("/matches", response_model=TeamMatchListResponse)
def get_team_matches(
    year: int | None = Query(default=None, ge=2023, le=2025),
) -> TeamMatchListResponse:
    return build_team_matches(year=year)


@router.get("/trainings", response_model=TeamTrainingListResponse)
def get_team_trainings(
    year: int | None = Query(default=None, ge=2023, le=2025),
) -> TeamTrainingListResponse:
    return build_team_trainings(year=year)


@router.get("/matches/{match_id}", response_model=TeamMatchDetailResponse)
def get_team_match(match_id: str) -> TeamMatchDetailResponse:
    return get_team_match_detail(match_id=match_id)


@router.get("/training/{training_id}", response_model=TeamTrainingDetailResponse)
def get_team_training(training_id: str) -> TeamTrainingDetailResponse:
    return get_team_training_detail(training_id=training_id)
