from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .shared import _contains_symptom_keywords


def _compute_physical_features(players: pd.DataFrame, physical_profiles: pd.DataFrame, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    base["body_fat_delta"] = np.nan
    base["muscle_mass_delta"] = np.nan
    base["weight_delta"] = np.nan
    base["physical_change_score"] = 0.0

    if physical_profiles.empty:
        return base

    profiles = physical_profiles.copy()
    profiles["created_at"] = pd.to_datetime(profiles["created_at"], errors="coerce")
    profiles = profiles[profiles["created_at"].notna() & (profiles["created_at"] <= snapshot_ts)].copy()
    profiles = profiles.sort_values(["player_id", "created_at"])
    profiles["previous_created_at"] = profiles.groupby("player_id")["created_at"].shift(1)
    profiles["previous_weight_kg"] = profiles.groupby("player_id")["weight_kg"].shift(1)
    profiles["previous_body_fat_percentage"] = profiles.groupby("player_id")["body_fat_percentage"].shift(1)
    profiles["previous_muscle_mass_kg"] = profiles.groupby("player_id")["muscle_mass_kg"].shift(1)

    latest = profiles.groupby("player_id").tail(1).copy()
    latest["days_between_profiles"] = (
        latest["created_at"] - latest["previous_created_at"]
    ).dt.days
    latest["body_fat_delta"] = latest["body_fat_percentage"] - latest["previous_body_fat_percentage"]
    latest["muscle_mass_delta"] = latest["muscle_mass_kg"] - latest["previous_muscle_mass_kg"]
    latest["weight_delta"] = latest["weight_kg"] - latest["previous_weight_kg"]

    recency_factor = np.clip(
        1 - np.maximum(latest["days_between_profiles"].fillna(999) - 90, 0) / 180,
        0.35,
        1.0,
    )
    body_fat_signal = np.clip((latest["body_fat_delta"].fillna(0) - 0.35) / 1.6, 0, 1)
    muscle_loss_signal = np.clip(((-latest["muscle_mass_delta"].fillna(0)) - 0.25) / 1.5, 0, 1)
    weight_swing_signal = np.clip((latest["weight_delta"].abs().fillna(0) - 1.5) / 4.0, 0, 1)
    muscle_gain_credit = np.clip((latest["muscle_mass_delta"].fillna(0) - 0.8) / 2.4, 0, 1) * 4.0

    # Recent unfavorable body-composition changes increase risk; muscle gain offsets part of that signal.
    latest["physical_change_score"] = np.maximum(
        0.0,
        np.round(
            (
                20.0
                * (
                    0.5 * body_fat_signal
                    + 0.35 * muscle_loss_signal
                    + 0.15 * weight_swing_signal
                )
                * recency_factor
            )
            - muscle_gain_credit,
            2,
        ),
    )

    base = base.merge(
        latest[
            [
                "player_id",
                "body_fat_delta",
                "muscle_mass_delta",
                "weight_delta",
                "physical_change_score",
            ]
        ],
        on="player_id",
        how="left",
        suffixes=("", "_new"),
    )
    for column in ["body_fat_delta", "muscle_mass_delta", "weight_delta", "physical_change_score"]:
        replacement = f"{column}_new"
        if replacement in base.columns:
            base[column] = base[replacement].combine_first(base[column])
            base = base.drop(columns=[replacement])
    base["physical_change_score"] = base["physical_change_score"].fillna(0.0)
    return base


def _compute_injury_features(players: pd.DataFrame, injuries: pd.DataFrame, snapshot_ts: pd.Timestamp) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    base["injuries_last_180d"] = 0
    base["injuries_last_365d"] = 0
    base["reinjury_flag"] = False
    base["days_since_return"] = np.nan
    base["open_rehab_flag"] = False
    base["injury_history_score"] = 0.0
    base["return_to_play_score"] = 0.0

    if injuries.empty:
        return base

    history = injuries.copy()
    for column in ["injury_date", "expected_return_date", "actual_return_date"]:
        history[column] = pd.to_datetime(history[column], errors="coerce")
    history = history[history["injury_date"].notna() & (history["injury_date"] <= snapshot_ts)].copy()
    if history.empty:
        return base

    history["days_since_injury"] = (snapshot_ts - history["injury_date"]).dt.days
    history["days_since_return"] = (snapshot_ts - history["actual_return_date"]).dt.days
    severity_points = history["severity_level"].map({"minor": 6, "moderate": 12, "severe": 18}).fillna(6)
    recency_weight = np.select(
        [
            history["days_since_injury"] <= 90,
            history["days_since_injury"] <= 180,
            history["days_since_injury"] <= 365,
        ],
        [1.0, 0.75, 0.45],
        default=0.0,
    )
    history["history_points"] = severity_points * recency_weight

    recent_180 = history.loc[history["days_since_injury"] <= 180].groupby("player_id").size()
    recent_365 = history.loc[history["days_since_injury"] <= 365].groupby("player_id").size()
    base["injuries_last_180d"] = base["player_id"].map(recent_180).fillna(0).astype(int)
    base["injuries_last_365d"] = base["player_id"].map(recent_365).fillna(0).astype(int)

    repeated_parts = (
        history.loc[history["days_since_injury"] <= 365]
        .groupby(["player_id", "injury_part"])
        .size()
        .reset_index(name="repeat_count")
    )
    reinjury = repeated_parts.groupby("player_id")["repeat_count"].max().fillna(0).ge(2)
    base["reinjury_flag"] = base["player_id"].map(reinjury).apply(
        lambda value: bool(value) if pd.notna(value) else False
    )

    latest_injury = history.sort_values(["player_id", "injury_date"]).groupby("player_id").tail(1).copy()
    latest_injury["open_rehab_flag"] = (
        latest_injury["injury_status"].eq("rehab")
        & (
            latest_injury["actual_return_date"].isna()
            | (latest_injury["actual_return_date"] > snapshot_ts)
        )
    )
    latest_injury["days_since_return_value"] = np.where(
        latest_injury["actual_return_date"].notna(),
        (snapshot_ts - latest_injury["actual_return_date"]).dt.days,
        np.nan,
    )

    history_base_points = history.groupby("player_id")["history_points"].sum().clip(upper=20)
    reinjury_bonus = base["reinjury_flag"].map({True: 6.0, False: 0.0})
    frequency_bonus = np.clip(base["injuries_last_180d"] - 1, 0, 3) * 2.0
    open_rehab_bonus_series = latest_injury.set_index("player_id")["open_rehab_flag"].map({True: 10.0, False: 0.0})
    base["injury_history_score"] = np.clip(
        base["player_id"].map(history_base_points).fillna(0.0)
        + reinjury_bonus
        + frequency_bonus
        + base["player_id"].map(open_rehab_bonus_series).fillna(0.0),
        0,
        30,
    ).round(2)

    base["open_rehab_flag"] = base["player_id"].map(
        latest_injury.set_index("player_id")["open_rehab_flag"]
    ).apply(lambda value: bool(value) if pd.notna(value) else False)
    base["days_since_return"] = base["player_id"].map(
        latest_injury.set_index("player_id")["days_since_return_value"]
    )

    days_since_return = pd.to_numeric(base["days_since_return"], errors="coerce")
    base["return_to_play_score"] = np.select(
        [
            base["open_rehab_flag"],
            days_since_return <= 7,
            days_since_return <= 14,
            days_since_return <= 30,
            days_since_return <= 60,
        ],
        [18.0, 16.0, 12.0, 8.0, 4.0],
        default=0.0,
    )
    return base


def _compute_symptom_features(
    players: pd.DataFrame,
    injuries: pd.DataFrame,
    counseling_notes: pd.DataFrame,
    snapshot_ts: pd.Timestamp,
) -> pd.DataFrame:
    base = players[["player_id"]].copy()
    base["recent_symptom_count_120d"] = 0
    base["recent_symptom_flag"] = False
    base["latest_symptom_days_ago"] = np.nan
    base["recent_medical_consultation_count_14d"] = 0
    base["symptom_score"] = 0.0

    if not injuries.empty:
        history = injuries.copy()
        for column in ["injury_date", "expected_return_date", "actual_return_date"]:
            history[column] = pd.to_datetime(history[column], errors="coerce")
        history = history[history["injury_date"].notna() & (history["injury_date"] <= snapshot_ts)].copy()
        if not history.empty:
            history["days_since_injury"] = (snapshot_ts - history["injury_date"]).dt.days
            history["symptom_flag"] = history.apply(
                lambda row: _contains_symptom_keywords(row.get("injury_type"), row.get("notes")),
                axis=1,
            )
            recent_symptoms = history.loc[
                history["symptom_flag"] & history["days_since_injury"].between(0, 120, inclusive="both")
            ].copy()
            if not recent_symptoms.empty:
                symptom_count = recent_symptoms.groupby("player_id").size()
                latest_days = recent_symptoms.groupby("player_id")["days_since_injury"].min()
                base["recent_symptom_count_120d"] = base["player_id"].map(symptom_count).fillna(0).astype(int)
                base["recent_symptom_flag"] = base["recent_symptom_count_120d"].gt(0)
                base["latest_symptom_days_ago"] = base["player_id"].map(latest_days)

    if not counseling_notes.empty:
        notes = counseling_notes.copy()
        notes["counseling_date"] = pd.to_datetime(notes["counseling_date"], errors="coerce")
        notes = notes[notes["counseling_date"].notna() & (notes["counseling_date"] <= snapshot_ts)].copy()
        notes = notes.loc[(snapshot_ts - notes["counseling_date"]).dt.days.between(0, 13, inclusive="both")]
        medical_notes = notes.loc[notes["topic"].eq("부상 관리")]
        if not medical_notes.empty:
            medical_count = medical_notes.groupby("player_id").size()
            base["recent_medical_consultation_count_14d"] = (
                base["player_id"].map(medical_count).fillna(0).astype(int)
            )

    symptom_days = pd.to_numeric(base["latest_symptom_days_ago"], errors="coerce")
    symptom_recency_signal = np.select(
        [
            symptom_days <= 14,
            symptom_days <= 30,
            symptom_days <= 60,
            symptom_days <= 120,
        ],
        [1.0, 0.82, 0.58, 0.35],
        default=0.0,
    )
    repeat_signal = np.clip(base["recent_symptom_count_120d"] - 1, 0, 2) / 2.0
    medical_followup_signal = np.where(
        base["recent_symptom_flag"],
        np.clip(base["recent_medical_consultation_count_14d"] / 2.0, 0, 1),
        0.0,
    )
    base["symptom_score"] = np.round(
        np.clip(
            0.72 * symptom_recency_signal
            + 0.18 * repeat_signal
            + 0.1 * medical_followup_signal,
            0,
            1,
        )
        * 15.0,
        2,
    )
    return base
