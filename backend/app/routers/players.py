from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from ..schemas import (
    PlayerDetailResponse,
    PlayerDevelopmentReportResponse,
    PlayerInjuryRiskResponse,
    PlayerListResponse,
    PlayerPerformanceReadinessResponse,
)
from ..services.injury_risk import build_player_injury_risk_report
from ..services.player_insights import (
    build_player_development_report,
    build_player_performance_readiness_report,
)
from ..services.players import get_player_detail, list_players


router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("", response_model=PlayerListResponse)
def get_players(
    q: str | None = Query(default=None, description="Search by player name, player_id, previous team"),
    position: str | None = Query(default=None, description="Primary or secondary position filter"),
    status: str | None = Query(default=None, description="Roster status filter"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PlayerListResponse:
    return list_players(q=q, position=position, status=status, limit=limit, offset=offset)


@router.get("/injury-risk", response_model=PlayerInjuryRiskResponse)
def get_player_injury_risk(
    as_of_date: date | None = Query(default=None, description="Snapshot date. Defaults to the latest date in the dataset."),
    risk_band: str | None = Query(default=None, description="Filter by normal, watch, risk"),
    limit: int | None = Query(default=None, ge=1, le=200),
) -> PlayerInjuryRiskResponse:
    return build_player_injury_risk_report(as_of_date=as_of_date, limit=limit, risk_band=risk_band)


@router.get("/performance-readiness", response_model=PlayerPerformanceReadinessResponse)
def get_player_performance_readiness(
    as_of_date: date | None = Query(default=None, description="Snapshot date. Defaults to the latest date in the dataset."),
    readiness_band: str | None = Query(default=None, description="Filter by ready, managed, watch"),
    limit: int | None = Query(default=None, ge=1, le=200),
) -> PlayerPerformanceReadinessResponse:
    return build_player_performance_readiness_report(
        as_of_date=as_of_date,
        limit=limit,
        readiness_band=readiness_band,
    )


@router.get("/development-report", response_model=PlayerDevelopmentReportResponse)
def get_player_development_report(
    as_of_date: date | None = Query(default=None, description="Snapshot date. Defaults to the latest date in the dataset."),
    growth_band: str | None = Query(default=None, description="Filter by rising, stable, monitor"),
    limit: int | None = Query(default=None, ge=1, le=200),
) -> PlayerDevelopmentReportResponse:
    return build_player_development_report(
        as_of_date=as_of_date,
        limit=limit,
        growth_band=growth_band,
    )


@router.get("/{player_id}", response_model=PlayerDetailResponse)
def get_player(
    player_id: str,
    recent_match_limit: int = Query(default=5, ge=1, le=20),
) -> PlayerDetailResponse:
    return get_player_detail(player_id=player_id, recent_match_limit=recent_match_limit)
