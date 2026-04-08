from __future__ import annotations

from typing import Any

import pandas as pd

from ...schemas import (
    CurrentInjurySummary,
    MatchSummary,
    PhysicalProfileSummary,
    PlayerSummary,
)


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(round(float(value), 2))


def _map_player_row(row: dict[str, Any]) -> PlayerSummary:
    injury_id = row["injury_id"]
    current_injury = None
    if injury_id:
        current_injury = CurrentInjurySummary(
            injury_id=injury_id,
            injury_date=row["injury_date"],
            injury_type=row["injury_type"],
            injury_part=row["injury_part"],
            severity_level=row["severity_level"],
            injury_status=row["injury_status"],
            expected_return_date=row["expected_return_date"],
            actual_return_date=row["actual_return_date"],
            occurred_during=row["occurred_during"],
        )

    return PlayerSummary(
        player_id=row["player_id"],
        name=row["name"],
        jersey_number=row["jersey_number"],
        date_of_birth=row["date_of_birth"],
        age=row["age"],
        primary_position=row["primary_position"],
        secondary_position=row["secondary_position"],
        foot=row["foot"],
        nationality=row["nationality"],
        status=row["status"],
        profile_image_url=row["profile_image_url"],
        joined_at=row["joined_at"],
        previous_team=row["previous_team"],
        updated_at=row["updated_at"],
        physical_profile=PhysicalProfileSummary(
            height_cm=row["height_cm"],
            weight_kg=row["weight_kg"],
            body_fat_percentage=row["body_fat_percentage"],
            bmi=row["bmi"],
            muscle_mass_kg=row["muscle_mass_kg"],
            measured_at=row["physical_measured_at"],
        ),
        current_injury=current_injury,
        match_summary=MatchSummary(
            appearances=row["appearances"],
            total_minutes=row["total_minutes"],
            total_goals=row["total_goals"],
            total_assists=row["total_assists"],
            recent_form_score=row["recent_form_score"],
            previous_form_score=row.get("previous_form_score"),
            form_delta=row.get("form_delta"),
            form_trend=row.get("form_trend"),
            evaluated_match_count=row.get("evaluated_match_count", 0),
            latest_match_score=row.get("latest_match_score"),
            position_average_form_score=row.get("position_average_form_score"),
            team_average_form_score=row.get("team_average_form_score"),
            form_vs_position_average=row.get("form_vs_position_average"),
            form_vs_team_average=row.get("form_vs_team_average"),
            latest_match_date=row["latest_match_date"],
        ),
    )


def _build_match_item_payload(match_row: dict[str, Any]) -> dict[str, Any]:
    match_date = match_row["match_date"]
    return {
        "match_player_id": match_row["match_player_id"],
        "match_id": match_row["match_id"],
        "match_date": match_date.date() if pd.notna(match_date) else None,
        "match_type": match_row["match_type"],
        "opponent_team": match_row["opponent_team"],
        "stadium": match_row["stadium"],
        "minutes_played": int(match_row["minutes_played"]),
        "goals": int(match_row["goals"]),
        "assists": int(match_row["assists"]),
        "shots": int(match_row["shots"]),
        "pass_accuracy": _optional_float(match_row["pass_accuracy"]),
        "total_distance": _optional_float(match_row["total_distance"]),
        "max_speed": _optional_float(match_row["max_speed"]),
        "sprint_count": int(match_row["sprint_count"]) if pd.notna(match_row["sprint_count"]) else None,
        "match_score": _optional_float(match_row["match_score"]),
        "match_score_band": match_row["match_score_band"],
    }
