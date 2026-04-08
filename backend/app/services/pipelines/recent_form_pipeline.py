from __future__ import annotations

import numpy as np
import pandas as pd


def summarize_recent_form(frame: pd.DataFrame, recent_window: int = 5, previous_window: int = 5) -> pd.DataFrame:
    base_columns = [
        "player_id",
        "recent_form_score",
        "previous_form_score",
        "form_delta",
        "form_trend",
        "evaluated_match_count",
        "latest_match_score",
    ]
    if frame.empty:
        return pd.DataFrame(columns=base_columns)

    recent = frame.loc[frame["match_rank"] <= recent_window]
    previous = frame.loc[(frame["match_rank"] > recent_window) & (frame["match_rank"] <= recent_window + previous_window)]

    recent_summary = recent.groupby("player_id").agg(
        recent_form_score=("match_score", "mean"),
        evaluated_match_count=("match_score", "size"),
        latest_match_score=("match_score", "first"),
    )
    previous_summary = previous.groupby("player_id").agg(previous_form_score=("match_score", "mean"))

    summary = recent_summary.merge(previous_summary, on="player_id", how="left").reset_index()
    summary["recent_form_score"] = summary["recent_form_score"].round(2)
    summary["previous_form_score"] = summary["previous_form_score"].round(2)
    summary["form_delta"] = (summary["recent_form_score"] - summary["previous_form_score"]).round(2)
    summary["form_trend"] = np.select(
        [summary["form_delta"] >= 5, summary["form_delta"] <= -5],
        ["up", "down"],
        default="flat",
    )
    return summary


def attach_form_benchmarks(summary: pd.DataFrame, roster: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary.copy()

    merged = summary.merge(roster[["player_id", "primary_position"]], on="player_id", how="left")
    team_average = round(float(merged["recent_form_score"].dropna().mean()), 2) if merged["recent_form_score"].notna().any() else np.nan
    merged["team_average_form_score"] = team_average
    merged["position_average_form_score"] = (
        merged.groupby("primary_position")["recent_form_score"].transform("mean").round(2)
    )
    merged["form_vs_position_average"] = (
        merged["recent_form_score"] - merged["position_average_form_score"]
    ).round(2)
    merged["form_vs_team_average"] = (
        merged["recent_form_score"] - merged["team_average_form_score"]
    ).round(2)
    return merged.drop(columns=["primary_position"])
