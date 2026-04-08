from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from db.workbook.workbook_enums import ENUM_BINDINGS, canonicalize_enum_value

from .load_virtual_players_workbook_shared import (
    COUNSELING_COLUMNS,
    DATE_ONLY_COLUMNS,
    DATETIME_COLUMNS,
    EVALUATION_COLUMNS,
    GPS_RENAME_MAP,
    INJURY_COLUMNS,
    LOOKUP_SPECS,
    LookupLoad,
    LookupSpec,
    MATCH_COLUMNS,
    MATCH_GPS_COLUMNS,
    MATCH_GPS_SKIP_COLUMNS,
    MATCH_METADATA_COLUMNS,
    PHYSICAL_PROFILE_COLUMNS,
    PHYSICAL_PROFILE_RENAME_MAP,
    PHYSICAL_TEST_COLUMNS,
    PLAYER_COLUMNS,
    PLAYER_MATCH_COLUMNS,
    PLAYER_MATCH_RENAME_MAP,
    PreparedWorkbook,
    TRAINING_COLUMNS,
    TRAINING_GPS_COLUMNS,
    TRAINING_GPS_SKIP_COLUMNS,
    WORKBOOK_SHEETS,
)


def load_frames(workbook_path: Path) -> dict[str, pd.DataFrame]:
    frames = pd.read_excel(workbook_path, sheet_name=list(WORKBOOK_SHEETS))
    normalize_frames(frames)
    return frames


def normalize_frames(frames: dict[str, pd.DataFrame]) -> None:
    convert_temporal_columns(frames)
    canonicalize_enums(frames)


def convert_temporal_columns(frames: dict[str, pd.DataFrame]) -> None:
    for sheet_name, columns in DATE_ONLY_COLUMNS.items():
        frame = frames[sheet_name]
        for column in columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce").dt.date
    for sheet_name, columns in DATETIME_COLUMNS.items():
        frame = frames[sheet_name]
        for column in columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")


def canonicalize_enums(frames: dict[str, pd.DataFrame]) -> None:
    for binding in ENUM_BINDINGS:
        frame = frames.get(binding.sheet_name)
        if frame is None or binding.column_name not in frame.columns:
            continue
        frame[binding.column_name] = frame[binding.column_name].map(
            lambda raw: canonicalize_enum_value(binding.enum_key, raw)
        )


def build_lookup_loads(frames: dict[str, pd.DataFrame]) -> dict[str, LookupLoad]:
    return {
        spec.table_name: build_lookup_load(frames[spec.sheet_name][spec.source_column], spec)
        for spec in LOOKUP_SPECS
    }


def build_lookup_load(values: pd.Series, spec: LookupSpec) -> LookupLoad:
    unique_values = sorted({str(value).strip() for value in values.dropna().tolist() if str(value).strip()})
    mapping: dict[str, str] = {}
    rows: list[tuple[str, str]] = []
    for index, value in enumerate(unique_values, start=1):
        identifier = f"{spec.prefix}_{index:03d}"
        mapping[value] = identifier
        rows.append((identifier, value))
    return LookupLoad(
        table_name=spec.table_name,
        columns=spec.table_columns,
        mapping=mapping,
        rows=tuple(rows),
    )


def prepare_workbook(frames: dict[str, pd.DataFrame]) -> PreparedWorkbook:
    lookup_loads = build_lookup_loads(frames)
    table_frames: dict[str, pd.DataFrame] = {}
    table_frames.update(prepare_player_frames(frames))
    table_frames.update(prepare_match_frames(frames, lookup_loads))
    table_frames.update(prepare_training_frames(frames, lookup_loads))
    return PreparedWorkbook(lookup_loads=lookup_loads, table_frames=table_frames)


def prepare_player_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    injuries = frames["injury_history"].copy()
    # Workbook booleans come in mixed localized forms, so normalize once before COPY.
    injuries["surgery_required"] = injuries["surgery_required"].map(
        lambda raw: canonicalize_enum_value("boolean_flag", raw) == "true"
    )
    return {
        "players": select_columns(frames["player_info"], PLAYER_COLUMNS),
        "physical_tests": select_columns(frames["physical_test_data"], PHYSICAL_TEST_COLUMNS),
        "physical_profiles": select_columns(
            frames["physical_data"].rename(columns=PHYSICAL_PROFILE_RENAME_MAP),
            PHYSICAL_PROFILE_COLUMNS,
        ),
        "injuries": select_columns(injuries, INJURY_COLUMNS),
        "evaluations": prepare_evaluations_frame(frames["evaluations"]),
        "counseling_notes": select_columns(frames["counseling"], COUNSELING_COLUMNS),
    }


def prepare_evaluations_frame(frame: pd.DataFrame) -> pd.DataFrame:
    evaluations = select_columns(frame, EVALUATION_COLUMNS).copy()
    evaluation_ts = pd.to_datetime(evaluations["evaluation_date"], errors="coerce")
    evaluations = evaluations.assign(
        evaluation_ts=evaluation_ts,
        evaluation_month=evaluation_ts.dt.to_period("M").astype(str),
    ).sort_values(["player_id", "evaluation_ts", "evaluation_id"])

    # The downstream trend view expects a single evaluation snapshot per player-month.
    evaluations = evaluations.drop_duplicates(
        subset=["player_id", "evaluation_month"],
        keep="last",
    ).copy()

    return evaluations.loc[:, list(EVALUATION_COLUMNS)].reset_index(drop=True)


def prepare_match_frames(
    frames: dict[str, pd.DataFrame],
    lookup_loads: dict[str, LookupLoad],
) -> dict[str, pd.DataFrame]:
    raw_matches = frames["match_data"].copy()
    matches = raw_matches.assign(
        stadium_id=raw_matches["stadium"].map(lookup_loads["stadiums"].mapping),
        opponent_team_id=raw_matches["opponent_team"].map(lookup_loads["opponent_teams"].mapping),
    )
    return {
        "matches": select_columns(matches, MATCH_COLUMNS),
        "match_team_stats": build_match_team_stats_frame(raw_matches),
        "player_match_stats": select_columns(
            frames["match_player_data"].rename(columns=PLAYER_MATCH_RENAME_MAP),
            PLAYER_MATCH_COLUMNS,
        ),
        "match_gps_stats": prepare_gps_frame(
            frames["match_gps_data"],
            MATCH_GPS_SKIP_COLUMNS,
            MATCH_GPS_COLUMNS,
        ),
    }


def prepare_training_frames(
    frames: dict[str, pd.DataFrame],
    lookup_loads: dict[str, LookupLoad],
) -> dict[str, pd.DataFrame]:
    raw_trainings = frames["training_data"].copy()
    trainings = raw_trainings.assign(
        coach_id=raw_trainings["coach_name"].map(lookup_loads["coaches"].mapping),
        training_location_id=raw_trainings["location"].map(lookup_loads["training_locations"].mapping),
    )
    return {
        "trainings": select_columns(trainings, TRAINING_COLUMNS),
        "training_gps_stats": prepare_gps_frame(
            frames["training_gps_data"],
            TRAINING_GPS_SKIP_COLUMNS,
            TRAINING_GPS_COLUMNS,
        ),
    }


def build_match_team_stats_frame(match_frame: pd.DataFrame) -> pd.DataFrame:
    team_stats = match_frame.drop(columns=[*MATCH_METADATA_COLUMNS, "phase"], errors="ignore").copy()
    team_stats.insert(0, "match_id", match_frame["match_id"].to_numpy(copy=False))
    return team_stats


def select_columns(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    return frame.loc[:, list(columns)].copy()


def prepare_gps_frame(
    frame: pd.DataFrame,
    skip_columns: frozenset[str],
    columns: Sequence[str],
) -> pd.DataFrame:
    renamed = frame.rename(columns=GPS_RENAME_MAP).copy()
    clipped = clip_nonnegative_metrics(renamed, skip_columns)
    return select_columns(clipped, columns)


def clip_nonnegative_metrics(frame: pd.DataFrame, skip_columns: set[str] | frozenset[str]) -> pd.DataFrame:
    clipped = frame.copy()
    metric_columns = [column for column in clipped.columns if column not in skip_columns]
    for column in metric_columns:
        numeric = pd.to_numeric(clipped[column], errors="coerce")
        if numeric.notna().any():
            clipped[column] = numeric.clip(lower=0)
    return clipped
