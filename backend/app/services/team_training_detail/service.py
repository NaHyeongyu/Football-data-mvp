from __future__ import annotations

import pandas as pd
from fastapi import HTTPException

from ...schemas import (
    TeamTrainingDetailMeta,
    TeamTrainingDetailResponse,
    TeamTrainingDetailSummary,
)
from ..frame_loader import fetch_frame as _fetch_frame
from ..service_reference import SERVICE_REFERENCE_DATE
from .queries import TRAINING_META_QUERY, TRAINING_PLAYERS_QUERY
from .serializers import (
    _build_training_leaders,
    _build_training_summary,
    _nullable_datetime,
    _nullable_text,
    _prepare_training_players,
    _sanitize_training_note,
    _serialize_training_players,
)


def get_team_training_detail(training_id: str) -> TeamTrainingDetailResponse:
    training_meta_frame = _fetch_frame(TRAINING_META_QUERY, (training_id, SERVICE_REFERENCE_DATE))
    if training_meta_frame.empty:
        raise HTTPException(status_code=404, detail="Training not found")

    player_frame = _fetch_frame(TRAINING_PLAYERS_QUERY, (training_id, SERVICE_REFERENCE_DATE))
    players = _prepare_training_players(player_frame)

    training_meta_row = training_meta_frame.iloc[0].to_dict()
    training_meta = TeamTrainingDetailMeta(
        training_id=str(training_meta_row["training_id"]),
        training_date=pd.Timestamp(training_meta_row["training_date"]).date(),
        session_name=str(training_meta_row["session_name"]),
        training_type=str(training_meta_row["training_type"]),
        training_focus=_nullable_text(training_meta_row.get("training_focus")),
        training_detail=_nullable_text(training_meta_row.get("training_detail")),
        notes=_sanitize_training_note(training_meta_row.get("notes")),
        start_at=_nullable_datetime(training_meta_row.get("start_at")),
        end_at=_nullable_datetime(training_meta_row.get("end_at")),
        intensity_level=_nullable_text(training_meta_row.get("intensity_level")),
        coach_name=_nullable_text(training_meta_row.get("coach_name")),
        location=_nullable_text(training_meta_row.get("location")),
    )

    summary = TeamTrainingDetailSummary(**_build_training_summary(training_meta_row, players))
    leaders = _build_training_leaders(players)

    return TeamTrainingDetailResponse(
        reference_date=SERVICE_REFERENCE_DATE,
        training=training_meta,
        summary=summary,
        leaders=leaders,
        players=_serialize_training_players(players),
    )


__all__ = ["get_team_training_detail"]
