from __future__ import annotations

from fastapi import HTTPException

from ...schemas import (
    TeamMatchDetailResponse,
    TeamMatchDetailSummary,
    TeamMatchDetailTeamStats,
)
from ..frame_loader import fetch_frame as _fetch_frame
from ..pipelines.team_match_detail_pipeline import (
    build_match_detail_leaders,
    build_match_detail_summary,
    build_match_detail_team_stats,
    prepare_match_detail_players,
    serialize_match_players,
)
from ..service_reference import SERVICE_REFERENCE_DATE
from .queries import MATCH_META_QUERY, MATCH_PLAYERS_QUERY
from .serializers import _build_match_meta


def get_team_match_detail(match_id: str) -> TeamMatchDetailResponse:
    match_meta_frame = _fetch_frame(MATCH_META_QUERY, (match_id, SERVICE_REFERENCE_DATE))
    if match_meta_frame.empty:
        raise HTTPException(status_code=404, detail="Match not found")

    player_frame = _fetch_frame(MATCH_PLAYERS_QUERY, (match_id, SERVICE_REFERENCE_DATE))
    scored_players = prepare_match_detail_players(player_frame)

    match_meta_row = match_meta_frame.iloc[0].to_dict()
    return TeamMatchDetailResponse(
        reference_date=SERVICE_REFERENCE_DATE,
        match=_build_match_meta(match_meta_row),
        summary=TeamMatchDetailSummary(**build_match_detail_summary(scored_players)),
        team_stats=TeamMatchDetailTeamStats(**build_match_detail_team_stats(match_meta_row)),
        leaders=build_match_detail_leaders(scored_players),
        players=serialize_match_players(scored_players),
    )


__all__ = ["get_team_match_detail"]
