from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def build_team_development_trend(
    players: pd.DataFrame,
    physical_profiles: pd.DataFrame,
    form_summary: pd.DataFrame,
    snapshot_ts: pd.Timestamp,
) -> dict[str, Any]:
    if physical_profiles.empty:
        return {
            "average_body_fat_delta": None,
            "average_muscle_mass_delta": None,
            "season_start_body_fat_delta": None,
            "season_start_muscle_mass_delta": None,
            "rising_players_count": int((form_summary.get("form_trend") == "up").sum()) if not form_summary.empty else 0,
            "falling_players_count": int((form_summary.get("form_trend") == "down").sum()) if not form_summary.empty else 0,
            "positions": [],
        }

    profiles = physical_profiles.copy()
    profiles["created_at"] = pd.to_datetime(profiles["created_at"], errors="coerce")
    profiles = profiles[profiles["created_at"].notna() & (profiles["created_at"] <= snapshot_ts)].copy()
    if profiles.empty:
        return {
            "average_body_fat_delta": None,
            "average_muscle_mass_delta": None,
            "season_start_body_fat_delta": None,
            "season_start_muscle_mass_delta": None,
            "rising_players_count": int((form_summary.get("form_trend") == "up").sum()) if not form_summary.empty else 0,
            "falling_players_count": int((form_summary.get("form_trend") == "down").sum()) if not form_summary.empty else 0,
            "positions": [],
        }

    latest_season_year = int(profiles["created_at"].dt.year.max())
    lookback_cutoff = snapshot_ts - pd.Timedelta(days=365)
    rows: list[dict[str, Any]] = []

    for player_id, group in profiles.groupby("player_id"):
        ordered = group.sort_values("created_at").reset_index(drop=True)
        latest = ordered.iloc[-1]
        history = ordered.iloc[:-1]
        if history.empty:
            rows.append({"player_id": player_id})
            continue

        recent_candidates = history.loc[history["created_at"] >= lookback_cutoff]
        recent_baseline = recent_candidates.iloc[0] if not recent_candidates.empty else history.iloc[0]

        season_candidates = ordered.loc[ordered["created_at"].dt.year == latest_season_year]
        season_start = season_candidates.iloc[0] if not season_candidates.empty else ordered.iloc[0]

        rows.append(
            {
                "player_id": player_id,
                "body_fat_delta": round(float(latest["body_fat_percentage"] - recent_baseline["body_fat_percentage"]), 2),
                "muscle_mass_delta": round(float(latest["muscle_mass_kg"] - recent_baseline["muscle_mass_kg"]), 2),
                "season_body_fat_delta": round(float(latest["body_fat_percentage"] - season_start["body_fat_percentage"]), 2),
                "season_muscle_mass_delta": round(float(latest["muscle_mass_kg"] - season_start["muscle_mass_kg"]), 2),
            }
        )

    development = players[["player_id", "primary_position"]].merge(pd.DataFrame(rows), on="player_id", how="left")
    if not form_summary.empty:
        development = development.merge(form_summary[["player_id", "form_delta", "form_trend"]], on="player_id", how="left")
    else:
        development["form_delta"] = np.nan
        development["form_trend"] = None

    position_growth = (
        development.groupby("primary_position", as_index=False)
        .agg(
            roster_count=("player_id", "size"),
            average_body_fat_delta=("body_fat_delta", "mean"),
            average_muscle_mass_delta=("muscle_mass_delta", "mean"),
            average_form_delta=("form_delta", "mean"),
        )
        .rename(columns={"primary_position": "position"})
        .round(
            {
                "average_body_fat_delta": 2,
                "average_muscle_mass_delta": 2,
                "average_form_delta": 2,
            }
        )
    )

    def label(row: pd.Series) -> str:
        form_delta = row.get("average_form_delta")
        body_fat_delta = row.get("average_body_fat_delta")
        muscle_delta = row.get("average_muscle_mass_delta")
        if pd.notna(form_delta) and float(form_delta) >= 4:
            return "rising"
        if pd.notna(form_delta) and float(form_delta) <= -4:
            return "monitor"
        if pd.notna(muscle_delta) and float(muscle_delta) >= 0.5 and (pd.isna(body_fat_delta) or float(body_fat_delta) <= 0.0):
            return "rising"
        if (pd.notna(body_fat_delta) and float(body_fat_delta) >= 0.5) or (pd.notna(muscle_delta) and float(muscle_delta) <= -0.5):
            return "monitor"
        return "stable"

    position_growth["growth_label"] = position_growth.apply(label, axis=1)

    return {
        "average_body_fat_delta": None
        if not development["body_fat_delta"].notna().any()
        else float(round(development["body_fat_delta"].dropna().mean(), 2)),
        "average_muscle_mass_delta": None
        if not development["muscle_mass_delta"].notna().any()
        else float(round(development["muscle_mass_delta"].dropna().mean(), 2)),
        "season_start_body_fat_delta": None
        if not development["season_body_fat_delta"].notna().any()
        else float(round(development["season_body_fat_delta"].dropna().mean(), 2)),
        "season_start_muscle_mass_delta": None
        if not development["season_muscle_mass_delta"].notna().any()
        else float(round(development["season_muscle_mass_delta"].dropna().mean(), 2)),
        "rising_players_count": int((development["form_trend"] == "up").sum()),
        "falling_players_count": int((development["form_trend"] == "down").sum()),
        "positions": [
            {
                "position": row["position"],
                "roster_count": int(row["roster_count"]),
                "average_body_fat_delta": None
                if pd.isna(row["average_body_fat_delta"])
                else float(row["average_body_fat_delta"]),
                "average_muscle_mass_delta": None
                if pd.isna(row["average_muscle_mass_delta"])
                else float(row["average_muscle_mass_delta"]),
                "average_form_delta": None
                if pd.isna(row["average_form_delta"])
                else float(row["average_form_delta"]),
                "growth_label": row["growth_label"],
            }
            for row in position_growth.sort_values("position").to_dict("records")
        ],
    }
