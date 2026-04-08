from __future__ import annotations

import numpy as np
import pandas as pd


def prepare_objective_match_scores(match_frame: pd.DataFrame) -> pd.DataFrame:
    if match_frame.empty:
        return match_frame.copy()

    frame = match_frame.copy()
    frame["match_date"] = pd.to_datetime(frame["match_date"], errors="coerce")
    numeric_columns = [
        "minutes_played",
        "goals",
        "assists",
        "shots",
        "shots_on_target",
        "key_passes",
        "pass_accuracy",
        "mistakes",
        "yellow_cards",
        "red_cards",
        "aerial_duels_won",
        "aerial_duels_total",
        "ground_duels_won",
        "ground_duels_total",
        "total_distance",
        "max_speed",
        "sprint_count",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)

    total_duels = frame.get("aerial_duels_total", 0.0) + frame.get("ground_duels_total", 0.0)
    duels_won = frame.get("aerial_duels_won", 0.0) + frame.get("ground_duels_won", 0.0)
    frame["duel_win_rate"] = np.where(total_duels > 0, duels_won / total_duels, 0.5)
    frame["distance_per_min"] = np.where(frame["minutes_played"] > 0, frame["total_distance"] / frame["minutes_played"], 0.0)
    frame["sprints_per_90"] = np.where(frame["minutes_played"] > 0, frame["sprint_count"] / frame["minutes_played"] * 90.0, 0.0)
    frame["match_score"] = np.clip(
        np.clip(frame["minutes_played"] / 90.0, 0, 1.2) * 15.0
        + frame["goals"] * 14.0
        + frame["assists"] * 9.0
        + frame["shots_on_target"] * 2.2
        + frame["key_passes"] * 1.6
        + frame["pass_accuracy"] * 18.0
        + frame["duel_win_rate"] * 10.0
        + np.clip(frame["distance_per_min"] / 120.0, 0, 1.2) * 8.0
        + np.clip(frame["sprints_per_90"] / 30.0, 0, 1.2) * 8.0
        - frame.get("mistakes", 0.0) * 4.5
        - frame.get("yellow_cards", 0.0) * 1.2
        - frame.get("red_cards", 0.0) * 5.0,
        0,
        100,
    ).round(2)
    frame["match_score_band"] = np.select(
        [
            frame["match_score"] >= 75,
            frame["match_score"] >= 60,
            frame["match_score"] >= 45,
        ],
        ["elite", "strong", "steady"],
        default="watch",
    )
    frame = frame.sort_values(["player_id", "match_date", "match_player_id"], ascending=[True, False, False]).copy()
    frame["match_rank"] = frame.groupby("player_id").cumcount() + 1
    return frame
