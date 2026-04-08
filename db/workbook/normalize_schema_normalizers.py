from __future__ import annotations

import pandas as pd

from .normalize_schema_loaders import infer_opponent_team
from .normalize_schema_shared import (
    COUNSELING_COLUMNS,
    EVALUATION_COLUMNS,
    INJURY_HISTORY_COLUMNS,
    LEGACY_MATCH_PLAYER_DROP_COLUMNS,
    LEGACY_MATCH_RENAME_MAP,
    LoadedWorkbook,
    MATCH_DATA_COLUMNS,
    MATCH_GPS_COLUMNS,
    MATCH_PLAYER_COLUMNS,
    PHYSICAL_DATA_COLUMNS,
    PHYSICAL_TEST_COLUMNS,
    PLAYER_INFO_COLUMNS,
    TRAINING_DATA_COLUMNS,
    TRAINING_GPS_COLUMNS,
    WorkbookFrames,
    build_year_scoped_ids,
    coerce_existing_datetime_columns,
    select_columns,
)


def normalize_player_info(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    coerce_existing_datetime_columns(normalized, ("date_of_birth", "joined_at", "updated_at"))
    return select_columns(normalized, PLAYER_INFO_COLUMNS)


def normalize_match_scores(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    if {"goals", "goals_for", "goals_against"}.issubset(normalized.columns):
        side = pd.Series(index=normalized.index, dtype="object")
        home_mask = (normalized["goals"] == normalized["goals_for"]) & (normalized["goals"] != normalized["goals_against"])
        away_mask = (normalized["goals"] == normalized["goals_against"]) & (normalized["goals"] != normalized["goals_for"])
        side.loc[home_mask] = "home"
        side.loc[away_mask] = "away"

        known = normalized.loc[side.notna()].copy()
        known["side"] = side.loc[side.notna()]
        stadium_pref = known.groupby("stadium")["side"].agg(lambda values: values.mode().iat[0]).to_dict() if not known.empty else {}
        opponent_pref = (
            known.groupby("opponent_team")["side"].agg(lambda values: values.mode().iat[0]).to_dict()
            if not known.empty
            else {}
        )
        side = side.fillna(normalized["stadium"].map(stadium_pref))
        side = side.fillna(normalized["opponent_team"].map(opponent_pref))
        side = side.fillna("home")

        original_goals_for = normalized["goals_for"].copy()
        original_goals_against = normalized["goals_against"].copy()
        original_possession_for = normalized["possession_for"].copy() if "possession_for" in normalized.columns else None
        original_possession_against = normalized["possession_against"].copy() if "possession_against" in normalized.columns else None

        normalized["goals_for"] = normalized["goals"]
        normalized["goals_against"] = original_goals_against.where(side == "home", original_goals_for)

        if original_possession_for is not None and original_possession_against is not None:
            normalized["possession_for"] = original_possession_for.where(side == "home", original_possession_against)
            normalized["possession_against"] = original_possession_against.where(side == "home", original_possession_for)

        normalized = normalized.drop(columns=["goals"])

    return normalized


def normalize_match_data(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = infer_opponent_team(frame)
    coerce_existing_datetime_columns(normalized, ("match_date",))
    normalized = normalized.rename(columns=LEGACY_MATCH_RENAME_MAP)
    normalized = normalize_match_scores(normalized)
    total_columns = [column for column in normalized.columns if str(column).startswith("total_")]
    normalized = normalized.drop(columns=total_columns, errors="ignore")
    normalized = normalized.drop(columns=["home_team", "away_team"], errors="ignore")
    return select_columns(normalized, MATCH_DATA_COLUMNS)


def normalize_match_player(
    frame: pd.DataFrame,
    match_date_lookup: dict[str, pd.Timestamp],
    name_to_player: dict[str, str],
) -> pd.DataFrame:
    normalized = frame.copy()
    if "player_id" not in normalized.columns and "player_name" in normalized.columns:
        normalized["player_id"] = normalized["player_name"].map(name_to_player)

    if "match_player_id" not in normalized.columns:
        date_source = normalized["match_date"] if "match_date" in normalized.columns else normalized["match_id"].map(match_date_lookup)
        normalized["match_player_id"] = build_year_scoped_ids(
            pd.DataFrame({"event_date": pd.to_datetime(date_source, errors="coerce")}),
            "event_date",
            "MPL",
            5,
        )

    normalized = normalized.drop(columns=list(LEGACY_MATCH_PLAYER_DROP_COLUMNS), errors="ignore")
    return select_columns(normalized, MATCH_PLAYER_COLUMNS)


def normalize_physical_test(frame: pd.DataFrame, name_to_player: dict[str, str]) -> pd.DataFrame:
    normalized = frame.copy()
    if "player_id" not in normalized.columns and "player_name" in normalized.columns:
        normalized["player_id"] = normalized["player_name"].map(name_to_player)
    coerce_existing_datetime_columns(normalized, ("test_date",))
    normalized["physical_test_id"] = build_year_scoped_ids(normalized, "test_date", "PTEST", 4)
    normalized = normalized.drop(columns=["player_name", "player_birth_day"], errors="ignore")
    return select_columns(normalized, PHYSICAL_TEST_COLUMNS)


def normalize_physical_data(frame: pd.DataFrame, name_to_player: dict[str, str]) -> pd.DataFrame:
    normalized = frame.copy()
    if "player_id" not in normalized.columns and "player_name" in normalized.columns:
        normalized["player_id"] = normalized["player_name"].map(name_to_player)
    coerce_existing_datetime_columns(normalized, ("created_at",))
    normalized["physical_data_id"] = build_year_scoped_ids(normalized, "created_at", "PDATA", 4)
    normalized = normalized.drop(columns=["player_name", "player_birth_day"], errors="ignore")
    return select_columns(normalized, PHYSICAL_DATA_COLUMNS)


def normalize_injury_history(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    coerce_existing_datetime_columns(
        normalized,
        ("injury_date", "expected_return_date", "actual_return_date", "created_at", "updated_at"),
    )
    return select_columns(normalized, INJURY_HISTORY_COLUMNS)


def normalize_training_data(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    coerce_existing_datetime_columns(normalized, ("training_date", "start_time", "end_time", "created_at", "updated_at"))
    return select_columns(normalized, TRAINING_DATA_COLUMNS)


def normalize_evaluations(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    coerce_existing_datetime_columns(normalized, ("evaluation_date",))
    normalized["evaluation_id"] = build_year_scoped_ids(normalized, "evaluation_date", "EVAL", 4)
    return select_columns(normalized, EVALUATION_COLUMNS)


def normalize_counseling(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    coerce_existing_datetime_columns(normalized, ("counseling_date",))
    normalized["counseling_id"] = build_year_scoped_ids(normalized, "counseling_date", "COUN", 4)
    return select_columns(normalized, COUNSELING_COLUMNS)


def normalize_gps_frame(
    frame: pd.DataFrame,
    *,
    date_lookup: dict[str, pd.Timestamp],
    source_id_column: str,
    target_id_column: str,
    prefix: str,
    drop_columns: tuple[str, ...],
    leading_columns: tuple[str, ...],
) -> pd.DataFrame:
    normalized = frame.copy()
    if "event_date" not in normalized.columns:
        normalized["event_date"] = normalized[source_id_column].map(date_lookup)
    normalized[target_id_column] = build_year_scoped_ids(normalized, "event_date", prefix, 5)
    normalized = normalized.drop(columns=[*drop_columns, "event_date"], errors="ignore")
    return select_columns(normalized, leading_columns)


def normalize_gps_sheets(
    frames: WorkbookFrames,
    *,
    gps_sheet_mode: str,
    match_date_lookup: dict[str, pd.Timestamp],
    training_date_lookup: dict[str, pd.Timestamp],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if gps_sheet_mode == "combined":
        gps = frames["gps_data"].copy()
        gps["event_date"] = gps["match_id"].map(match_date_lookup)
        gps["event_date"] = gps["event_date"].fillna(gps["training_id"].map(training_date_lookup))
        match_gps = gps[gps["match_id"].notna() & gps["training_id"].isna()].copy()
        training_gps = gps[gps["training_id"].notna() & gps["match_id"].isna()].copy()
    else:
        match_gps = frames["match_gps_data"].copy()
        training_gps = frames["training_gps_data"].copy()

    normalized_match_gps = normalize_gps_frame(
        match_gps,
        date_lookup=match_date_lookup,
        source_id_column="match_id",
        target_id_column="match_gps_id",
        prefix="MGPS",
        drop_columns=("gps_id", "training_id"),
        leading_columns=MATCH_GPS_COLUMNS,
    )
    normalized_training_gps = normalize_gps_frame(
        training_gps,
        date_lookup=training_date_lookup,
        source_id_column="training_id",
        target_id_column="training_gps_id",
        prefix="TGPS",
        drop_columns=("gps_id", "match_id"),
        leading_columns=TRAINING_GPS_COLUMNS,
    )
    return normalized_match_gps, normalized_training_gps


def normalize_workbook(loaded: LoadedWorkbook) -> WorkbookFrames:
    player_info = normalize_player_info(loaded.frames["player_info"])
    name_to_player = player_info.set_index("name")["player_id"].to_dict()

    match_data = normalize_match_data(loaded.frames["match_data"])
    match_date_lookup = match_data.set_index("match_id")["match_date"].to_dict()
    match_player = normalize_match_player(loaded.frames["match_player_data"], match_date_lookup, name_to_player)

    physical_test = normalize_physical_test(loaded.frames["physical_test_data"], name_to_player)
    physical_data = normalize_physical_data(loaded.frames["physical_data"], name_to_player)
    injury_history = normalize_injury_history(loaded.frames["injury_history"])
    training_data = normalize_training_data(loaded.frames["training_data"])
    training_date_lookup = training_data.set_index("training_id")["training_date"].to_dict()

    evaluations = normalize_evaluations(loaded.frames["evaluations"])
    counseling = normalize_counseling(loaded.frames["counseling"])
    match_gps, training_gps = normalize_gps_sheets(
        loaded.frames,
        gps_sheet_mode=loaded.gps_sheet_mode,
        match_date_lookup=match_date_lookup,
        training_date_lookup=training_date_lookup,
    )

    return {
        "player_info": player_info,
        "physical_test_data": physical_test,
        "physical_data": physical_data,
        "injury_history": injury_history,
        "match_data": match_data,
        "match_player_data": match_player,
        "training_data": training_data,
        "match_gps_data": match_gps,
        "training_gps_data": training_gps,
        "evaluations": evaluations,
        "counseling": counseling,
    }
