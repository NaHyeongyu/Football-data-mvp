from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DB_DIR = Path(__file__).resolve().parents[1]

DEFAULT_WORKBOOK_PATH = ROOT_DIR / "virtual_players_2008_complete_with_all_staff_data.xlsx"
DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:5432/football_data",
)

WORKBOOK_SHEETS = (
    "player_info",
    "physical_test_data",
    "physical_data",
    "injury_history",
    "match_data",
    "match_player_data",
    "training_data",
    "match_gps_data",
    "training_gps_data",
    "evaluations",
    "counseling",
)

DATE_ONLY_COLUMNS = {
    "player_info": ("date_of_birth",),
    "physical_test_data": ("test_date",),
    "injury_history": ("injury_date", "expected_return_date", "actual_return_date"),
    "match_data": ("match_date",),
    "training_data": ("training_date",),
    "evaluations": ("evaluation_date",),
    "counseling": ("counseling_date",),
}

DATETIME_COLUMNS = {
    "player_info": ("joined_at", "updated_at"),
    "physical_data": ("created_at",),
    "injury_history": ("created_at", "updated_at"),
    "training_data": ("start_time", "end_time", "created_at", "updated_at"),
}

MATCH_METADATA_COLUMNS = (
    "match_id",
    "match_date",
    "match_type",
    "stadium",
    "opponent_team",
    "goals_for",
    "goals_against",
    "possession_for",
    "possession_against",
)

PLAYER_COLUMNS = (
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

PHYSICAL_TEST_COLUMNS = (
    "physical_test_id",
    "player_id",
    "test_date",
    "sprint_10m",
    "sprint_30m",
    "sprint_50m",
    "sprint_100m",
    "vertical_jump_cm",
    "agility_t_test_sec",
    "agility_505_sec",
    "agility_shuttle_run_sec",
)

PHYSICAL_PROFILE_COLUMNS = (
    "physical_data_id",
    "player_id",
    "height_cm",
    "weight_kg",
    "body_fat_percentage",
    "bmi",
    "muscle_mass_kg",
    "created_at",
)

INJURY_COLUMNS = (
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

MATCH_COLUMNS = (
    "match_id",
    "match_date",
    "match_type",
    "stadium_id",
    "opponent_team_id",
    "goals_for",
    "goals_against",
    "possession_for",
    "possession_against",
)

PLAYER_MATCH_COLUMNS = (
    "match_player_id",
    "match_id",
    "player_id",
    "position",
    "minutes_played",
    "start_position",
    "substitute_in",
    "substitute_out",
    "goals",
    "goals_type",
    "assists",
    "shots",
    "shots_on_target",
    "shots_off_target",
    "blocked_shots",
    "shots_inside_pa",
    "shots_outside_pa",
    "offsides",
    "freekicks",
    "corners",
    "throw_ins",
    "take_ons_attempted",
    "take_ons_succeeded",
    "take_ons_failed",
    "shooting_accuracy",
    "take_on_success_rate",
    "passes_attempted",
    "passes_completed",
    "passes_failed",
    "pass_accuracy",
    "key_passes",
    "crosses_attempted",
    "crosses_succeeded",
    "crosses_failed",
    "cross_accuracy",
    "forward_passes_attempted",
    "forward_passes_succeeded",
    "forward_passes_failed",
    "sideways_passes_attempted",
    "sideways_passes_succeeded",
    "sideways_passes_failed",
    "backward_passes_attempted",
    "backward_passes_succeeded",
    "backward_passes_failed",
    "short_passes_attempted",
    "short_passes_succeeded",
    "short_passes_failed",
    "medium_passes_attempted",
    "medium_passes_succeeded",
    "medium_passes_failed",
    "long_passes_attempted",
    "long_passes_succeeded",
    "long_passes_failed",
    "passes_in_defensive_third_attempted",
    "passes_in_defensive_third_succeeded",
    "passes_in_defensive_third_failed",
    "passes_in_middle_third_attempted",
    "passes_in_middle_third_succeeded",
    "passes_in_middle_third_failed",
    "passes_in_final_third_attempted",
    "passes_in_final_third_succeeded",
    "passes_in_final_third_failed",
    "control_under_pressure",
    "tackles_attempted",
    "tackles_succeeded",
    "tackles_failed",
    "interceptions",
    "recoveries",
    "clearances",
    "interventions",
    "blocks",
    "mistakes",
    "fouls_committed",
    "fouls_won",
    "yellow_cards",
    "red_cards",
    "aerial_duels_total",
    "aerial_duels_won",
    "aerial_duels_lost",
    "ground_duels_total",
    "ground_duels_won",
    "ground_duels_lost",
    "goalkeeper_player_id",
    "goals_conceded",
    "shots_on_target_faced",
    "saves",
    "save_rate",
    "catches",
    "punches",
    "goal_kicks_attempted",
    "goal_kicks_succeeded",
    "goal_kicks_failed",
    "aerial_clearances_attempted",
    "aerial_clearances_succeeded",
    "aerial_clearances_failed",
)

TRAINING_COLUMNS = (
    "training_id",
    "training_date",
    "training_type",
    "training_detail",
    "training_focus",
    "session_name",
    "start_time",
    "end_time",
    "intensity_level",
    "coach_id",
    "training_location_id",
    "notes",
    "created_at",
    "updated_at",
)

MATCH_GPS_COLUMNS = (
    "match_gps_id",
    "match_id",
    "player_id",
    "total_distance",
    "play_time_min",
    "avg_speed",
    "max_speed",
    "distance_0_15_min",
    "distance_15_30_min",
    "distance_30_45_min",
    "distance_45_60_min",
    "distance_60_75_min",
    "distance_75_90_min",
    "sprint_count",
    "sprint_distance",
    "distance_speed_0_5",
    "distance_speed_5_10",
    "distance_speed_10_15",
    "distance_speed_15_20",
    "distance_speed_20_25",
    "distance_speed_25_plus",
    "cod_count",
    "accel_count",
    "decel_count",
    "hi_accel_count",
    "hi_decel_count",
)

TRAINING_GPS_COLUMNS = (
    "training_gps_id",
    "training_id",
    "player_id",
    "total_distance",
    "play_time_min",
    "avg_speed",
    "max_speed",
    "distance_0_15_min",
    "distance_15_30_min",
    "distance_30_45_min",
    "distance_45_60_min",
    "distance_60_75_min",
    "distance_75_90_min",
    "sprint_count",
    "sprint_distance",
    "distance_speed_0_5",
    "distance_speed_5_10",
    "distance_speed_10_15",
    "distance_speed_15_20",
    "distance_speed_20_25",
    "distance_speed_25_plus",
    "cod_count",
    "accel_count",
    "decel_count",
    "hi_accel_count",
    "hi_decel_count",
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

PLAYER_MATCH_RENAME_MAP = {
    "crosses_success": "crosses_succeeded",
    "tackles_success": "tackles_succeeded",
    "goalkeeper_id": "goalkeeper_player_id",
}

GPS_RENAME_MAP = {
    "distance": "total_distance",
    "avg_speed": "avg_speed",
    "max_speed": "max_speed",
    "0~15min_distance": "distance_0_15_min",
    "15~30min_distance": "distance_15_30_min",
    "30~45min_distance": "distance_30_45_min",
    "45~60min_distance": "distance_45_60_min",
    "60~75min_distance": "distance_60_75_min",
    "75~90min_distance": "distance_75_90_min",
    "sprint_distance": "sprint_distance",
    "distance_speed_0_5km": "distance_speed_0_5",
    "distance_speed_5_10km": "distance_speed_5_10",
    "distance_speed_10_15km": "distance_speed_10_15",
    "distance_speed_15_20km": "distance_speed_15_20",
    "distance_speed_20_25km": "distance_speed_20_25",
    "distance_speed_25<": "distance_speed_25_plus",
}

MATCH_GPS_SKIP_COLUMNS = frozenset({"match_gps_id", "match_id", "player_id"})
TRAINING_GPS_SKIP_COLUMNS = frozenset({"training_gps_id", "training_id", "player_id"})
PHYSICAL_PROFILE_RENAME_MAP = {"height": "height_cm", "weight": "weight_kg", "muscle_mass": "muscle_mass_kg"}

TRUNCATE_SQL = """
TRUNCATE TABLE
    football.counseling_notes,
    football.evaluations,
    football.training_gps_stats,
    football.match_gps_stats,
    football.player_match_stats,
    football.match_team_stats,
    football.trainings,
    football.matches,
    football.injuries,
    football.physical_profiles,
    football.physical_tests,
    football.players,
    football.training_locations,
    football.coaches,
    football.opponent_teams,
    football.stadiums
CASCADE;
"""

INIT_SQL_FILES = (
    DB_DIR / "init" / "001_schema.sql",
    DB_DIR / "init" / "003_gps_column_naming.sql",
    DB_DIR / "init" / "002_views.sql",
    DB_DIR / "init" / "004_evaluation_trend.sql",
    DB_DIR / "init" / "005_assistant_rag.sql",
)

COUNT_QUERIES = {
    "players": "SELECT COUNT(*) FROM football.players",
    "matches": "SELECT COUNT(*) FROM football.matches",
    "player_match_stats": "SELECT COUNT(*) FROM football.player_match_stats",
    "match_gps_stats": "SELECT COUNT(*) FROM football.match_gps_stats",
    "trainings": "SELECT COUNT(*) FROM football.trainings",
    "training_gps_stats": "SELECT COUNT(*) FROM football.training_gps_stats",
    "injuries": "SELECT COUNT(*) FROM football.injuries",
}


@dataclass(frozen=True)
class LookupSpec:
    sheet_name: str
    source_column: str
    prefix: str
    table_name: str
    table_columns: tuple[str, str]


@dataclass(frozen=True)
class LookupLoad:
    table_name: str
    columns: tuple[str, str]
    mapping: dict[str, str]
    rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class TableCopySpec:
    table_name: str
    frame_name: str
    columns: tuple[str, ...] | None = None


@dataclass(frozen=True)
class PreparedWorkbook:
    lookup_loads: dict[str, LookupLoad]
    table_frames: dict[str, pd.DataFrame]


LOOKUP_SPECS = (
    LookupSpec("match_data", "stadium", "STADIUM", "stadiums", ("stadium_id", "stadium_name")),
    LookupSpec("match_data", "opponent_team", "OPPONENT", "opponent_teams", ("opponent_team_id", "opponent_team_name")),
    LookupSpec("training_data", "coach_name", "COACH", "coaches", ("coach_id", "coach_name")),
    LookupSpec("training_data", "location", "TLOC", "training_locations", ("training_location_id", "location_name")),
)

TABLE_COPY_SPECS = (
    TableCopySpec("players", "players", PLAYER_COLUMNS),
    TableCopySpec("physical_tests", "physical_tests", PHYSICAL_TEST_COLUMNS),
    TableCopySpec("physical_profiles", "physical_profiles", PHYSICAL_PROFILE_COLUMNS),
    TableCopySpec("injuries", "injuries", INJURY_COLUMNS),
    TableCopySpec("matches", "matches", MATCH_COLUMNS),
    TableCopySpec("match_team_stats", "match_team_stats"),
    TableCopySpec("trainings", "trainings", TRAINING_COLUMNS),
    TableCopySpec("player_match_stats", "player_match_stats", PLAYER_MATCH_COLUMNS),
    TableCopySpec("match_gps_stats", "match_gps_stats", MATCH_GPS_COLUMNS),
    TableCopySpec("training_gps_stats", "training_gps_stats", TRAINING_GPS_COLUMNS),
    TableCopySpec("evaluations", "evaluations", EVALUATION_COLUMNS),
    TableCopySpec("counseling_notes", "counseling_notes", COUNSELING_COLUMNS),
)
