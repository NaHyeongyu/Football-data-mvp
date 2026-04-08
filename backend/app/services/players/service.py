from __future__ import annotations

from fastapi import HTTPException
import pandas as pd
from psycopg import sql

from ...db import get_connection
from ...schemas import MatchHighlightItem, PlayerDetailResponse, PlayerListResponse, RecentMatchItem
from .form_summary import _apply_form_summary, _build_form_summary_map
from .mappers import _build_match_item_payload, _map_player_row
from .queries import PLAYER_BASE_CTES, PLAYER_SELECT, RECENT_MATCHES_SQL, _build_player_filters
from ..pipelines.match_score_pipeline import prepare_objective_match_scores
from ..pipelines.season_highlights_pipeline import extract_latest_season_highlights


def list_players(
    q: str | None = None,
    position: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PlayerListResponse:
    where_sql, params = _build_player_filters(q=q, position=position, status=status)

    count_query = sql.SQL(
        PLAYER_BASE_CTES
        + " SELECT COUNT(*) AS total FROM football.players AS p"
    ) + where_sql

    data_query = (
        sql.SQL(PLAYER_BASE_CTES + PLAYER_SELECT)
        + where_sql
        + sql.SQL(" ORDER BY p.primary_position::text, p.jersey_number, p.name LIMIT %s OFFSET %s")
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(count_query, params)
            total = int(cursor.fetchone()["total"])

            cursor.execute(data_query, [*params, limit, offset])
            rows = cursor.fetchall()

    form_summary_map = _build_form_summary_map(matches_per_player=10)
    items = [_map_player_row(_apply_form_summary(row, form_summary_map.get(row["player_id"]))) for row in rows]
    return PlayerListResponse(total=total, items=items)


def get_player_detail(player_id: str, recent_match_limit: int = 5) -> PlayerDetailResponse:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(PLAYER_BASE_CTES + PLAYER_SELECT + " WHERE p.player_id = %s"),
                [player_id],
            )
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Player not found")

            cursor.execute(RECENT_MATCHES_SQL, [player_id, max(recent_match_limit, 400)])
            recent_matches_rows = cursor.fetchall()

    form_summary_map = _build_form_summary_map(matches_per_player=10)
    recent_matches_frame = pd.DataFrame(recent_matches_rows) if recent_matches_rows else pd.DataFrame()
    if not recent_matches_frame.empty:
        recent_matches_frame = prepare_objective_match_scores(recent_matches_frame)
        season_highlights = extract_latest_season_highlights(recent_matches_frame)
        recent_matches_records = [
            _build_match_item_payload(recent_row)
            for recent_row in recent_matches_frame.head(recent_match_limit).to_dict("records")
        ]
    else:
        recent_matches_records = []
        season_highlights = {
            "latest_season_year": None,
            "season_best_match": None,
            "season_worst_match": None,
        }

    summary = _map_player_row(_apply_form_summary(row, form_summary_map.get(player_id)))
    recent_matches = [RecentMatchItem(**recent_row) for recent_row in recent_matches_records]
    season_best_match = (
        MatchHighlightItem(**_build_match_item_payload(season_highlights["season_best_match"]))
        if season_highlights["season_best_match"] is not None
        else None
    )
    season_worst_match = (
        MatchHighlightItem(**_build_match_item_payload(season_highlights["season_worst_match"]))
        if season_highlights["season_worst_match"] is not None
        else None
    )
    return PlayerDetailResponse(
        **summary.model_dump(),
        latest_season_year=season_highlights["latest_season_year"],
        season_best_match=season_best_match,
        season_worst_match=season_worst_match,
        recent_matches=recent_matches,
    )
