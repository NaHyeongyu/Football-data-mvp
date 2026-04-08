from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from .shared import _safe_float


def _build_physical_test_records(physical_tests: pd.DataFrame) -> list[dict[str, Any]]:
    if physical_tests.empty:
        return []

    round_map: dict[tuple[int, date], int] = {}
    grouped_dates = (
        physical_tests[["season_year", "test_date"]]
        .drop_duplicates()
        .sort_values(["season_year", "test_date"], ascending=[True, True])
    )
    for season_year, season_group in grouped_dates.groupby("season_year", sort=True):
        for index, row in enumerate(season_group.itertuples(index=False), start=1):
            round_map[(int(season_year), row.test_date.date())] = index

    records: list[dict[str, Any]] = []
    for row in physical_tests.itertuples(index=False):
        season_year = int(row.season_year)
        round_number = round_map.get((season_year, row.test_date.date()), 1)
        records.append(
            {
                "physical_id": str(row.physical_test_id),
                "season_id": str(row.season_id),
                "season_year": season_year,
                "player_id": str(row.player_id),
                "player_name": str(row.player_name),
                "registered_position": row.registered_position,
                "test_round": round_number,
                "test_date": row.test_date.date(),
                "height_cm": _safe_float(row.height_cm, 1),
                "weight_kg": _safe_float(row.weight_kg, 1),
                "skeletal_muscle_kg": _safe_float(row.muscle_mass_kg, 1),
                "body_fat_pct": _safe_float(row.body_fat_percentage, 1),
                "sprint_10m_sec": _safe_float(row.sprint_10m, 2),
                "sprint_30m_sec": _safe_float(row.sprint_30m, 2),
                "sprint_50m_sec": _safe_float(row.sprint_50m, 2),
                "sprint_100m_sec": _safe_float(row.sprint_100m, 2),
                "vertical_jump_cm": _safe_float(row.vertical_jump_cm, 1),
                "agility_t_sec": _safe_float(row.agility_t_test_sec, 2),
                "shuttle_run_count": None,
                "shuttle_run_sec": _safe_float(row.agility_shuttle_run_sec, 2),
                "endurance_m": None,
                "flexibility_cm": None,
            }
        )

    return records


def _metric_delta(current: float | None, previous: float | None, digits: int = 2) -> float | None:
    if current is None or previous is None:
        return None
    return round(current - previous, digits)


def _build_physical_sessions(physical_tests: pd.DataFrame) -> list[dict[str, Any]]:
    if physical_tests.empty:
        return []

    serialized_tests = _build_physical_test_records(physical_tests)
    tests_frame = pd.DataFrame(serialized_tests)
    tests_frame["test_date"] = pd.to_datetime(tests_frame["test_date"], errors="coerce")
    tests_frame = tests_frame.sort_values(["player_id", "test_date", "physical_id"], ascending=[True, False, False]).copy()
    for column in [
        "weight_kg",
        "skeletal_muscle_kg",
        "body_fat_pct",
        "sprint_10m_sec",
        "sprint_30m_sec",
        "sprint_50m_sec",
        "sprint_100m_sec",
        "vertical_jump_cm",
        "agility_t_sec",
        "shuttle_run_count",
    ]:
        # Rows are sorted newest first, so shift(-1) gives the previous older test
        # for the same player without re-querying.
        tests_frame[f"previous_{column}"] = tests_frame.groupby("player_id")[column].shift(-1)

    sessions: list[dict[str, Any]] = []
    grouped = tests_frame.sort_values(["test_date", "test_round"], ascending=[False, False]).groupby(
        ["season_year", "test_date", "test_round"],
        sort=False,
    )
    for (season_year, test_date, test_round), session_rows in grouped:
        rows: list[dict[str, Any]] = []
        for row in session_rows.sort_values(["registered_position", "player_name"], ascending=[True, True]).itertuples(index=False):
            rows.append(
                {
                    "playerId": str(row.player_id),
                    "playerName": str(row.player_name),
                    "registeredPosition": row.registered_position,
                    "metrics": {
                        "heightCm": {
                            "current": _safe_float(row.height_cm, 1),
                            "previous": None,
                            "delta": None,
                        },
                        "weightKg": {
                            "current": _safe_float(row.weight_kg, 1),
                            "previous": _safe_float(row.previous_weight_kg, 1),
                            "delta": _metric_delta(_safe_float(row.weight_kg, 1), _safe_float(row.previous_weight_kg, 1), 1),
                        },
                        "skeletalMuscleKg": {
                            "current": _safe_float(row.skeletal_muscle_kg, 1),
                            "previous": _safe_float(row.previous_skeletal_muscle_kg, 1),
                            "delta": _metric_delta(_safe_float(row.skeletal_muscle_kg, 1), _safe_float(row.previous_skeletal_muscle_kg, 1), 1),
                        },
                        "bodyFatPct": {
                            "current": _safe_float(row.body_fat_pct, 1),
                            "previous": _safe_float(row.previous_body_fat_pct, 1),
                            "delta": _metric_delta(_safe_float(row.body_fat_pct, 1), _safe_float(row.previous_body_fat_pct, 1), 1),
                        },
                        "sprint10mSec": {
                            "current": _safe_float(row.sprint_10m_sec, 2),
                            "previous": _safe_float(row.previous_sprint_10m_sec, 2),
                            "delta": _metric_delta(_safe_float(row.sprint_10m_sec, 2), _safe_float(row.previous_sprint_10m_sec, 2)),
                        },
                        "sprint30mSec": {
                            "current": _safe_float(row.sprint_30m_sec, 2),
                            "previous": _safe_float(row.previous_sprint_30m_sec, 2),
                            "delta": _metric_delta(_safe_float(row.sprint_30m_sec, 2), _safe_float(row.previous_sprint_30m_sec, 2)),
                        },
                        "sprint50mSec": {
                            "current": _safe_float(row.sprint_50m_sec, 2),
                            "previous": _safe_float(row.previous_sprint_50m_sec, 2),
                            "delta": _metric_delta(_safe_float(row.sprint_50m_sec, 2), _safe_float(row.previous_sprint_50m_sec, 2)),
                        },
                        "sprint100mSec": {
                            "current": _safe_float(row.sprint_100m_sec, 2),
                            "previous": _safe_float(row.previous_sprint_100m_sec, 2),
                            "delta": _metric_delta(_safe_float(row.sprint_100m_sec, 2), _safe_float(row.previous_sprint_100m_sec, 2)),
                        },
                        "verticalJumpCm": {
                            "current": _safe_float(row.vertical_jump_cm, 1),
                            "previous": _safe_float(row.previous_vertical_jump_cm, 1),
                            "delta": _metric_delta(_safe_float(row.vertical_jump_cm, 1), _safe_float(row.previous_vertical_jump_cm, 1), 1),
                        },
                        "agilityTSec": {
                            "current": _safe_float(row.agility_t_sec, 2),
                            "previous": _safe_float(row.previous_agility_t_sec, 2),
                            "delta": _metric_delta(_safe_float(row.agility_t_sec, 2), _safe_float(row.previous_agility_t_sec, 2)),
                        },
                        "shuttleRunCount": {
                            "current": _safe_float(row.shuttle_run_count, 0),
                            "previous": _safe_float(row.previous_shuttle_run_count, 0),
                            "delta": _metric_delta(_safe_float(row.shuttle_run_count, 0), _safe_float(row.previous_shuttle_run_count, 0), 0),
                        },
                    },
                }
            )

        sessions.append(
            {
                "key": f"{pd.Timestamp(test_date).date()}-{int(test_round)}",
                "testDate": pd.Timestamp(test_date).date(),
                "testRound": int(test_round),
                "seasonYear": int(season_year),
                "playerCount": len(rows),
                "rows": rows,
            }
        )

    return sessions


__all__ = [
    "_build_physical_sessions",
    "_build_physical_test_records",
]
