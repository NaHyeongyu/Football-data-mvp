from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from .calendar_update_shared import (
    LoadedWorkbook,
    PlayerDirectory,
    WORKBOOK_SHEETS,
    WorkbookFrames,
)


def infer_opponent_team(frame: pd.DataFrame) -> pd.DataFrame:
    if "opponent_team" in frame.columns:
        return frame.copy()
    if "home_team" not in frame.columns or "away_team" not in frame.columns:
        raise ValueError("Expected either opponent_team or home_team/away_team columns.")

    derived = frame.copy()
    team_counts = pd.concat([derived["home_team"], derived["away_team"]]).value_counts()
    candidates = team_counts[team_counts == len(derived)].index.tolist()
    own_team = candidates[0] if candidates else team_counts.index[0]
    derived["opponent_team"] = derived["away_team"].where(derived["home_team"] == own_team, derived["home_team"])
    return derived


def combine_split_gps_frames(match_gps: pd.DataFrame, training_gps: pd.DataFrame) -> pd.DataFrame:
    match_frame = match_gps.drop(columns=["match_gps_id"], errors="ignore").copy()
    match_frame["training_id"] = pd.NA

    training_frame = training_gps.drop(columns=["training_gps_id"], errors="ignore").copy()
    training_frame["match_id"] = pd.NA

    return pd.concat([match_frame, training_frame], ignore_index=True, sort=False)


def load_frames(workbook_path: Path) -> LoadedWorkbook:
    workbook = pd.ExcelFile(workbook_path)
    frames = pd.read_excel(workbook_path, sheet_name=list(WORKBOOK_SHEETS))
    source_columns = {sheet_name: frame.columns.tolist() for sheet_name, frame in frames.items()}

    # Support both the legacy combined GPS sheet and the normalized split-sheet layout.
    if "gps_data" in workbook.sheet_names:
        frames["gps_data"] = pd.read_excel(workbook_path, sheet_name="gps_data").drop(columns=["gps_id"], errors="ignore")
        source_columns["gps_data"] = pd.read_excel(workbook_path, sheet_name="gps_data", nrows=0).columns.tolist()
        return LoadedWorkbook(frames=frames, gps_sheet_mode="combined", source_columns=source_columns)

    if {"match_gps_data", "training_gps_data"}.issubset(workbook.sheet_names):
        match_gps = pd.read_excel(workbook_path, sheet_name="match_gps_data")
        training_gps = pd.read_excel(workbook_path, sheet_name="training_gps_data")
        frames["gps_data"] = combine_split_gps_frames(match_gps, training_gps)
        source_columns["match_gps_data"] = match_gps.columns.tolist()
        source_columns["training_gps_data"] = training_gps.columns.tolist()
        return LoadedWorkbook(frames=frames, gps_sheet_mode="split", source_columns=source_columns)

    raise ValueError("Expected either gps_data or both match_gps_data/training_gps_data sheets.")


def coerce_datetime_columns(frame: pd.DataFrame, columns: Sequence[str], *, errors: str = "raise") -> None:
    for column in columns:
        frame[column] = pd.to_datetime(frame[column], errors=errors)


def prepare_source_frames(frames: WorkbookFrames) -> None:
    frames["match_data"] = infer_opponent_team(frames["match_data"])

    coerce_datetime_columns(frames["player_info"], ("date_of_birth",))
    coerce_datetime_columns(frames["match_data"], ("match_date",))
    optional_match_player_columns = [
        column for column in ("match_date", "player_birth_day") if column in frames["match_player_data"].columns
    ]
    if optional_match_player_columns:
        coerce_datetime_columns(frames["match_player_data"], optional_match_player_columns)
    coerce_datetime_columns(frames["training_data"], ("training_date", "start_time", "end_time", "created_at", "updated_at"))
    coerce_datetime_columns(frames["injury_history"], ("injury_date", "expected_return_date", "created_at", "updated_at"))
    coerce_datetime_columns(frames["injury_history"], ("actual_return_date",), errors="coerce")
    optional_physical_test_columns = [column for column in ("test_date", "player_birth_day") if column in frames["physical_test_data"].columns]
    coerce_datetime_columns(frames["physical_test_data"], optional_physical_test_columns)
    optional_physical_data_columns = [column for column in ("created_at", "player_birth_day") if column in frames["physical_data"].columns]
    coerce_datetime_columns(frames["physical_data"], optional_physical_data_columns)
    coerce_datetime_columns(frames["evaluations"], ("evaluation_date",))
    coerce_datetime_columns(frames["counseling"], ("counseling_date",))

    frames["match_data"]["year"] = frames["match_data"]["match_date"].dt.year
    frames["training_data"]["year"] = frames["training_data"]["training_date"].dt.year
    frames["physical_test_data"]["year"] = frames["physical_test_data"]["test_date"].dt.year
    frames["physical_data"]["year"] = frames["physical_data"]["created_at"].dt.year


def build_player_directory(player_info: pd.DataFrame) -> PlayerDirectory:
    return PlayerDirectory(
        name_by_id=player_info.set_index("player_id")["name"].to_dict(),
        birth_date_by_id=player_info.set_index("player_id")["date_of_birth"].to_dict(),
        player_id_by_name=player_info.set_index("name")["player_id"].to_dict(),
    )


def populate_player_identifiers(frames: WorkbookFrames, directory: PlayerDirectory) -> None:
    if "player_id" not in frames["physical_test_data"].columns and "player_name" in frames["physical_test_data"].columns:
        frames["physical_test_data"]["player_id"] = frames["physical_test_data"]["player_name"].map(directory.player_id_by_name)
    if "player_id" not in frames["physical_data"].columns and "player_name" in frames["physical_data"].columns:
        frames["physical_data"]["player_id"] = frames["physical_data"]["player_name"].map(directory.player_id_by_name)


def build_year_date_index(frame: pd.DataFrame, date_column: str) -> dict[int, list[pd.Timestamp]]:
    with_years = frame.assign(_year=pd.to_datetime(frame[date_column], errors="coerce").dt.year)
    date_index: dict[int, list[pd.Timestamp]] = {}
    for year, group in with_years.groupby("_year", sort=True):
        if pd.isna(year):
            continue
        values = pd.to_datetime(group[date_column], errors="coerce").dropna().drop_duplicates().tolist()
        date_index[int(year)] = sorted(pd.Timestamp(value) for value in values)
    return date_index
