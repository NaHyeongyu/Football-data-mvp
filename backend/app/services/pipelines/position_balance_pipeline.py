from __future__ import annotations

import math

import pandas as pd


def build_position_balance(
    scored_matches: pd.DataFrame,
    position_availability: pd.DataFrame,
    team_matches: pd.DataFrame,
) -> list[dict[str, object]]:
    if scored_matches.empty:
        if position_availability.empty:
            return []
        return [
            {
                "position": row["position"],
                "recent_form_score": None,
                "previous_form_score": None,
                "form_delta": None,
                "average_minutes": None,
                "average_sprint_count": None,
                "average_total_distance": None,
                "available_count": int(row["available_count"]),
                "managed_count": int(row["managed_count"]),
                "injured_count": int(row["injured_count"]),
                "insight_label": "availability risk" if int(row["injured_count"]) > 0 else "stable",
            }
            for row in position_availability.sort_values("position").to_dict("records")
        ]

    recent_match_ids = team_matches.head(5)["match_id"].tolist()
    previous_match_ids = team_matches.iloc[5:10]["match_id"].tolist()

    recent = scored_matches.loc[scored_matches["match_id"].isin(recent_match_ids)].copy()
    previous = scored_matches.loc[scored_matches["match_id"].isin(previous_match_ids)].copy()

    recent_summary = (
        recent.groupby("position", as_index=False)
        .agg(
            recent_form_score=("match_score", "mean"),
            average_minutes=("minutes_played", "mean"),
            average_sprint_count=("sprint_count", "mean"),
            average_total_distance=("total_distance", "mean"),
        )
        .round({"recent_form_score": 2, "average_minutes": 1, "average_sprint_count": 1, "average_total_distance": 2})
    )
    previous_summary = (
        previous.groupby("position", as_index=False)
        .agg(previous_form_score=("match_score", "mean"))
        .round({"previous_form_score": 2})
    )

    balance = recent_summary.merge(previous_summary, on="position", how="left").merge(
        position_availability,
        on="position",
        how="outer",
    )
    balance["form_delta"] = (balance["recent_form_score"] - balance["previous_form_score"]).round(2)

    sprint_threshold = balance["average_sprint_count"].dropna().quantile(0.75) if balance["average_sprint_count"].notna().any() else math.inf
    distance_threshold = balance["average_total_distance"].dropna().quantile(0.75) if balance["average_total_distance"].notna().any() else math.inf

    def label(row: pd.Series) -> str:
        roster_count = int(row.get("roster_count", 0) or 0)
        injured_count = int(row.get("injured_count", 0) or 0)
        if roster_count > 0 and injured_count >= max(1, math.ceil(roster_count * 0.25)):
            return "availability risk"
        if pd.notna(row.get("form_delta")) and float(row["form_delta"]) <= -4:
            return "form down"
        if (
            pd.notna(row.get("average_sprint_count"))
            and float(row["average_sprint_count"]) >= float(sprint_threshold)
        ) or (
            pd.notna(row.get("average_total_distance"))
            and float(row["average_total_distance"]) >= float(distance_threshold)
        ):
            return "high load"
        if pd.notna(row.get("form_delta")) and float(row["form_delta"]) >= 4:
            return "stable"
        return "stable"

    balance["insight_label"] = balance.apply(label, axis=1)
    balance = balance.sort_values("position")

    items: list[dict[str, object]] = []
    for row in balance.to_dict("records"):
        items.append(
            {
                "position": row["position"],
                "recent_form_score": None if pd.isna(row.get("recent_form_score")) else float(row["recent_form_score"]),
                "previous_form_score": None if pd.isna(row.get("previous_form_score")) else float(row["previous_form_score"]),
                "form_delta": None if pd.isna(row.get("form_delta")) else float(row["form_delta"]),
                "average_minutes": None if pd.isna(row.get("average_minutes")) else float(row["average_minutes"]),
                "average_sprint_count": None if pd.isna(row.get("average_sprint_count")) else float(row["average_sprint_count"]),
                "average_total_distance": None if pd.isna(row.get("average_total_distance")) else float(row["average_total_distance"]),
                "available_count": int(row.get("available_count", 0) or 0),
                "managed_count": int(row.get("managed_count", 0) or 0),
                "injured_count": int(row.get("injured_count", 0) or 0),
                "insight_label": row["insight_label"],
            }
        )
    return items
