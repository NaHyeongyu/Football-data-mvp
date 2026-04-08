from __future__ import annotations

from typing import Any

import pandas as pd


def extract_latest_season_highlights(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "latest_season_year": None,
            "season_best_match": None,
            "season_worst_match": None,
        }

    matches = frame.copy()
    matches["match_date"] = pd.to_datetime(matches["match_date"], errors="coerce")
    matches = matches[matches["match_date"].notna()].copy()
    if matches.empty:
        return {
            "latest_season_year": None,
            "season_best_match": None,
            "season_worst_match": None,
        }

    latest_season_year = int(matches["match_date"].dt.year.max())
    season_matches = matches.loc[matches["match_date"].dt.year == latest_season_year].copy()
    if season_matches.empty:
        return {
            "latest_season_year": latest_season_year,
            "season_best_match": None,
            "season_worst_match": None,
        }

    season_best_match = season_matches.sort_values(
        ["match_score", "match_date", "match_player_id"],
        ascending=[False, False, False],
    ).iloc[0].to_dict()
    season_worst_match = season_matches.sort_values(
        ["match_score", "match_date", "match_player_id"],
        ascending=[True, False, False],
    ).iloc[0].to_dict()

    return {
        "latest_season_year": latest_season_year,
        "season_best_match": season_best_match,
        "season_worst_match": season_worst_match,
    }
