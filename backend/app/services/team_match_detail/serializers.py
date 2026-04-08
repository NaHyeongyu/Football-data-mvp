from __future__ import annotations

from typing import Any

import pandas as pd

from ...schemas import TeamMatchDetailMeta


def _result_label(goals_for: int, goals_against: int) -> str:
    if goals_for > goals_against:
        return "승"
    if goals_for < goals_against:
        return "패"
    return "무"


def _build_match_meta(match_meta_row: dict[str, Any]) -> TeamMatchDetailMeta:
    goals_for = int(match_meta_row["goals_for"])
    goals_against = int(match_meta_row["goals_against"])
    return TeamMatchDetailMeta(
        match_id=str(match_meta_row["match_id"]),
        match_date=pd.Timestamp(match_meta_row["match_date"]).date(),
        match_type=str(match_meta_row["match_type"]),
        opponent_team=str(match_meta_row["opponent_team"]),
        stadium_name=str(match_meta_row["stadium_name"]),
        goals_for=goals_for,
        goals_against=goals_against,
        result=_result_label(goals_for, goals_against),
        possession_for=(
            None
            if pd.isna(match_meta_row["possession_for"])
            else float(round(float(match_meta_row["possession_for"]), 1))
        ),
        possession_against=(
            None
            if pd.isna(match_meta_row["possession_against"])
            else float(round(float(match_meta_row["possession_against"]), 1))
        ),
    )


__all__ = ["_build_match_meta"]
