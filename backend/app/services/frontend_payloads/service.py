from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException
import pandas as pd

from ..frame_loader import fetch_frame as _fetch_frame
from ..service_reference import SERVICE_REFERENCE_DATE
from .match_payloads import _build_match_gps_summary, _build_match_performance_records
from .medical import _build_medical_payloads
from .mental import _build_mental_notes
from .physical_payloads import _build_physical_sessions, _build_physical_test_records
from .queries import COUNSELING_QUERY, INJURY_HISTORY_QUERY, MATCH_LOG_QUERY, PHYSICAL_TESTS_QUERY, PLAYERS_QUERY, TEAM_NAME
from .season_summary import _build_season_summary_records
from .shared import (
    _age_today,
    _filter_supported_season_frame,
    _grade_from_age,
    _position_group,
    _prepare_match_frame,
    _prepare_physical_tests_frame,
    _safe_float,
    _season_year_for_date,
)


def _fetch_players() -> pd.DataFrame:
    return _fetch_frame(PLAYERS_QUERY)


def _fetch_match_frame() -> pd.DataFrame:
    raw_matches = _fetch_frame(MATCH_LOG_QUERY, (SERVICE_REFERENCE_DATE,))
    return _filter_supported_season_frame(_prepare_match_frame(raw_matches))


def _fetch_injury_history() -> pd.DataFrame:
    return _filter_supported_season_frame(
        _fetch_frame(INJURY_HISTORY_QUERY, (SERVICE_REFERENCE_DATE,)),
        date_column="injury_date",
    )


def _fetch_physical_tests() -> pd.DataFrame:
    return _prepare_physical_tests_frame(_fetch_frame(PHYSICAL_TESTS_QUERY, (SERVICE_REFERENCE_DATE,)))


def _fetch_counseling() -> pd.DataFrame:
    return _filter_supported_season_frame(
        _fetch_frame(COUNSELING_QUERY, (SERVICE_REFERENCE_DATE,)),
        date_column="counseling_date",
    )


def _latest_frontend_season_year(*season_sources: Iterable[Any]) -> int:
    candidates: list[int] = []
    for source in season_sources:
        for value in source:
            if value is None or pd.isna(value):
                continue
            candidates.append(int(value))
    return max(candidates, default=_season_year_for_date(SERVICE_REFERENCE_DATE))


def build_players_directory_payload() -> dict[str, Any]:
    players = _fetch_players()
    match_frame = _fetch_match_frame()
    injuries = _fetch_injury_history()

    season_summaries = _build_season_summary_records(players, match_frame)
    medical_reports, _ = _build_medical_payloads(players, injuries)
    latest_season_year = _latest_frontend_season_year(item["season_year"] for item in season_summaries)
    return {
        "latestSeasonYear": latest_season_year,
        "medicalAvailability": list(medical_reports.values()),
        "playerSeasonSummary": season_summaries,
    }


def build_player_detail_payload(player_id: str) -> dict[str, Any]:
    players = _fetch_players()
    player_rows = players.loc[players["player_id"] == player_id].copy()
    if player_rows.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    player_row = player_rows.iloc[0].to_dict()
    all_matches = _fetch_match_frame()
    player_matches = all_matches.loc[all_matches["player_id"] == player_id].copy()
    physical_tests = _fetch_physical_tests()
    player_physical_tests = physical_tests.loc[physical_tests["player_id"] == player_id].copy()
    injuries = _fetch_injury_history()
    counseling = _fetch_counseling()
    player_counseling = counseling.loc[counseling["player_id"] == player_id].copy() if not counseling.empty else counseling

    medical_reports, history_map = _build_medical_payloads(players, injuries)
    player_medical = medical_reports.get(player_id)
    all_season_summaries = _build_season_summary_records(players, all_matches)
    season_summaries = [item for item in all_season_summaries if item["player_id"] == player_id]
    latest_season_summary = max(season_summaries, key=lambda item: item["season_year"], default=None)
    physical_test_records = _build_physical_test_records(player_physical_tests)
    injury_history = history_map.get(player_id, [])
    mental_notes = [item for item in _build_mental_notes(player_counseling) if item["player_id"] == player_id]
    latest_season_year = _latest_frontend_season_year(
        (item["season_year"] for item in season_summaries),
        (item["season_year"] for item in physical_test_records),
        (item["season_year"] for item in injury_history),
        (
            _season_year_for_date(value)
            for value in player_counseling["counseling_date"].tolist()
        ),
    )
    age_today = _age_today(player_row.get("date_of_birth"))

    return {
        "generatedOn": SERVICE_REFERENCE_DATE.isoformat(),
        "profile": {
            "player_id": player_id,
            "name": player_row.get("name"),
            "birth_date": player_row.get("date_of_birth"),
            "grade": _grade_from_age(age_today),
            "registered_position": player_row.get("primary_position"),
            "primary_role": player_row.get("primary_position"),
            "position_group": _position_group(player_row.get("primary_position")),
            "age_today": age_today,
            "dominant_foot": player_row.get("foot"),
            "height_cm": _safe_float(player_row.get("height_cm"), 1),
            "weight_kg": _safe_float(player_row.get("weight_kg"), 1),
            "team_name": TEAM_NAME,
            "status": player_row.get("status"),
            "latest_season_id": f"S{latest_season_year}",
            "latest_season_year": latest_season_year,
            "latest_match_availability": player_medical.get("latest_match_availability") if player_medical else "가능",
            "latest_injury_name": player_medical.get("latest_injury_name") if player_medical else None,
            "latest_injury_grade": player_medical.get("latest_injury_grade") if player_medical else None,
            "latest_return_to_play_date": player_medical.get("latest_return_to_play_date") if player_medical else None,
            "growth_score": None,
            "growth_band": None,
        },
        "latestSeasonSummary": latest_season_summary,
        "seasonSummaries": season_summaries,
        "matchPerformance": _build_match_performance_records(player_matches),
        "physicalTests": physical_test_records,
        "injuryHistory": injury_history,
        "mentalNotes": mental_notes,
        "reports": {
            "agent": None,
            "scout": None,
            "coach": None,
            "management": None,
            "medical": player_medical,
            "growth": None,
            "physical": None,
        },
    }


def build_physical_overview_payload() -> dict[str, Any]:
    match_frame = _fetch_match_frame()
    physical_tests = _fetch_physical_tests()
    match_gps_summary = _build_match_gps_summary(match_frame)
    latest_season_year = _latest_frontend_season_year(
        (item["season_year"] for item in match_gps_summary),
        physical_tests["season_year"].tolist() if "season_year" in physical_tests.columns else [],
    )
    return {
        "latestSeasonYear": latest_season_year,
        "matchGpsSummary": match_gps_summary,
        "physicalSessions": _build_physical_sessions(physical_tests),
    }


__all__ = [
    "build_physical_overview_payload",
    "build_player_detail_payload",
    "build_players_directory_payload",
]
