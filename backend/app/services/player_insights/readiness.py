from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from ...schemas import (
    PerformanceReadinessFactors,
    PlayerPerformanceReadinessItem,
    PlayerPerformanceReadinessResponse,
)
from .shared import (
    ReadinessSourceFrames,
    _compute_evaluation_features,
    _compute_match_form_features,
    _filter_ranked_report,
    _load_readiness_source_frames,
    _merge_player_features,
    _optional_date,
    _optional_float,
    _resolve_snapshot_date,
    _top_reason_messages,
    _build_match_frame,
)


COUNSELING_TOPIC_WEIGHTS = {
    "멘탈 관리": 1.0,
    "부상 관리": 1.0,
    "훈련 태도": 0.7,
    "경기 피드백": 0.3,
    "진로 상담": 0.2,
}
POSITIVE_COUNSELING_KEYWORDS = ("자신감 회복", "목표 설정", "집중도 향상", "향상", "회복")
CAUTION_COUNSELING_KEYWORDS = ("부상", "회복 관리", "멘탈", "집중도", "관리")

READINESS_FILL_COLUMNS = [
    "match_form_score",
    "evaluation_score",
    "mental_readiness_score",
    "availability_penalty",
    "recent_match_count",
    "recent_counseling_count_90d",
    "caution_note_count_90d",
]
READINESS_SORT_COLUMNS = ["readiness_score", "match_form_score", "evaluation_score", "name"]
DEFAULT_MENTAL_READINESS_SCORE = 16.0


def _compute_counseling_features(players: pd.DataFrame, counseling: pd.DataFrame, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    base["recent_counseling_count_90d"] = 0
    base["caution_note_count_90d"] = 0
    base["positive_note_count_90d"] = 0
    base["mental_readiness_score"] = DEFAULT_MENTAL_READINESS_SCORE

    if counseling.empty:
        return base

    frame = counseling.copy()
    frame["counseling_date"] = pd.to_datetime(frame["counseling_date"], errors="coerce")
    frame = frame[frame["counseling_date"].notna() & (frame["counseling_date"] <= snapshot_ts)].copy()
    frame["days_ago"] = (snapshot_ts - frame["counseling_date"]).dt.days
    recent = frame.loc[frame["days_ago"] <= 90].copy()
    if recent.empty:
        return base

    recent["topic_weight"] = recent["topic"].map(COUNSELING_TOPIC_WEIGHTS).fillna(0.3)
    recent["positive_flag"] = recent["summary"].fillna("").apply(
        lambda text: any(keyword in text for keyword in POSITIVE_COUNSELING_KEYWORDS)
    )
    recent["caution_flag"] = recent["summary"].fillna("").apply(
        lambda text: any(keyword in text for keyword in CAUTION_COUNSELING_KEYWORDS)
    ) | recent["topic"].isin(["멘탈 관리", "부상 관리", "훈련 태도"])

    note_count = recent.groupby("player_id").size()
    caution_count = recent.groupby("player_id")["caution_flag"].sum()
    positive_count = recent.groupby("player_id")["positive_flag"].sum()
    topic_weight_sum = recent.groupby("player_id")["topic_weight"].sum()

    base["recent_counseling_count_90d"] = base["player_id"].map(note_count).fillna(0).astype(int)
    base["caution_note_count_90d"] = base["player_id"].map(caution_count).fillna(0).astype(int)
    base["positive_note_count_90d"] = base["player_id"].map(positive_count).fillna(0).astype(int)

    # Counseling notes act as a soft readiness modifier rather than a hard availability blocker.
    mental_signal = np.clip(
        0.8
        - base["player_id"].map(topic_weight_sum).fillna(0.0) * 0.06
        - base["caution_note_count_90d"] * 0.05
        + base["positive_note_count_90d"] * 0.04,
        0.25,
        1.0,
    )
    base["mental_readiness_score"] = np.round(mental_signal * 20.0, 2)
    return base.drop(columns=["positive_note_count_90d"])


def _build_readiness_reasons(row: Any) -> list[str]:
    reasons: list[tuple[float, str]] = []
    if row.status == "injured":
        reasons.append((100.0, "현재 부상 상태라 경기 투입 준비도를 보수적으로 봐야 합니다."))
    if pd.notna(row.recent_form_index) and float(row.recent_form_index) >= 72:
        reasons.append((86.0, "최근 5경기 퍼포먼스 지수가 높게 유지되고 있습니다."))
    if pd.notna(row.form_delta) and float(row.form_delta) >= 6:
        reasons.append((82.0, f"최근 5경기 폼이 이전 구간 대비 {row.form_delta:.1f}점 개선됐습니다."))
    if pd.notna(row.form_delta) and float(row.form_delta) <= -6:
        reasons.append((84.0, f"최근 5경기 폼이 이전 구간 대비 {abs(row.form_delta):.1f}점 하락했습니다."))
    if pd.notna(row.latest_evaluation_average) and float(row.latest_evaluation_average) >= 80:
        reasons.append((78.0, f"최근 코치 평가 평균이 {row.latest_evaluation_average:.1f}점으로 높습니다."))
    if pd.notna(row.evaluation_delta) and float(row.evaluation_delta) >= 3:
        reasons.append((76.0, f"최근 코치 평가가 이전 대비 {row.evaluation_delta:.1f}점 상승했습니다."))
    if pd.notna(row.evaluation_delta) and float(row.evaluation_delta) <= -3:
        reasons.append((80.0, f"최근 코치 평가가 이전 대비 {abs(row.evaluation_delta):.1f}점 하락했습니다."))
    if int(row.caution_note_count_90d) >= 3:
        reasons.append((74.0, f"최근 90일 상담/관리 메모가 {int(row.caution_note_count_90d)}건으로 관리 이슈가 이어지고 있습니다."))
    if pd.notna(row.recent_match_minutes_avg) and float(row.recent_match_minutes_avg) <= 35 and int(row.recent_match_count) >= 2:
        reasons.append((68.0, "최근 경기 투입 시간이 낮아 실전 준비도 확인이 더 필요합니다."))
    return _top_reason_messages(reasons, "최근 준비도 지표가 안정적인 편입니다.")


def _build_readiness_report_frame(source_frames: ReadinessSourceFrames, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    match_frame = _build_match_frame(source_frames.match_stats, snapshot_ts)
    match_features = _compute_match_form_features(source_frames.players, match_frame)
    evaluation_features = _compute_evaluation_features(source_frames.players, source_frames.evaluations)
    counseling_features = _compute_counseling_features(source_frames.players, source_frames.counseling, snapshot_ts)

    report = _merge_player_features(
        source_frames.players,
        match_features,
        evaluation_features,
        counseling_features,
    )
    report["availability_penalty"] = np.where(report["status"] == "injured", 22.0, 0.0)
    for column in READINESS_FILL_COLUMNS:
        report[column] = report[column].fillna(0)

    # Final readiness weights match evidence highest, then coach input and recent note context.
    report["readiness_score"] = np.clip(
        report["match_form_score"]
        + report["evaluation_score"]
        + report["mental_readiness_score"]
        - report["availability_penalty"],
        0,
        100,
    ).round(2)
    report["readiness_band"] = np.select(
        [report["readiness_score"] >= 70, report["readiness_score"] >= 52],
        ["ready", "managed"],
        default="watch",
    )
    report["snapshot_date"] = snapshot_ts.date()
    return report


def _serialize_readiness_item(row: Any) -> PlayerPerformanceReadinessItem:
    return PlayerPerformanceReadinessItem(
        snapshot_date=row.snapshot_date,
        player_id=row.player_id,
        name=row.name,
        primary_position=row.primary_position,
        status=row.status,
        readiness_score=float(row.readiness_score),
        readiness_band=str(row.readiness_band),
        reasons=list(row.reasons),
        factors=PerformanceReadinessFactors(
            match_form_score=float(row.match_form_score),
            evaluation_score=float(row.evaluation_score),
            mental_readiness_score=float(row.mental_readiness_score),
            availability_penalty=float(row.availability_penalty),
            recent_form_index=_optional_float(row.recent_form_index, 2),
            previous_form_index=_optional_float(row.previous_form_index, 2),
            form_delta=_optional_float(row.form_delta, 2),
            recent_match_count=int(row.recent_match_count),
            recent_match_minutes_avg=_optional_float(row.recent_match_minutes_avg, 1),
            latest_match_date=_optional_date(row.latest_match_date),
            latest_evaluation_average=_optional_float(row.latest_evaluation_average, 2),
            previous_evaluation_average=_optional_float(row.previous_evaluation_average, 2),
            evaluation_delta=_optional_float(row.evaluation_delta, 2),
            latest_evaluation_date=_optional_date(row.latest_evaluation_date),
            recent_counseling_count_90d=int(row.recent_counseling_count_90d),
            caution_note_count_90d=int(row.caution_note_count_90d),
        ),
    )


def _build_readiness_items(report: pd.DataFrame) -> list[PlayerPerformanceReadinessItem]:
    return [_serialize_readiness_item(row) for row in report.itertuples(index=False)]


def build_player_performance_readiness_report(
    as_of_date: date | None = None,
    limit: int | None = None,
    readiness_band: str | None = None,
) -> PlayerPerformanceReadinessResponse:
    source_frames = _load_readiness_source_frames()
    snapshot_ts = _resolve_snapshot_date(
        as_of_date,
        [
            (source_frames.match_stats, "match_date"),
            (source_frames.evaluations, "evaluation_date"),
            (source_frames.counseling, "counseling_date"),
        ],
    )
    report = _build_readiness_report_frame(source_frames, snapshot_ts)
    report = _filter_ranked_report(
        report,
        band_column="readiness_band",
        band_value=readiness_band,
        sort_columns=READINESS_SORT_COLUMNS,
        limit=limit,
    )
    report["reasons"] = [_build_readiness_reasons(row) for row in report.itertuples(index=False)]
    items = _build_readiness_items(report)

    return PlayerPerformanceReadinessResponse(
        snapshot_date=snapshot_ts.date(),
        total=len(items),
        items=items,
    )
