from __future__ import annotations

from typing import Any

import pandas as pd


def build_team_availability_board(
    players: pd.DataFrame,
    injuries: pd.DataFrame,
    player_load_status: pd.DataFrame,
    snapshot_ts: pd.Timestamp,
) -> tuple[dict[str, Any], pd.DataFrame]:
    roster = players.copy()
    roster["injured_flag"] = roster["status"].eq("injured")
    roster["managed_flag"] = False
    roster["available_flag"] = False
    roster["open_rehab_flag"] = False
    roster["scheduled_return_flag"] = False
    roster["days_since_return"] = pd.NA

    latest_injury = pd.DataFrame(columns=["player_id"])
    if not injuries.empty:
        history = injuries.copy()
        for column in ["injury_date", "expected_return_date", "actual_return_date"]:
            history[column] = pd.to_datetime(history[column], errors="coerce")
        history = history[history["injury_date"].notna() & (history["injury_date"] <= snapshot_ts)].copy()
        if not history.empty:
            latest_injury = history.sort_values(["player_id", "injury_date"]).groupby("player_id").tail(1).copy()
            latest_injury["open_rehab_flag"] = latest_injury["injury_status"].eq("rehab") & (
                latest_injury["actual_return_date"].isna()
                | (latest_injury["actual_return_date"] > snapshot_ts)
            )
            latest_injury["scheduled_return_flag"] = latest_injury["open_rehab_flag"] & (
                latest_injury["expected_return_date"].notna()
                & (latest_injury["expected_return_date"] >= snapshot_ts)
            )
            latest_injury["days_since_return"] = (
                snapshot_ts - latest_injury["actual_return_date"]
            ).dt.days
            roster = roster.merge(
                latest_injury[
                    [
                        "player_id",
                        "open_rehab_flag",
                        "scheduled_return_flag",
                        "days_since_return",
                    ]
                ],
                on="player_id",
                how="left",
                suffixes=("", "_latest"),
            )
            for column in ["open_rehab_flag", "scheduled_return_flag", "days_since_return"]:
                replacement = f"{column}_latest"
                if replacement in roster.columns:
                    roster[column] = roster[replacement].where(roster[replacement].notna(), roster[column])
                    roster = roster.drop(columns=[replacement])
            roster["open_rehab_flag"] = roster["open_rehab_flag"].eq(True)
            roster["scheduled_return_flag"] = roster["scheduled_return_flag"].eq(True)
            roster["injured_flag"] = roster["injured_flag"] | roster["open_rehab_flag"]

    roster = roster.merge(
        player_load_status[["player_id", "spike_flag", "drop_flag"]],
        on="player_id",
        how="left",
    )
    roster["spike_flag"] = roster["spike_flag"].eq(True)
    roster["drop_flag"] = roster["drop_flag"].eq(True)

    roster["managed_flag"] = (
        ~roster["injured_flag"]
        & (
            roster["spike_flag"]
            | roster["drop_flag"]
            | (pd.to_numeric(roster["days_since_return"], errors="coerce").fillna(9999) <= 14)
        )
    )
    roster["available_flag"] = ~roster["injured_flag"] & ~roster["managed_flag"]

    positions = (
        roster.groupby("primary_position", as_index=False)
        .agg(
            roster_count=("player_id", "size"),
            available_count=("available_flag", "sum"),
            managed_count=("managed_flag", "sum"),
            injured_count=("injured_flag", "sum"),
        )
        .rename(columns={"primary_position": "position"})
        .sort_values("position")
    )
    positions["available_count"] = positions["available_count"].astype(int)
    positions["managed_count"] = positions["managed_count"].astype(int)
    positions["injured_count"] = positions["injured_count"].astype(int)
    positions["roster_count"] = positions["roster_count"].astype(int)

    board = {
        "available_count": int(roster["available_flag"].sum()),
        "managed_count": int(roster["managed_flag"].sum()),
        "injured_count": int(roster["injured_flag"].sum()),
        "scheduled_return_count": int(roster["scheduled_return_flag"].sum()),
        "positions": positions.to_dict("records"),
    }
    return board, positions
