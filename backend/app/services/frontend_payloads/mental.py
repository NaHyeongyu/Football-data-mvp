from __future__ import annotations

from typing import Any

import pandas as pd

from .shared import _season_id_for_date, _season_year_for_date


def _build_mental_notes(counseling: pd.DataFrame) -> list[dict[str, Any]]:
    if counseling.empty:
        return []

    prepared = counseling.copy()
    prepared["season_year"] = prepared["counseling_date"].apply(_season_year_for_date)
    prepared["season_id"] = prepared["counseling_date"].apply(_season_id_for_date)
    notes: list[dict[str, Any]] = []
    for player_id, group in prepared.groupby("player_id", sort=False):
        ordered = group.sort_values(["counseling_date", "counseling_id"], ascending=[True, True]).copy()
        ordered["session_round"] = range(1, len(ordered) + 1)
        for row in ordered.sort_values(["counseling_date", "counseling_id"], ascending=[False, False]).itertuples(index=False):
            notes.append(
                {
                    "mental_id": str(row.counseling_id),
                    "season_id": str(row.season_id),
                    "season_year": int(row.season_year),
                    "player_id": str(player_id),
                    "session_round": int(row.session_round),
                    "session_date": row.counseling_date,
                    "counseling_type": row.topic,
                    "player_quote": row.summary,
                }
            )
    return notes


__all__ = ["_build_mental_notes"]
