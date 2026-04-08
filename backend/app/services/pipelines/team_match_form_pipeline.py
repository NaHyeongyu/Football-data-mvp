from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def build_team_match_form(scored_matches: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    if scored_matches.empty:
        return (
            {
                "recent_5_match_score": 0.0,
                "previous_5_match_score": None,
                "form_delta": None,
                "latest_match_score": None,
                "recent_matches": [],
                "best_match": None,
                "worst_match": None,
            },
            pd.DataFrame(),
        )

    grouped = (
        scored_matches.groupby(
            [
                "match_id",
                "match_date",
                "match_type",
                "opponent_team",
                "goals_for",
                "goals_against",
            ],
            as_index=False,
        )
        .agg(
            team_average_match_score=("match_score", "mean"),
            average_minutes=("minutes_played", "mean"),
            total_minutes=("minutes_played", "sum"),
            total_distance=("total_distance", "sum"),
            total_sprint_count=("sprint_count", "sum"),
            player_count=("player_id", "nunique"),
        )
        .sort_values(["match_date", "match_id"], ascending=[False, False])
    )
    grouped["team_average_match_score"] = grouped["team_average_match_score"].round(2)
    grouped["average_minutes"] = grouped["average_minutes"].round(1)
    grouped["efficiency_score"] = np.where(
        grouped["average_minutes"] > 0,
        (grouped["team_average_match_score"] / grouped["average_minutes"] * 90.0).round(2),
        np.nan,
    )
    grouped["match_rank"] = range(1, len(grouped) + 1)

    recent = grouped.loc[grouped["match_rank"] <= 5]
    previous = grouped.loc[(grouped["match_rank"] >= 6) & (grouped["match_rank"] <= 10)]
    recent_score = float(round(recent["team_average_match_score"].mean(), 2)) if not recent.empty else 0.0
    previous_score = float(round(previous["team_average_match_score"].mean(), 2)) if not previous.empty else None
    form_delta = float(round(recent_score - previous_score, 2)) if previous_score is not None else None

    latest_season_year = int(grouped["match_date"].dt.year.max())
    latest_season_matches = grouped.loc[grouped["match_date"].dt.year == latest_season_year].copy()
    best_match = (
        latest_season_matches.sort_values(["team_average_match_score", "match_date"], ascending=[False, False]).iloc[0].to_dict()
        if not latest_season_matches.empty
        else None
    )
    worst_match = (
        latest_season_matches.sort_values(["team_average_match_score", "match_date"], ascending=[True, False]).iloc[0].to_dict()
        if not latest_season_matches.empty
        else None
    )

    recent_matches = [
        {
            "match_id": row["match_id"],
            "match_date": row["match_date"].date(),
            "match_type": row["match_type"],
            "opponent_team": row["opponent_team"],
            "goals_for": int(row["goals_for"]),
            "goals_against": int(row["goals_against"]),
            "team_average_match_score": float(row["team_average_match_score"]),
            "average_minutes": float(row["average_minutes"]),
            "efficiency_score": None if pd.isna(row["efficiency_score"]) else float(row["efficiency_score"]),
        }
        for row in grouped.head(10).to_dict("records")
    ]

    board = {
        "recent_5_match_score": recent_score,
        "previous_5_match_score": previous_score,
        "form_delta": form_delta,
        "latest_match_score": float(grouped.iloc[0]["team_average_match_score"]) if not grouped.empty else None,
        "recent_matches": recent_matches,
        "best_match": _serialize_match(best_match),
        "worst_match": _serialize_match(worst_match),
    }
    return board, grouped


def _serialize_match(match_row: dict[str, Any] | None) -> dict[str, Any] | None:
    if match_row is None:
        return None
    return {
        "match_id": match_row["match_id"],
        "match_date": match_row["match_date"].date(),
        "match_type": match_row["match_type"],
        "opponent_team": match_row["opponent_team"],
        "goals_for": int(match_row["goals_for"]),
        "goals_against": int(match_row["goals_against"]),
        "team_average_match_score": float(round(match_row["team_average_match_score"], 2)),
        "average_minutes": float(round(match_row["average_minutes"], 1)),
        "efficiency_score": None
        if pd.isna(match_row["efficiency_score"])
        else float(round(match_row["efficiency_score"], 2)),
    }
