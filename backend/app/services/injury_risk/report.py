from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from ...schemas import (
    InjuryRiskFactors,
    PlayerInjuryRiskItem,
    PlayerInjuryRiskResponse,
    RecentInjuryHistoryItem,
)
from .medical import (
    _compute_injury_features,
    _compute_physical_features,
    _compute_symptom_features,
)
from .shared import (
    InjuryRiskSourceFrames,
    _build_session_frame,
    _compute_load_features,
    _filter_ranked_report,
    _load_injury_risk_source_frames,
    _optional_date,
    _optional_float,
    _optional_int,
    _optional_text,
    _resolve_load_snapshot_date,
    _resolve_snapshot_date,
    _top_reason_messages,
)


REPORT_FILL_COLUMNS = [
    "load_score",
    "physical_change_score",
    "injury_history_score",
    "return_to_play_score",
    "symptom_score",
    "acute_load_7d",
    "acute_distance_7d",
    "high_intensity_sessions_7d",
    "match_minutes_7d",
    "sprint_count_7d",
    "injuries_last_180d",
    "injuries_last_365d",
    "recent_symptom_count_120d",
    "recent_medical_consultation_count_14d",
]


def _build_recent_injury_history(
    players: pd.DataFrame,
    injuries: pd.DataFrame,
    snapshot_ts: pd.Timestamp,
    limit: int = 24,
) -> list[RecentInjuryHistoryItem]:
    if injuries.empty:
        return []

    history = injuries.copy()
    for column in ["injury_date", "expected_return_date", "actual_return_date"]:
        history[column] = pd.to_datetime(history[column], errors="coerce")
    history = history[history["injury_date"].notna() & (history["injury_date"] <= snapshot_ts)].copy()
    if history.empty:
        return []

    history = history.merge(
        players[["player_id", "name", "primary_position", "status"]],
        on="player_id",
        how="left",
    )
    history = history.sort_values(
        ["injury_date", "actual_return_date", "expected_return_date", "injury_id"],
        ascending=[False, False, False, False],
        na_position="last",
    ).head(limit)

    return [_serialize_recent_injury_history_item(row, snapshot_ts) for row in history.itertuples(index=False)]


def _build_reason_list(row: Any) -> list[str]:
    reasons: list[tuple[float, str]] = []

    if bool(row.open_rehab_flag):
        reasons.append((100.0, "현재 재활 상태라 즉시 관리가 필요합니다."))
    if pd.notna(row.days_since_return) and float(row.days_since_return) <= 30:
        reasons.append((92.0, f"복귀 후 {int(row.days_since_return)}일 경과라 재부상 관리 구간입니다."))
    if bool(row.recent_symptom_flag) and pd.notna(row.latest_symptom_days_ago):
        symptom_days = int(row.latest_symptom_days_ago)
        if symptom_days <= 30:
            reasons.append((86.0, f"최근 {symptom_days}일 내 통증 또는 불편감 신호가 기록됐습니다."))
        else:
            reasons.append((64.0, f"최근 120일 내 통증 또는 불편감 이력이 있고 마지막 기록은 {symptom_days}일 전입니다."))
    if row.load_direction == "spike" and pd.notna(row.acute_chronic_ratio):
        reasons.append((88.0, f"최근 7일 부하가 기준 대비 {row.acute_chronic_ratio:.2f}배로 급증했습니다."))
    if (
        row.primary_position != "GK"
        and row.load_direction == "drop"
        and pd.notna(row.acute_chronic_ratio)
    ):
        if pd.notna(row.distance_ratio) and float(row.distance_ratio) <= float(row.acute_chronic_ratio):
            reasons.append((82.0, f"최근 7일 활동량이 개인 기준의 {row.distance_ratio:.2f}배 수준으로 떨어졌습니다."))
        else:
            reasons.append((82.0, f"최근 7일 부하가 개인 기준의 {row.acute_chronic_ratio:.2f}배 수준으로 떨어졌습니다."))
    if pd.notna(row.sprint_ratio) and float(row.sprint_ratio) >= 1.25 and int(row.sprint_count_7d) >= 35:
        reasons.append((84.0, f"최근 7일 스프린트가 개인 기준치 대비 {row.sprint_ratio:.2f}배로 늘었습니다."))
    if pd.notna(row.acute_load_percentile) and float(row.acute_load_percentile) >= 85:
        top_band = max(1, 100 - int(round(float(row.acute_load_percentile))))
        reasons.append((79.0, f"최근 7일 절대 부하가 팀 내 상위 {top_band}% 수준입니다."))
    if row.high_intensity_sessions_7d >= 3:
        reasons.append((70.0, f"최근 7일 고강도 훈련이 {int(row.high_intensity_sessions_7d)}회 누적됐습니다."))
    if row.match_minutes_7d >= 160:
        reasons.append((66.0, f"최근 7일 경기 출전시간이 {int(row.match_minutes_7d)}분으로 높습니다."))
    if int(row.sprint_count_7d) >= 55:
        reasons.append((72.0, f"최근 7일 스프린트 노출이 {int(row.sprint_count_7d)}회로 많습니다."))
    if pd.notna(row.body_fat_delta) and float(row.body_fat_delta) >= 0.6:
        reasons.append((76.0, f"체지방이 최근 측정 대비 {row.body_fat_delta:.1f}%p 증가했습니다."))
    elif pd.notna(row.body_fat_delta) and float(row.body_fat_delta) >= 0.35:
        reasons.append((60.0, f"체지방이 최근 측정 대비 {row.body_fat_delta:.1f}%p 증가 추세입니다."))
    if pd.notna(row.muscle_mass_delta) and float(row.muscle_mass_delta) <= -0.5:
        reasons.append((74.0, f"근육량이 최근 측정 대비 {abs(row.muscle_mass_delta):.1f}kg 감소했습니다."))
    elif pd.notna(row.muscle_mass_delta) and float(row.muscle_mass_delta) <= -0.25:
        reasons.append((62.0, f"근육량이 최근 측정 대비 {abs(row.muscle_mass_delta):.1f}kg 감소 추세입니다."))
    if bool(row.reinjury_flag):
        reasons.append((84.0, "같은 부위의 부상 이력이 반복되고 있습니다."))
    if int(row.injuries_last_180d) >= 2:
        reasons.append((78.0, f"최근 180일 내 부상이 {int(row.injuries_last_180d)}건으로 잦습니다."))
    if int(row.injuries_last_365d) >= 1:
        reasons.append((58.0, f"최근 1년 내 부상 이력이 {int(row.injuries_last_365d)}건 있습니다."))
    if int(row.recent_medical_consultation_count_14d) >= 2:
        reasons.append((56.0, f"최근 14일 메디컬 상담이 {int(row.recent_medical_consultation_count_14d)}회 있었습니다."))
    return _top_reason_messages(reasons, "최근 위험 신호가 크지 않습니다.")


def _build_injury_risk_report_frame(
    source_frames: InjuryRiskSourceFrames,
    load_snapshot_ts: pd.Timestamp,
    snapshot_ts: pd.Timestamp,
) -> pd.DataFrame:
    sessions = _build_session_frame(source_frames.training_load, source_frames.match_load, load_snapshot_ts)
    load_features = _compute_load_features(source_frames.players, sessions, load_snapshot_ts)
    physical_features = _compute_physical_features(source_frames.players, source_frames.physical_profiles, snapshot_ts)
    injury_features = _compute_injury_features(source_frames.players, source_frames.injuries, snapshot_ts)
    symptom_features = _compute_symptom_features(
        source_frames.players,
        source_frames.injuries,
        source_frames.counseling_notes,
        snapshot_ts,
    )

    report = (
        source_frames.players.merge(load_features, on="player_id", how="left")
        .merge(physical_features, on="player_id", how="left")
        .merge(injury_features, on="player_id", how="left")
        .merge(symptom_features, on="player_id", how="left")
    )
    for column in REPORT_FILL_COLUMNS:
        report[column] = report[column].fillna(0)

    # Overall risk keeps each evidence source explicit so one noisy signal cannot dominate alone.
    report["overall_risk_score"] = (
        report["load_score"]
        + report["physical_change_score"]
        + report["injury_history_score"]
        + report["return_to_play_score"]
        + report["symptom_score"]
    ).round(2)
    report["risk_band"] = np.select(
        [report["overall_risk_score"] >= 55, report["overall_risk_score"] >= 25],
        ["risk", "watch"],
        default="normal",
    )
    report["snapshot_date"] = snapshot_ts.date()
    return report


def _serialize_recent_injury_history_item(row: Any, snapshot_ts: pd.Timestamp) -> RecentInjuryHistoryItem:
    return RecentInjuryHistoryItem(
        injury_id=str(row.injury_id),
        player_id=str(row.player_id),
        name=_optional_text(row.name) or str(row.player_id),
        primary_position=_optional_text(row.primary_position) or "-",
        status=_optional_text(row.status) or "unknown",
        injury_date=_optional_date(row.injury_date) or snapshot_ts.date(),
        injury_type=_optional_text(row.injury_type),
        injury_part=_optional_text(row.injury_part),
        severity_level=_optional_text(row.severity_level),
        injury_status=_optional_text(row.injury_status),
        expected_return_date=_optional_date(row.expected_return_date),
        actual_return_date=_optional_date(row.actual_return_date),
        notes=_optional_text(row.notes),
    )


def _serialize_injury_risk_item(row: Any) -> PlayerInjuryRiskItem:
    return PlayerInjuryRiskItem(
        snapshot_date=row.snapshot_date,
        player_id=row.player_id,
        name=row.name,
        primary_position=row.primary_position,
        status=row.status,
        overall_risk_score=float(row.overall_risk_score),
        risk_band=str(row.risk_band),
        reasons=list(row.reasons),
        factors=InjuryRiskFactors(
            load_score=float(row.load_score),
            physical_change_score=float(row.physical_change_score),
            injury_history_score=float(row.injury_history_score),
            return_to_play_score=float(row.return_to_play_score),
            symptom_score=float(row.symptom_score),
            acute_load_7d=float(row.acute_load_7d),
            acute_load_percentile=_optional_float(row.acute_load_percentile, 1),
            chronic_load_baseline=_optional_float(row.chronic_load_baseline),
            acute_chronic_ratio=_optional_float(row.acute_chronic_ratio, 2),
            acute_distance_7d=_optional_float(row.acute_distance_7d, 2),
            chronic_distance_baseline=_optional_float(row.chronic_distance_baseline, 2),
            distance_ratio=_optional_float(row.distance_ratio, 2),
            high_intensity_sessions_7d=int(row.high_intensity_sessions_7d),
            match_minutes_7d=int(row.match_minutes_7d),
            sprint_count_7d=int(row.sprint_count_7d),
            sprint_count_baseline=_optional_float(row.sprint_count_baseline, 2),
            sprint_ratio=_optional_float(row.sprint_ratio, 2),
            body_fat_delta=_optional_float(row.body_fat_delta, 2),
            muscle_mass_delta=_optional_float(row.muscle_mass_delta, 2),
            weight_delta=_optional_float(row.weight_delta, 2),
            injuries_last_180d=int(row.injuries_last_180d),
            injuries_last_365d=int(row.injuries_last_365d),
            reinjury_flag=bool(row.reinjury_flag),
            days_since_return=_optional_int(row.days_since_return),
            open_rehab_flag=bool(row.open_rehab_flag),
            recent_symptom_count_120d=int(row.recent_symptom_count_120d),
            recent_symptom_flag=bool(row.recent_symptom_flag),
            latest_symptom_days_ago=_optional_int(row.latest_symptom_days_ago),
            recent_medical_consultation_count_14d=int(row.recent_medical_consultation_count_14d),
        ),
    )


def build_player_injury_risk_report(
    as_of_date: date | None = None,
    limit: int | None = None,
    risk_band: str | None = None,
) -> PlayerInjuryRiskResponse:
    source_frames = _load_injury_risk_source_frames()
    snapshot_ts = _resolve_snapshot_date(
        as_of_date,
        [
            (source_frames.training_load, "session_date"),
            (source_frames.match_load, "session_date"),
            (source_frames.physical_profiles, "created_at"),
            (source_frames.injuries, "actual_return_date"),
            (source_frames.injuries, "injury_date"),
        ],
    )
    load_snapshot_ts = _resolve_load_snapshot_date(
        source_frames.training_load,
        source_frames.match_load,
        snapshot_ts,
    )
    report = _build_injury_risk_report_frame(source_frames, load_snapshot_ts, snapshot_ts)
    recent_history = _build_recent_injury_history(
        players=source_frames.players,
        injuries=source_frames.injuries,
        snapshot_ts=snapshot_ts,
    )
    report = _filter_ranked_report(report, risk_band=risk_band, limit=limit)
    report["reasons"] = [_build_reason_list(row) for row in report.itertuples(index=False)]
    items = [_serialize_injury_risk_item(row) for row in report.itertuples(index=False)]

    return PlayerInjuryRiskResponse(
        snapshot_date=snapshot_ts.date(),
        total=len(items),
        items=items,
        recent_history=recent_history,
    )
