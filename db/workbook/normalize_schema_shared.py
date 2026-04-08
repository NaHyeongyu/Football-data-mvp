from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_WORKBOOK_PATH = ROOT_DIR / "virtual_players_2008_complete_with_all_staff_data.xlsx"

BASE_SHEETS = (
    "player_info",
    "match_data",
    "match_player_data",
    "physical_test_data",
    "physical_data",
    "injury_history",
    "training_data",
    "evaluations",
    "counseling",
)

PLAYER_INFO_COLUMNS = (
    "player_id",
    "name",
    "date_of_birth",
    "jersey_number",
    "primary_position",
    "secondary_position",
    "foot",
    "nationality",
    "status",
    "profile_image_url",
    "joined_at",
    "previous_team",
    "updated_at",
)

MATCH_DATA_COLUMNS = (
    "match_id",
    "match_date",
    "match_type",
    "phase",
    "stadium",
    "opponent_team",
    "goals_for",
    "goals_against",
    "possession_for",
    "possession_against",
)

MATCH_PLAYER_COLUMNS = (
    "match_player_id",
    "match_id",
    "player_id",
    "position",
    "minutes_played",
    "start_position",
    "substitute_in",
    "substitute_out",
)

PHYSICAL_TEST_COLUMNS = (
    "physical_test_id",
    "player_id",
    "test_date",
)

PHYSICAL_DATA_COLUMNS = (
    "physical_data_id",
    "player_id",
    "height",
    "weight",
    "body_fat_percentage",
    "bmi",
    "muscle_mass",
    "created_at",
)

INJURY_HISTORY_COLUMNS = (
    "injury_id",
    "player_id",
    "injury_date",
    "injury_type",
    "injury_part",
    "severity_level",
    "status",
    "expected_return_date",
    "actual_return_date",
    "surgery_required",
    "injury_mechanism",
    "occurred_during",
    "notes",
    "created_at",
    "updated_at",
)

TRAINING_DATA_COLUMNS = (
    "training_id",
    "training_date",
    "training_type",
    "training_detail",
    "training_focus",
    "session_name",
    "start_time",
    "end_time",
    "intensity_level",
    "coach_name",
    "location",
    "notes",
    "created_at",
    "updated_at",
)

EVALUATION_COLUMNS = (
    "evaluation_id",
    "player_id",
    "evaluation_date",
    "technical",
    "tactical",
    "physical",
    "mental",
    "coach_comment",
)

COUNSELING_COLUMNS = (
    "counseling_id",
    "player_id",
    "counseling_date",
    "topic",
    "summary",
)

MATCH_GPS_COLUMNS = (
    "match_gps_id",
    "match_id",
    "player_id",
)

TRAINING_GPS_COLUMNS = (
    "training_gps_id",
    "training_id",
    "player_id",
)

LEGACY_MATCH_RENAME_MAP = {
    "score_home": "goals_for",
    "score_away": "goals_against",
    "possession_home": "possession_for",
    "possession_away": "possession_against",
}

LEGACY_MATCH_PLAYER_DROP_COLUMNS = (
    "match_date",
    "match_type",
    "phase",
    "stadium",
    "opponent_team",
    "goals_for",
    "goals_against",
    "possession_for",
    "possession_against",
    "score_home",
    "score_away",
    "possession_home",
    "possession_away",
    "player_name",
    "player_birth_day",
)

DESIRED_SHEET_ORDER = (
    "player_info",
    "physical_test_data",
    "physical_data",
    "injury_history",
    "README",
    "enum_reference",
    "match_data",
    "match_player_data",
    "training_data",
    "match_gps_data",
    "training_gps_data",
    "evaluations",
    "counseling",
)

REPLACED_SHEETS = (
    "player_info",
    "physical_test_data",
    "physical_data",
    "injury_history",
    "match_data",
    "match_player_data",
    "training_data",
    "gps_data",
    "match_gps_data",
    "training_gps_data",
    "evaluations",
    "counseling",
)

DATE_ONLY_COLUMNS = {
    "player_info": {"date_of_birth"},
    "match_data": {"match_date"},
    "physical_test_data": {"test_date"},
    "injury_history": {"injury_date", "expected_return_date", "actual_return_date"},
    "training_data": {"training_date"},
    "evaluations": {"evaluation_date"},
    "counseling": {"counseling_date"},
}

DATETIME_COLUMNS = {
    "player_info": {"joined_at", "updated_at"},
    "physical_data": {"created_at"},
    "injury_history": {"created_at", "updated_at"},
    "training_data": {"start_time", "end_time", "created_at", "updated_at"},
}


WorkbookFrames = dict[str, pd.DataFrame]


@dataclass(frozen=True)
class LoadedWorkbook:
    frames: WorkbookFrames
    readme: pd.DataFrame | None
    gps_sheet_mode: str


def build_year_scoped_ids(frame: pd.DataFrame, date_column: str, prefix: str, width: int) -> list[str]:
    counters: dict[int, int] = defaultdict(int)
    values: list[str] = []
    years = pd.to_datetime(frame[date_column], errors="coerce").dt.year.tolist()
    for year in years:
        if pd.isna(year):
            raise ValueError(f"Cannot derive year for {prefix} from column {date_column}")
        year_int = int(year)
        counters[year_int] += 1
        values.append(f"{prefix}-{year_int}-{counters[year_int]:0{width}d}")
    return values


def normalize_date(value: Any) -> date | None:
    if pd.isna(value):
        return None
    return pd.Timestamp(value).to_pydatetime().date()


def normalize_datetime(value: Any) -> datetime | None:
    if pd.isna(value):
        return None
    return pd.Timestamp(value).to_pydatetime().replace(second=0, microsecond=0)


def select_columns(frame: pd.DataFrame, leading_columns: tuple[str, ...]) -> pd.DataFrame:
    ordered = [column for column in leading_columns if column in frame.columns]
    remaining = [column for column in frame.columns if column not in ordered]
    return frame.loc[:, ordered + remaining].copy()


def coerce_existing_datetime_columns(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
