from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from ..service_reference import SERVICE_REFERENCE_DATE
from .shared import _season_id_for_date, _season_year_for_date


def _availability_bundle(
    injury_status: str | None,
    actual_return_date: Any,
    expected_return_date: Any,
    reference_date: date = SERVICE_REFERENCE_DATE,
) -> dict[str, str | None]:
    actual_return = pd.Timestamp(actual_return_date) if actual_return_date is not None and not pd.isna(actual_return_date) else None
    expected_return = pd.Timestamp(expected_return_date) if expected_return_date is not None and not pd.isna(expected_return_date) else None
    reference_ts = pd.Timestamp(reference_date)

    if injury_status == "rehab" and (actual_return is None or actual_return > reference_ts):
        return {
            "status_type": "재활 중",
            "match_availability": "불가",
            "training_participation": "휴식",
            "rehab_stage": "재활중",
        }

    if actual_return is not None and (reference_ts - actual_return).days <= 30:
        return {
            "status_type": "복귀 관리",
            "match_availability": "조건부",
            "training_participation": "부분참여",
            "rehab_stage": "복귀조절",
        }

    if expected_return is not None and expected_return >= reference_ts:
        return {
            "status_type": "복귀 예정",
            "match_availability": "조건부",
            "training_participation": "부분참여",
            "rehab_stage": "복귀조절",
        }

    return {
        "status_type": "복귀 완료",
        "match_availability": "가능",
        "training_participation": "전체참여",
        "rehab_stage": "해당없음",
    }


def _days_missed(
    injury_date: Any,
    actual_return_date: Any,
    expected_return_date: Any,
    reference_date: date = SERVICE_REFERENCE_DATE,
) -> int:
    if injury_date is None or pd.isna(injury_date):
        return 0

    end_date = actual_return_date
    if end_date is None or pd.isna(end_date):
        end_date = expected_return_date
    if end_date is None or pd.isna(end_date):
        end_date = reference_date
    return max(0, (pd.Timestamp(end_date) - pd.Timestamp(injury_date)).days)


def _build_medical_payloads(
    players: pd.DataFrame,
    injury_history: pd.DataFrame,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    reports: dict[str, dict[str, Any]] = {}
    history_map: dict[str, list[dict[str, Any]]] = {}
    reference_date = SERVICE_REFERENCE_DATE

    grouped_history = injury_history.groupby("player_id", sort=False) if not injury_history.empty else []
    grouped_records = {
        str(player_id): group.sort_values(["injury_date", "injury_id"], ascending=[False, False]).copy()
        for player_id, group in grouped_history
    }

    for player_row in players.to_dict("records"):
        player_id = str(player_row["player_id"])
        group = grouped_records.get(player_id)
        serialized_history: list[dict[str, Any]] = []
        latest_report = {
            "player_id": player_id,
            "player_name": str(player_row["name"]),
            "registered_position": player_row.get("primary_position"),
            "latest_record_date": None,
            "latest_status_type": "정상",
            "latest_injury_name": None,
            "latest_injury_type": None,
            "latest_injury_grade": None,
            "latest_rehab_stage": "해당없음",
            "latest_match_availability": "가능",
            "total_days_missed": 0,
            "unavailable_events": 0,
            "conditional_events": 0,
            "availability_risk_score": 0.0,
            "latest_return_to_play_date": None,
            "latest_training_participation": "전체참여",
        }

        if group is not None and not group.empty:
            total_days_missed = 0
            unavailable_events = 0
            conditional_events = 0

            for row in group.itertuples(index=False):
                availability = _availability_bundle(
                    getattr(row, "injury_status", None),
                    getattr(row, "actual_return_date", None),
                    getattr(row, "expected_return_date", None),
                    reference_date=reference_date,
                )
                days_missed = _days_missed(
                    getattr(row, "injury_date", None),
                    getattr(row, "actual_return_date", None),
                    getattr(row, "expected_return_date", None),
                    reference_date=reference_date,
                )
                total_days_missed += days_missed
                unavailable_events += 1 if availability["match_availability"] == "불가" else 0
                conditional_events += 1 if availability["match_availability"] == "조건부" else 0
                serialized_history.append(
                    {
                        "at_id": str(row.injury_id),
                        "season_id": _season_id_for_date(row.injury_date),
                        "season_year": _season_year_for_date(row.injury_date),
                        "player_id": player_id,
                        "record_date": row.injury_date,
                        "status_type": availability["status_type"],
                        "body_part": row.injury_part,
                        "injury_name": row.injury_type,
                        "injury_type": row.injury_type,
                        "injury_grade": row.severity_level,
                        "injury_start_date": row.injury_date,
                        "injury_end_date": row.actual_return_date,
                        "days_missed": days_missed,
                        "return_to_play_date": row.actual_return_date or row.expected_return_date,
                        "training_participation": availability["training_participation"],
                        "match_availability": availability["match_availability"],
                        "rehab_stage": availability["rehab_stage"],
                    }
                )

            latest = serialized_history[0]
            latest_report.update(
                {
                    "latest_record_date": latest["record_date"],
                    "latest_status_type": latest["status_type"],
                    "latest_injury_name": latest["injury_name"],
                    "latest_injury_type": latest["injury_type"],
                    "latest_injury_grade": latest["injury_grade"],
                    "latest_rehab_stage": latest["rehab_stage"],
                    "latest_match_availability": latest["match_availability"],
                    "total_days_missed": total_days_missed,
                    "unavailable_events": unavailable_events,
                    "conditional_events": conditional_events,
                    # Keep a single frontend-friendly risk score instead of exposing several raw counters.
                    "availability_risk_score": min(
                        100.0,
                        round(unavailable_events * 18 + conditional_events * 9 + total_days_missed * 0.25, 1),
                    ),
                    "latest_return_to_play_date": latest["return_to_play_date"],
                    "latest_training_participation": latest["training_participation"],
                }
            )

        reports[player_id] = latest_report
        history_map[player_id] = serialized_history

    return reports, history_map


__all__ = ["_build_medical_payloads"]
