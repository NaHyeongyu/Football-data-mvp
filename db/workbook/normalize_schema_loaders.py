from __future__ import annotations

from pathlib import Path

import pandas as pd

from .normalize_schema_shared import BASE_SHEETS, LoadedWorkbook


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


def load_workbook_data(workbook_path: Path) -> LoadedWorkbook:
    workbook = pd.ExcelFile(workbook_path)
    frames = pd.read_excel(workbook_path, sheet_name=list(BASE_SHEETS))
    readme = pd.read_excel(workbook_path, sheet_name="README", header=None) if "README" in workbook.sheet_names else None

    # Keep legacy support while converting all outputs into split GPS sheets.
    if "gps_data" in workbook.sheet_names:
        frames["gps_data"] = pd.read_excel(workbook_path, sheet_name="gps_data")
        gps_sheet_mode = "combined"
    else:
        frames["match_gps_data"] = pd.read_excel(workbook_path, sheet_name="match_gps_data") if "match_gps_data" in workbook.sheet_names else pd.DataFrame()
        frames["training_gps_data"] = pd.read_excel(workbook_path, sheet_name="training_gps_data") if "training_gps_data" in workbook.sheet_names else pd.DataFrame()
        gps_sheet_mode = "split"

    return LoadedWorkbook(frames=frames, readme=readme, gps_sheet_mode=gps_sheet_mode)
