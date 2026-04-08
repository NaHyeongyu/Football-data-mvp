from __future__ import annotations

from typing import Any

import pandas as pd

from ..service_reference import SERVICE_REFERENCE_DATE
from .shared import _age_today, _grade_from_age, _position_group, _season_year_for_date


def _build_season_summary_records(players: pd.DataFrame, match_frame: pd.DataFrame) -> list[dict[str, Any]]:
    if players.empty:
        return []

    season_match_counts = (
        match_frame[["season_year", "match_id"]]
        .drop_duplicates()
        .groupby("season_year")
        .size()
        .to_dict()
    )
    latest_season_year = max(season_match_counts) if season_match_counts else _season_year_for_date(SERVICE_REFERENCE_DATE)
    player_rows = players.set_index("player_id").to_dict("index")
    records: list[dict[str, Any]] = []

    for (player_id, season_year), group in match_frame.groupby(["player_id", "season_year"], sort=False):
        player_row = player_rows.get(player_id)
        if player_row is None:
            continue

        ordered = group.sort_values(["match_date", "match_player_id"], ascending=[False, False]).copy()
        season_match_count = int(season_match_counts.get(season_year, len(ordered)))
        appearances = int(len(ordered))
        starts = int(ordered["start_position"].notna().sum())
        minutes = int(ordered["minutes_played"].fillna(0).sum())
        goals = int(ordered["goals"].fillna(0).sum())
        assists = int(ordered["assists"].fillna(0).sum())
        goal_contrib = goals + assists
        shots_on_target = float(ordered["shots_on_target"].fillna(0).sum())
        key_passes = float(ordered["key_passes"].fillna(0).sum())
        pass_attempts = float(ordered["passes_attempted"].fillna(0).sum())
        pass_success = float(ordered["passes_completed"].fillna(0).sum())
        dribble_attempts = float(ordered["take_ons_attempted"].fillna(0).sum())
        dribble_success = float(ordered["take_ons_succeeded"].fillna(0).sum())
        tackles = float(ordered["tackles_succeeded"].fillna(0).sum())
        interceptions = float(ordered["interceptions"].fillna(0).sum())
        clearances = float(ordered["clearances"].fillna(0).sum())
        saves = float(ordered["saves"].fillna(0).sum())
        duels_won = float(ordered["aerial_duels_won"].fillna(0).sum() + ordered["ground_duels_won"].fillna(0).sum())
        duels_total = float(ordered["aerial_duels_total"].fillna(0).sum() + ordered["ground_duels_total"].fillna(0).sum())
        total_distance = float(ordered["total_distance"].fillna(0).sum())
        high_speed_m = float(ordered["distance_high_speed_m"].fillna(0).sum())
        sprint_count = float(ordered["sprint_count"].fillna(0).sum())
        player_load = float(ordered["player_load"].fillna(0).sum())
        # Recent form is intentionally short-horizon so the directory highlights current momentum,
        # while the rest of the row keeps full-season totals.
        recent_matches = ordered.head(5)
        age_today = _age_today(player_row.get("date_of_birth"))

        records.append(
            {
                "player_id": player_id,
                "player_name": str(player_row["name"]),
                "season_id": f"S{int(season_year)}",
                "season_year": int(season_year),
                "registered_position": player_row.get("primary_position"),
                "primary_role": player_row.get("primary_position"),
                "position_group": _position_group(player_row.get("primary_position")),
                "grade": _grade_from_age(age_today) or 1,
                "age_today": age_today or 0.0,
                "season_match_count": season_match_count,
                "appearances": appearances,
                "starts": starts,
                "minutes": minutes,
                "appearance_rate_pct": round((appearances / max(season_match_count, 1)) * 100, 1),
                "start_rate_pct": round((starts / max(appearances, 1)) * 100, 1),
                "minutes_share_pct": round((minutes / max(season_match_count * 90, 1)) * 100, 1),
                "goals": goals,
                "assists": assists,
                "goal_contrib": goal_contrib,
                "goal_contrib_p90": round((goal_contrib / max(minutes, 1)) * 90, 2),
                "saves_p90": round((saves / max(minutes, 1)) * 90, 2),
                "shots_on_target_p90": round((shots_on_target / max(minutes, 1)) * 90, 2),
                "key_passes_p90": round((key_passes / max(minutes, 1)) * 90, 2),
                "duels_won_p90": round((duels_won / max(minutes, 1)) * 90, 2),
                "pass_completion_pct": round((pass_success / max(pass_attempts, 1)) * 100, 1) if pass_attempts > 0 else 0.0,
                "dribble_efficiency_pct": round((dribble_success / max(dribble_attempts, 1)) * 100, 1) if dribble_attempts > 0 else 0.0,
                "duel_win_pct": round((duels_won / max(duels_total, 1)) * 100, 1) if duels_total > 0 else 0.0,
                "def_actions_p90": round(((tackles + interceptions + clearances + saves) / max(minutes, 1)) * 90, 2),
                "distance_total_p90": round((total_distance / max(minutes, 1)) * 90, 2),
                "high_speed_m_p90": round((high_speed_m / max(minutes, 1)) * 90, 2),
                "max_speed_kmh": round(float(ordered["max_speed"].fillna(0).max()), 1),
                "sprint_count_p90": round((sprint_count / max(minutes, 1)) * 90, 2),
                "player_load_p90": round((player_load / max(minutes, 1)) * 90, 2),
                "role_count": int(ordered["position_played"].fillna(player_row.get("primary_position")).nunique()),
                "role_alignment_pct": round((ordered["position_played"].fillna("") == (player_row.get("primary_position") or "")).mean() * 100, 1),
                "recent_form_score": round(float(recent_matches["match_score"].fillna(0).mean()), 1) if not recent_matches.empty else 0.0,
                "recent_minutes": int(recent_matches["minutes_played"].fillna(0).sum()),
                "recent_goal_contrib": int(recent_matches["goals"].fillna(0).sum() + recent_matches["assists"].fillna(0).sum()),
                "discipline_risk": round(float(ordered["yellow_cards"].fillna(0).sum() + ordered["red_cards"].fillna(0).sum() * 2), 1),
            }
        )

    latest_season_records = {
        record["player_id"]
        for record in records
        if record["season_year"] == latest_season_year
    }
    for player_row in players.to_dict("records"):
        player_id = str(player_row["player_id"])
        if player_id in latest_season_records:
            continue

        age_today = _age_today(player_row.get("date_of_birth"))
        records.append(
            {
                "player_id": player_id,
                "player_name": str(player_row["name"]),
                "season_id": f"S{latest_season_year}",
                "season_year": latest_season_year,
                "registered_position": player_row.get("primary_position"),
                "primary_role": player_row.get("primary_position"),
                "position_group": _position_group(player_row.get("primary_position")),
                "grade": _grade_from_age(age_today) or 1,
                "age_today": age_today or 0.0,
                "season_match_count": int(season_match_counts.get(latest_season_year, 0)),
                "appearances": 0,
                "starts": 0,
                "minutes": 0,
                "appearance_rate_pct": 0.0,
                "start_rate_pct": 0.0,
                "minutes_share_pct": 0.0,
                "goals": 0,
                "assists": 0,
                "goal_contrib": 0,
                "goal_contrib_p90": 0.0,
                "saves_p90": 0.0,
                "shots_on_target_p90": 0.0,
                "key_passes_p90": 0.0,
                "duels_won_p90": 0.0,
                "pass_completion_pct": 0.0,
                "dribble_efficiency_pct": 0.0,
                "duel_win_pct": 0.0,
                "def_actions_p90": 0.0,
                "distance_total_p90": 0.0,
                "high_speed_m_p90": 0.0,
                "max_speed_kmh": 0.0,
                "sprint_count_p90": 0.0,
                "player_load_p90": 0.0,
                "role_count": 1,
                "role_alignment_pct": 100.0,
                "recent_form_score": 0.0,
                "recent_minutes": 0,
                "recent_goal_contrib": 0,
                "discipline_risk": 0.0,
            }
        )

    return sorted(
        records,
        key=lambda item: (
            -int(item["season_year"]),
            item["registered_position"] or "",
            item["player_name"],
        ),
    )


__all__ = ["_build_season_summary_records"]
