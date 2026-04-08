from __future__ import annotations

import pandas as pd

from ...schemas import TeamMatchListItem, TeamMatchesSummary, TeamMatchYearOption
from ..pipelines.match_score_pipeline import prepare_objective_match_scores
from ..service_reference import SERVICE_REFERENCE_DATE


def _resolve_selected_year(available_years: list[int], year: int | None) -> int:
    if year is not None:
        return year
    if SERVICE_REFERENCE_DATE.year in available_years:
        return SERVICE_REFERENCE_DATE.year
    if available_years:
        return available_years[-1]
    return SERVICE_REFERENCE_DATE.year


def _result_label(goals_for: int, goals_against: int) -> str:
    if goals_for > goals_against:
        return "승"
    if goals_for < goals_against:
        return "패"
    return "무"


def _prepare_matches_frame(matches: pd.DataFrame) -> pd.DataFrame:
    if matches.empty:
        return matches.copy()

    prepared = matches.copy()
    prepared["match_date"] = pd.to_datetime(prepared["match_date"], errors="coerce")
    prepared = prepared[prepared["match_date"].notna()].copy()
    prepared = prepare_objective_match_scores(prepared)

    grouped = (
        prepared.groupby(
            [
                "match_id",
                "match_date",
                "match_type",
                "opponent_team",
                "stadium_name",
                "goals_for",
                "goals_against",
                "possession_for",
                "possession_against",
            ],
            as_index=False,
        )
        # Match-level board metrics are built from player rows, so aggregate after
        # objective scoring rather than trying to score match rows separately.
        .agg(
            team_average_match_score=("match_score", "mean"),
            average_minutes=("minutes_played", "mean"),
            player_count=("player_id", "nunique"),
        )
        .sort_values(["match_date", "match_id"], ascending=[False, False])
    )
    grouped["team_average_match_score"] = grouped["team_average_match_score"].round(2)
    grouped["average_minutes"] = grouped["average_minutes"].round(1)
    grouped["year"] = grouped["match_date"].dt.year.astype(int)
    return grouped


def _build_matches_summary(selected: pd.DataFrame) -> TeamMatchesSummary:
    return TeamMatchesSummary(
        match_count=int(len(selected)),
        official_match_count=int((selected["match_type"] == "공식").sum()),
        practice_match_count=int((selected["match_type"] == "연습").sum()),
        win_count=int((selected["goals_for"] > selected["goals_against"]).sum()),
        draw_count=int((selected["goals_for"] == selected["goals_against"]).sum()),
        loss_count=int((selected["goals_for"] < selected["goals_against"]).sum()),
        average_match_score=(None if selected.empty else float(round(selected["team_average_match_score"].mean(), 2))),
    )


def _build_year_options(available_years: list[int]) -> list[TeamMatchYearOption]:
    return [TeamMatchYearOption(year=item, label=f"{item} Season") for item in available_years]


def _serialize_match_items(selected: pd.DataFrame) -> list[TeamMatchListItem]:
    return [
        TeamMatchListItem(
            match_id=str(row.match_id),
            match_date=pd.Timestamp(row.match_date).date(),
            match_type=str(row.match_type),
            opponent_team=str(row.opponent_team),
            stadium_name=str(row.stadium_name),
            goals_for=int(row.goals_for),
            goals_against=int(row.goals_against),
            result=_result_label(int(row.goals_for), int(row.goals_against)),
            possession_for=None if pd.isna(row.possession_for) else float(round(row.possession_for, 1)),
            possession_against=None if pd.isna(row.possession_against) else float(round(row.possession_against, 1)),
            team_average_match_score=float(row.team_average_match_score),
            average_minutes=float(row.average_minutes),
            player_count=int(row.player_count),
        )
        for row in selected.itertuples(index=False)
    ]


__all__ = [
    "_build_matches_summary",
    "_build_year_options",
    "_prepare_matches_frame",
    "_resolve_selected_year",
    "_serialize_match_items",
]
