from __future__ import annotations

from ...schemas import TeamMatchListResponse, TeamMatchesSummary
from ..frame_loader import fetch_frame as _fetch_frame
from ..service_reference import SERVICE_REFERENCE_DATE
from .queries import TEAM_MATCHES_LIST_QUERY
from .transforms import (
    _build_matches_summary,
    _build_year_options,
    _prepare_matches_frame,
    _resolve_selected_year,
    _serialize_match_items,
)


def build_team_matches(year: int | None = None) -> TeamMatchListResponse:
    matches = _prepare_matches_frame(_fetch_frame(TEAM_MATCHES_LIST_QUERY, (SERVICE_REFERENCE_DATE,)))
    if matches.empty:
        selected_year = year or SERVICE_REFERENCE_DATE.year
        return TeamMatchListResponse(
            reference_date=SERVICE_REFERENCE_DATE,
            selected_year=selected_year,
            available_years=[],
            summary=TeamMatchesSummary(
                match_count=0,
                official_match_count=0,
                practice_match_count=0,
                win_count=0,
                draw_count=0,
                loss_count=0,
                average_match_score=None,
            ),
            matches=[],
        )

    available_years = sorted(matches["year"].dropna().astype(int).unique().tolist())
    selected_year = _resolve_selected_year(available_years, year)
    selected = matches.loc[matches["year"] == selected_year].copy()

    return TeamMatchListResponse(
        reference_date=SERVICE_REFERENCE_DATE,
        selected_year=selected_year,
        available_years=_build_year_options(available_years),
        summary=_build_matches_summary(selected),
        matches=_serialize_match_items(selected),
    )


__all__ = ["build_team_matches"]
