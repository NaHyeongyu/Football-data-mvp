from __future__ import annotations

from typing import Any

import pandas as pd


def build_team_medical_overview(injuries: pd.DataFrame, snapshot_ts: pd.Timestamp) -> dict[str, Any]:
    if injuries.empty:
        return {
            "injuries_last_180d": 0,
            "reinjury_count_365d": 0,
            "returns_last_14d_count": 0,
            "current_rehab_count": 0,
            "injury_parts": [],
        }

    history = injuries.copy()
    for column in ["injury_date", "expected_return_date", "actual_return_date"]:
        history[column] = pd.to_datetime(history[column], errors="coerce")
    history = history[history["injury_date"].notna() & (history["injury_date"] <= snapshot_ts)].copy()
    if history.empty:
        return {
            "injuries_last_180d": 0,
            "reinjury_count_365d": 0,
            "returns_last_14d_count": 0,
            "current_rehab_count": 0,
            "injury_parts": [],
        }

    history["days_since_injury"] = (snapshot_ts - history["injury_date"]).dt.days
    history["days_since_return"] = (snapshot_ts - history["actual_return_date"]).dt.days
    recent_180 = history.loc[history["days_since_injury"] <= 180].copy()
    recent_365 = history.loc[history["days_since_injury"] <= 365].copy()

    repeated_parts = (
        recent_365.groupby(["player_id", "injury_part"])
        .size()
        .reset_index(name="repeat_count")
    )
    reinjury_count = int(repeated_parts.loc[repeated_parts["repeat_count"] >= 2, "repeat_count"].sub(1).sum())

    latest_injury = history.sort_values(["player_id", "injury_date"]).groupby("player_id").tail(1).copy()
    latest_injury["open_rehab_flag"] = latest_injury["injury_status"].eq("rehab") & (
        latest_injury["actual_return_date"].isna()
        | (latest_injury["actual_return_date"] > snapshot_ts)
    )

    injury_parts = (
        recent_180.groupby("injury_part", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values(["count", "injury_part"], ascending=[False, True])
    )

    return {
        "injuries_last_180d": int(len(recent_180)),
        "reinjury_count_365d": reinjury_count,
        "returns_last_14d_count": int(
            history["days_since_return"].between(0, 14, inclusive="both").fillna(False).sum()
        ),
        "current_rehab_count": int(latest_injury["open_rehab_flag"].sum()),
        "injury_parts": [
            {"injury_part": row["injury_part"], "count": int(row["count"])}
            for row in injury_parts.to_dict("records")
        ],
    }
