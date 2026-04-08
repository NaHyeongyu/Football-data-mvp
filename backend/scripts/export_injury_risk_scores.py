from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.app.services.injury_risk import build_player_injury_risk_report


MAX_REASON_COUNT = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export score-based player injury risk data.")
    parser.add_argument("--as-of-date", type=date.fromisoformat, default=None)
    parser.add_argument("--risk-band", choices=["normal", "watch", "risk"], default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def serialize_report_item(item: Any) -> dict[str, Any]:
    row = {
        "snapshot_date": item.snapshot_date,
        "player_id": item.player_id,
        "name": item.name,
        "primary_position": item.primary_position,
        "status": item.status,
        "overall_risk_score": item.overall_risk_score,
        "risk_band": item.risk_band,
        "load_score": item.factors.load_score,
        "physical_change_score": item.factors.physical_change_score,
        "injury_history_score": item.factors.injury_history_score,
        "return_to_play_score": item.factors.return_to_play_score,
        "symptom_score": item.factors.symptom_score,
        "acute_load_7d": item.factors.acute_load_7d,
        "acute_load_percentile": item.factors.acute_load_percentile,
        "chronic_load_baseline": item.factors.chronic_load_baseline,
        "acute_chronic_ratio": item.factors.acute_chronic_ratio,
        "acute_distance_7d": item.factors.acute_distance_7d,
        "chronic_distance_baseline": item.factors.chronic_distance_baseline,
        "distance_ratio": item.factors.distance_ratio,
        "high_intensity_sessions_7d": item.factors.high_intensity_sessions_7d,
        "match_minutes_7d": item.factors.match_minutes_7d,
        "sprint_count_7d": item.factors.sprint_count_7d,
        "sprint_count_baseline": item.factors.sprint_count_baseline,
        "sprint_ratio": item.factors.sprint_ratio,
        "body_fat_delta": item.factors.body_fat_delta,
        "muscle_mass_delta": item.factors.muscle_mass_delta,
        "weight_delta": item.factors.weight_delta,
        "injuries_last_180d": item.factors.injuries_last_180d,
        "injuries_last_365d": item.factors.injuries_last_365d,
        "reinjury_flag": item.factors.reinjury_flag,
        "days_since_return": item.factors.days_since_return,
        "open_rehab_flag": item.factors.open_rehab_flag,
        "recent_symptom_count_120d": item.factors.recent_symptom_count_120d,
        "recent_symptom_flag": item.factors.recent_symptom_flag,
        "latest_symptom_days_ago": item.factors.latest_symptom_days_ago,
        "recent_medical_consultation_count_14d": item.factors.recent_medical_consultation_count_14d,
    }
    for index in range(MAX_REASON_COUNT):
        row[f"reason_{index + 1}"] = item.reasons[index] if len(item.reasons) > index else None
    return row


def build_export_frame(items: list[Any]) -> pd.DataFrame:
    return pd.DataFrame(serialize_report_item(item) for item in items)


def write_output(frame: pd.DataFrame, output_path: Path | None) -> None:
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output_path, index=False)
        print(f"saved {output_path}")
        return
    print(frame.to_string(index=False))


def main() -> None:
    args = parse_args()
    report = build_player_injury_risk_report(
        as_of_date=args.as_of_date,
        limit=args.limit,
        risk_band=args.risk_band,
    )
    frame = build_export_frame(report.items)
    write_output(frame, args.output)


if __name__ == "__main__":
    main()
