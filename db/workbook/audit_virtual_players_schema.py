from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db.workbook.workbook_enums import ENUM_BINDINGS, ENUM_DEFINITIONS, canonicalize_enum_value
WORKBOOK_PATH = ROOT_DIR / "virtual_players_2008_complete_with_all_staff_data.xlsx"


def assert_unique(frame: pd.DataFrame, columns: list[str], label: str) -> list[str]:
    issues: list[str] = []
    if frame[columns].isna().any().any():
        issues.append(f"{label}: null found in {columns}")
    duplicate_count = int(frame.duplicated(columns).sum())
    if duplicate_count:
        issues.append(f"{label}: duplicated key rows={duplicate_count} for {columns}")
    return issues


def main() -> None:
    path = WORKBOOK_PATH
    sheets = {
        "player_info": pd.read_excel(path, sheet_name="player_info"),
        "physical_test_data": pd.read_excel(path, sheet_name="physical_test_data"),
        "physical_data": pd.read_excel(path, sheet_name="physical_data"),
        "injury_history": pd.read_excel(path, sheet_name="injury_history"),
        "match_data": pd.read_excel(path, sheet_name="match_data"),
        "match_player_data": pd.read_excel(path, sheet_name="match_player_data"),
        "training_data": pd.read_excel(path, sheet_name="training_data"),
        "match_gps_data": pd.read_excel(path, sheet_name="match_gps_data"),
        "training_gps_data": pd.read_excel(path, sheet_name="training_gps_data"),
        "evaluations": pd.read_excel(path, sheet_name="evaluations"),
        "counseling": pd.read_excel(path, sheet_name="counseling"),
    }

    issues: list[str] = []

    issues += assert_unique(sheets["player_info"], ["player_id"], "player_info")
    issues += assert_unique(sheets["physical_test_data"], ["physical_test_id"], "physical_test_data")
    issues += assert_unique(sheets["physical_data"], ["physical_data_id"], "physical_data")
    issues += assert_unique(sheets["injury_history"], ["injury_id"], "injury_history")
    issues += assert_unique(sheets["match_data"], ["match_id"], "match_data")
    issues += assert_unique(sheets["match_player_data"], ["match_player_id"], "match_player_data")
    issues += assert_unique(sheets["training_data"], ["training_id"], "training_data")
    issues += assert_unique(sheets["match_gps_data"], ["match_gps_id"], "match_gps_data")
    issues += assert_unique(sheets["training_gps_data"], ["training_gps_id"], "training_gps_data")
    issues += assert_unique(sheets["evaluations"], ["evaluation_id"], "evaluations")
    issues += assert_unique(sheets["counseling"], ["counseling_id"], "counseling")

    issues += assert_unique(sheets["match_player_data"], ["match_id", "player_id"], "match_player natural key")
    issues += assert_unique(sheets["physical_test_data"], ["player_id", "test_date"], "physical_test natural key")
    issues += assert_unique(sheets["physical_data"], ["player_id", "created_at"], "physical_data natural key")
    issues += assert_unique(sheets["match_gps_data"], ["match_id", "player_id"], "match_gps natural key")
    issues += assert_unique(sheets["training_gps_data"], ["training_id", "player_id"], "training_gps natural key")
    issues += assert_unique(sheets["evaluations"], ["player_id", "evaluation_date"], "evaluations natural key")
    issues += assert_unique(sheets["counseling"], ["player_id", "counseling_date"], "counseling natural key")

    players = set(sheets["player_info"]["player_id"].dropna())
    matches = set(sheets["match_data"]["match_id"].dropna())
    trainings = set(sheets["training_data"]["training_id"].dropna())

    for sheet_name, column in [
        ("physical_test_data", "player_id"),
        ("physical_data", "player_id"),
        ("injury_history", "player_id"),
        ("match_player_data", "player_id"),
        ("match_gps_data", "player_id"),
        ("training_gps_data", "player_id"),
        ("evaluations", "player_id"),
        ("counseling", "player_id"),
    ]:
        missing = sorted(set(sheets[sheet_name][column].dropna()) - players)
        if missing:
            issues.append(f"{sheet_name}: unknown player_id values {missing[:10]}")

    missing_match_ids = sorted(set(sheets["match_player_data"]["match_id"].dropna()) - matches)
    if missing_match_ids:
        issues.append(f"match_player_data: unknown match_id values {missing_match_ids[:10]}")

    match_gps = sheets["match_gps_data"]
    training_gps = sheets["training_gps_data"]
    missing_gps_matches = sorted(set(match_gps["match_id"].dropna()) - matches)
    missing_gps_trainings = sorted(set(training_gps["training_id"].dropna()) - trainings)
    if missing_gps_matches:
        issues.append(f"match_gps_data: unknown match_id values {missing_gps_matches[:10]}")
    if missing_gps_trainings:
        issues.append(f"training_gps_data: unknown training_id values {missing_gps_trainings[:10]}")

    match_headers = [
        "match_date",
        "match_type",
        "phase",
        "stadium",
        "opponent_team",
        "goals_for",
        "goals_against",
        "possession_for",
        "possession_against",
    ]
    repeated_in_match_player = [column for column in match_headers if column in sheets["match_player_data"].columns]
    if repeated_in_match_player:
        issues.append(
            "match_player_data: match-level header columns are duplicated "
            f"{repeated_in_match_player}"
        )

    player_descriptors = ["player_name", "player_birth_day"]
    for sheet_name in ["physical_test_data", "physical_data", "match_player_data"]:
        repeated = [column for column in player_descriptors if column in sheets[sheet_name].columns]
        if repeated:
            issues.append(f"{sheet_name}: player descriptor columns duplicated {repeated}")

    total_columns = [column for column in sheets["match_data"].columns if str(column).startswith("total_")]
    if total_columns:
        issues.append(f"match_data: derived total columns present {total_columns}")

    legacy_match_columns = ["score_home", "score_away", "possession_home", "possession_away"]
    legacy_leftovers = [column for column in legacy_match_columns if column in sheets["match_data"].columns]
    if legacy_leftovers:
        issues.append(f"match_data: legacy home/away columns present {legacy_leftovers}")

    if "goals" in sheets["match_data"].columns:
        issues.append("match_data: duplicate team goals column 'goals' should be removed")

    if "enum_reference" not in pd.ExcelFile(path).sheet_names:
        issues.append("enum_reference: sheet missing")

    for binding in ENUM_BINDINGS:
        sheet = sheets.get(binding.sheet_name)
        if sheet is None or binding.column_name not in sheet.columns:
            continue
        invalid_values: list[str] = []
        for raw_value in sheet[binding.column_name].dropna().tolist():
            try:
                canonical = canonicalize_enum_value(binding.enum_key, raw_value)
            except ValueError:
                invalid_values.append(str(raw_value))
                continue
            if canonical not in ENUM_DEFINITIONS[binding.enum_key]:
                invalid_values.append(str(raw_value))
        if invalid_values:
            issues.append(
                f"{binding.sheet_name}.{binding.column_name}: invalid enum values "
                f"{sorted(set(invalid_values))[:10]}"
            )

    print("Normalization audit")
    print(f"Workbook: {path}")
    print(f"Issue count: {len(issues)}")
    if issues:
        for issue in issues:
            print(f"- {issue}")
    else:
        print("- no blocking normalization issues found")


if __name__ == "__main__":
    main()
