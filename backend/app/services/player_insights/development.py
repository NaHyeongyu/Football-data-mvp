from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from ...schemas import (
    DevelopmentReportFactors,
    PlayerDevelopmentReportItem,
    PlayerDevelopmentReportResponse,
)
from .shared import (
    DevelopmentSourceFrames,
    _build_match_frame,
    _compute_evaluation_features,
    _compute_match_form_features,
    _filter_ranked_report,
    _load_development_source_frames,
    _optional_date,
    _optional_float,
    _optional_int,
    _resolve_snapshot_date,
    _top_reason_messages,
)


GROWTH_SORT_COLUMNS = ["growth_score", "physical_growth_score", "performance_growth_score", "name"]
DEFAULT_PHYSICAL_GROWTH_SCORE = 17.5


def _summarize_physical_growth(
    player_id: str,
    profiles: pd.DataFrame,
    lookback_cutoff: pd.Timestamp,
) -> dict[str, Any]:
    ordered = profiles.sort_values("created_at").reset_index(drop=True)
    latest = ordered.iloc[-1]
    history = ordered.iloc[:-1]
    if history.empty:
        return {
            "player_id": player_id,
            "latest_profile_date": latest["created_at"],
            "physical_growth_score": DEFAULT_PHYSICAL_GROWTH_SCORE,
        }

    # Prefer a baseline inside the lookback window; otherwise fall back to the earliest available profile.
    baseline_candidates = history.loc[history["created_at"] >= lookback_cutoff]
    baseline = baseline_candidates.iloc[0] if not baseline_candidates.empty else history.iloc[0]
    muscle_delta = float(latest["muscle_mass_kg"] - baseline["muscle_mass_kg"])
    body_fat_delta = float(latest["body_fat_percentage"] - baseline["body_fat_percentage"])
    weight_delta = float(latest["weight_kg"] - baseline["weight_kg"])
    comparison_days = int((latest["created_at"] - baseline["created_at"]).days)

    muscle_signal = np.clip(muscle_delta / 2.5, -1, 1)
    body_fat_signal = np.clip((-body_fat_delta) / 2.5, -1, 1)
    if muscle_delta > 0 and weight_delta > 0:
        weight_signal = min(weight_delta / 3.0, 0.8)
    else:
        weight_signal = -min(abs(weight_delta) / 4.0, 0.8) if abs(weight_delta) >= 3 else 0.1

    physical_signal = np.clip(
        0.55 * muscle_signal + 0.35 * body_fat_signal + 0.10 * weight_signal,
        -1,
        1,
    )
    return {
        "player_id": player_id,
        "comparison_window_days": comparison_days,
        "muscle_mass_delta": round(muscle_delta, 2),
        "body_fat_delta": round(body_fat_delta, 2),
        "weight_delta": round(weight_delta, 2),
        "latest_profile_date": latest["created_at"],
        "physical_growth_score": round(((physical_signal + 1.0) / 2.0) * 35.0, 2),
    }


def _compute_physical_growth_features(players: pd.DataFrame, physical_profiles: pd.DataFrame, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    base["comparison_window_days"] = np.nan
    base["muscle_mass_delta"] = np.nan
    base["body_fat_delta"] = np.nan
    base["weight_delta"] = np.nan
    base["latest_profile_date"] = pd.NaT
    base["physical_growth_score"] = DEFAULT_PHYSICAL_GROWTH_SCORE

    if physical_profiles.empty:
        return base

    profiles = physical_profiles.copy()
    profiles["created_at"] = pd.to_datetime(profiles["created_at"], errors="coerce")
    profiles = profiles[profiles["created_at"].notna() & (profiles["created_at"] <= snapshot_ts)].copy()
    if profiles.empty:
        return base

    lookback_cutoff = snapshot_ts - pd.Timedelta(days=365)
    details = pd.DataFrame(
        [
            _summarize_physical_growth(player_id, group, lookback_cutoff)
            for player_id, group in profiles.groupby("player_id")
        ]
    )
    merged = base.merge(details, on="player_id", how="left", suffixes=("", "_new"))
    for column in [
        "comparison_window_days",
        "muscle_mass_delta",
        "body_fat_delta",
        "weight_delta",
        "latest_profile_date",
        "physical_growth_score",
    ]:
        replacement = f"{column}_new"
        if replacement in merged.columns:
            merged[column] = merged[replacement].where(merged[replacement].notna(), merged[column])
            merged = merged.drop(columns=[replacement])
    return merged


def _compute_development_features(
    players: pd.DataFrame,
    match_features: pd.DataFrame,
    evaluation_features: pd.DataFrame,
    physical_growth: pd.DataFrame,
) -> pd.DataFrame:
    report = (
        players[["player_id"]]
        .merge(match_features, on="player_id", how="left")
        .merge(evaluation_features, on="player_id", how="left", suffixes=("", "_evaluation"))
        .merge(physical_growth, on="player_id", how="left", suffixes=("", "_physical"))
    )

    for column in [
        "recent_form_index",
        "previous_form_index",
        "form_delta",
        "recent_distance_avg",
        "previous_distance_avg",
        "recent_sprint_avg",
        "previous_sprint_avg",
        "recent_max_speed_avg",
        "previous_max_speed_avg",
        "latest_evaluation_average",
        "previous_evaluation_average",
        "evaluation_delta",
    ]:
        if column not in report.columns:
            report[column] = np.nan

    # Growth favors sustained performance trend first, then GPS exposure and physical change.
    form_signal = np.clip(report["form_delta"].fillna(0.0) / 18.0, -1, 1)
    current_form_signal = np.clip((report["recent_form_index"].fillna(50.0) - 50.0) / 25.0, -1, 1)
    report["performance_growth_score"] = np.round(
        ((np.clip(0.7 * form_signal + 0.3 * current_form_signal, -1, 1) + 1.0) / 2.0) * 35.0,
        2,
    )

    distance_delta_pct = np.where(
        report["previous_distance_avg"].fillna(0.0) > 0,
        (report["recent_distance_avg"].fillna(0.0) - report["previous_distance_avg"].fillna(0.0))
        / report["previous_distance_avg"].replace(0, np.nan),
        0.0,
    )
    sprint_delta_pct = np.where(
        report["previous_sprint_avg"].fillna(0.0) > 0,
        (report["recent_sprint_avg"].fillna(0.0) - report["previous_sprint_avg"].fillna(0.0))
        / report["previous_sprint_avg"].replace(0, np.nan),
        0.0,
    )
    speed_delta = report["recent_max_speed_avg"].fillna(0.0) - report["previous_max_speed_avg"].fillna(0.0)
    gps_signal = np.clip(
        0.4 * np.clip(distance_delta_pct / 0.12, -1, 1)
        + 0.4 * np.clip(sprint_delta_pct / 0.18, -1, 1)
        + 0.2 * np.clip(speed_delta / 1.2, -1, 1),
        -1,
        1,
    )
    report["gps_growth_score"] = np.round(((gps_signal + 1.0) / 2.0) * 20.0, 2)

    eval_signal = np.clip(
        0.7 * np.clip(report["evaluation_delta"].fillna(0.0) / 8.0, -1, 1)
        + 0.3 * np.clip((report["latest_evaluation_average"].fillna(75.0) - 75.0) / 12.0, -1, 1),
        -1,
        1,
    )
    report["evaluation_growth_score"] = np.round(((eval_signal + 1.0) / 2.0) * 10.0, 2)

    report["physical_growth_score"] = report.get(
        "physical_growth_score",
        pd.Series(DEFAULT_PHYSICAL_GROWTH_SCORE, index=report.index),
    ).fillna(DEFAULT_PHYSICAL_GROWTH_SCORE)
    report["growth_score"] = (
        report["physical_growth_score"]
        + report["performance_growth_score"]
        + report["gps_growth_score"]
        + report["evaluation_growth_score"]
    ).round(2)
    return report


def _build_growth_reasons(row: Any) -> list[str]:
    reasons: list[tuple[float, str]] = []
    if pd.notna(row.muscle_mass_delta) and float(row.muscle_mass_delta) >= 1.0:
        reasons.append((84.0, f"근육량이 비교 구간 대비 {row.muscle_mass_delta:.1f}kg 증가했습니다."))
    if pd.notna(row.muscle_mass_delta) and float(row.muscle_mass_delta) <= -0.8:
        reasons.append((86.0, f"근육량이 비교 구간 대비 {abs(row.muscle_mass_delta):.1f}kg 감소했습니다."))
    if pd.notna(row.body_fat_delta) and float(row.body_fat_delta) <= -0.8:
        reasons.append((82.0, f"체지방이 비교 구간 대비 {abs(row.body_fat_delta):.1f}%p 감소했습니다."))
    if pd.notna(row.body_fat_delta) and float(row.body_fat_delta) >= 0.8:
        reasons.append((84.0, f"체지방이 비교 구간 대비 {row.body_fat_delta:.1f}%p 증가했습니다."))
    if pd.notna(row.form_delta) and float(row.form_delta) >= 6:
        reasons.append((78.0, f"최근 5경기 퍼포먼스 지수가 이전 구간 대비 {row.form_delta:.1f}점 상승했습니다."))
    if pd.notna(row.form_delta) and float(row.form_delta) <= -6:
        reasons.append((80.0, f"최근 5경기 퍼포먼스 지수가 이전 구간 대비 {abs(row.form_delta):.1f}점 하락했습니다."))
    if pd.notna(row.recent_sprint_avg) and pd.notna(row.previous_sprint_avg) and float(row.recent_sprint_avg) - float(row.previous_sprint_avg) >= 6:
        reasons.append((74.0, "최근 경기 스프린트 노출이 이전 구간보다 뚜렷하게 증가했습니다."))
    if pd.notna(row.evaluation_delta) and float(row.evaluation_delta) >= 3:
        reasons.append((72.0, f"최근 코치 평가 평균이 {row.evaluation_delta:.1f}점 상승했습니다."))
    if pd.notna(row.evaluation_delta) and float(row.evaluation_delta) <= -3:
        reasons.append((74.0, f"최근 코치 평가 평균이 {abs(row.evaluation_delta):.1f}점 하락했습니다."))
    return _top_reason_messages(reasons, "비교 구간 대비 큰 성장 또는 하락 신호는 아직 제한적입니다.")


def _build_development_report_frame(source_frames: DevelopmentSourceFrames, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    match_frame = _build_match_frame(source_frames.match_stats, snapshot_ts)
    match_features = _compute_match_form_features(source_frames.players, match_frame)
    evaluation_features = _compute_evaluation_features(source_frames.players, source_frames.evaluations)
    physical_growth = _compute_physical_growth_features(
        source_frames.players,
        source_frames.physical_profiles,
        snapshot_ts,
    )
    report = _compute_development_features(
        source_frames.players,
        match_features,
        evaluation_features,
        physical_growth,
    )
    report = source_frames.players.merge(report, on="player_id", how="left")
    report["growth_band"] = np.select(
        [report["growth_score"] >= 60, report["growth_score"] >= 45],
        ["rising", "stable"],
        default="monitor",
    )
    report["snapshot_date"] = snapshot_ts.date()
    return report


def _serialize_development_item(row: Any) -> PlayerDevelopmentReportItem:
    return PlayerDevelopmentReportItem(
        snapshot_date=row.snapshot_date,
        player_id=row.player_id,
        name=row.name,
        primary_position=row.primary_position,
        status=row.status,
        growth_score=float(row.growth_score),
        growth_band=str(row.growth_band),
        reasons=list(row.reasons),
        factors=DevelopmentReportFactors(
            physical_growth_score=float(row.physical_growth_score),
            performance_growth_score=float(row.performance_growth_score),
            gps_growth_score=float(row.gps_growth_score),
            evaluation_growth_score=float(row.evaluation_growth_score),
            comparison_window_days=_optional_int(row.comparison_window_days),
            muscle_mass_delta=_optional_float(row.muscle_mass_delta, 2),
            body_fat_delta=_optional_float(row.body_fat_delta, 2),
            weight_delta=_optional_float(row.weight_delta, 2),
            recent_form_index=_optional_float(row.recent_form_index, 2),
            previous_form_index=_optional_float(row.previous_form_index, 2),
            form_delta=_optional_float(row.form_delta, 2),
            recent_distance_avg=_optional_float(row.recent_distance_avg, 1),
            previous_distance_avg=_optional_float(row.previous_distance_avg, 1),
            recent_sprint_avg=_optional_float(row.recent_sprint_avg, 1),
            previous_sprint_avg=_optional_float(row.previous_sprint_avg, 1),
            recent_max_speed_avg=_optional_float(row.recent_max_speed_avg, 2),
            previous_max_speed_avg=_optional_float(row.previous_max_speed_avg, 2),
            latest_evaluation_average=_optional_float(row.latest_evaluation_average, 2),
            previous_evaluation_average=_optional_float(row.previous_evaluation_average, 2),
            evaluation_delta=_optional_float(row.evaluation_delta, 2),
            latest_profile_date=_optional_date(row.latest_profile_date),
        ),
    )


def _build_development_items(report: pd.DataFrame) -> list[PlayerDevelopmentReportItem]:
    return [_serialize_development_item(row) for row in report.itertuples(index=False)]


def build_player_development_report(
    as_of_date: date | None = None,
    limit: int | None = None,
    growth_band: str | None = None,
) -> PlayerDevelopmentReportResponse:
    source_frames = _load_development_source_frames()
    snapshot_ts = _resolve_snapshot_date(
        as_of_date,
        [
            (source_frames.match_stats, "match_date"),
            (source_frames.evaluations, "evaluation_date"),
            (source_frames.physical_profiles, "created_at"),
        ],
    )
    report = _build_development_report_frame(source_frames, snapshot_ts)
    report = _filter_ranked_report(
        report,
        band_column="growth_band",
        band_value=growth_band,
        sort_columns=GROWTH_SORT_COLUMNS,
        limit=limit,
    )
    report["reasons"] = [_build_growth_reasons(row) for row in report.itertuples(index=False)]
    items = _build_development_items(report)

    return PlayerDevelopmentReportResponse(
        snapshot_date=snapshot_ts.date(),
        total=len(items),
        items=items,
    )
