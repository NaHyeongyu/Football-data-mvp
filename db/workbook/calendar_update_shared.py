from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_WORKBOOK_PATH = Path(__file__).resolve().parents[2] / "virtual_players_2008_complete_with_all_staff_data.xlsx"
END_OF_2025 = pd.Timestamp("2025-12-31 23:59:59")
CALENDAR_END_DATE = END_OF_2025.normalize()

WORKBOOK_SHEETS = (
    "player_info",
    "physical_test_data",
    "physical_data",
    "injury_history",
    "match_data",
    "match_player_data",
    "training_data",
    "evaluations",
    "counseling",
)

MATCH_PLAYER_CONTEXT_COLUMNS = (
    "match_date",
    "match_type",
    "phase",
    "stadium",
    "opponent_team",
    "score_home",
    "score_away",
    "possession_home",
    "possession_away",
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

GPS_LEADING_COLUMNS = (
    "gps_id",
    "match_id",
    "training_id",
    "player_id",
    "distance",
    "play_time_min",
    "avg_speed",
    "max_speed",
)

MATCH_GPS_LEADING_COLUMNS = (
    "match_gps_id",
    "match_id",
    "player_id",
    "distance",
    "play_time_min",
    "avg_speed",
    "max_speed",
)

TRAINING_GPS_LEADING_COLUMNS = (
    "training_gps_id",
    "training_id",
    "player_id",
    "distance",
    "play_time_min",
    "avg_speed",
    "max_speed",
)

DATE_ONLY_COLUMNS = {
    "player_info": {"date_of_birth"},
    "physical_test_data": {"player_birth_day", "test_date"},
    "physical_data": {"player_birth_day"},
    "injury_history": {"injury_date", "expected_return_date", "actual_return_date"},
    "match_data": {"match_date"},
    "match_player_data": {"match_date", "player_birth_day"},
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

PHYSICAL_CHECKPOINTS = {
    2023: [pd.Timestamp("2023-02-25"), pd.Timestamp("2023-07-29"), pd.Timestamp("2023-12-07")],
    2024: [pd.Timestamp("2024-02-24"), pd.Timestamp("2024-07-27"), pd.Timestamp("2024-12-07")],
    2025: [pd.Timestamp("2025-02-22"), pd.Timestamp("2025-07-26"), pd.Timestamp("2025-12-06")],
}


WorkbookFrames = dict[str, pd.DataFrame]


@dataclass(frozen=True)
class PlayerDirectory:
    name_by_id: dict[str, str]
    birth_date_by_id: dict[str, pd.Timestamp]
    player_id_by_name: dict[str, str]


@dataclass(frozen=True)
class MatchTransforms:
    match_id_to_date: dict[str, pd.Timestamp]
    old_dates_by_year: dict[int, list[pd.Timestamp]]
    new_dates_by_year: dict[int, list[pd.Timestamp]]
    match_dates_by_year: dict[int, list[pd.Timestamp]]


@dataclass(frozen=True)
class LoadedWorkbook:
    frames: WorkbookFrames
    gps_sheet_mode: str
    source_columns: dict[str, list[str]]


def first_weekday_on_or_after(year: int, month: int, day: int, weekday: int) -> pd.Timestamp:
    value = pd.Timestamp(year=year, month=month, day=day)
    delta = (weekday - value.weekday()) % 7
    return value + pd.Timedelta(days=delta)


def generate_alternating(start: pd.Timestamp, count: int, gaps: tuple[int, ...]) -> list[pd.Timestamp]:
    values = [start]
    while len(values) < count:
        gap = gaps[(len(values) - 1) % len(gaps)]
        values.append(values[-1] + pd.Timedelta(days=gap))
    return values[:count]


def build_phase_dates(year: int, phase_counts: dict[str, int]) -> dict[str, list[pd.Timestamp]]:
    phase_dates: dict[str, list[pd.Timestamp]] = {}

    winter_start = first_weekday_on_or_after(year, 1, 10, 5)
    phase_dates["동계훈련 연습경기"] = generate_alternating(
        winter_start,
        phase_counts.get("동계훈련 연습경기", 0),
        (4, 3),
    )

    feb_start = first_weekday_on_or_after(year, 2, 15, 5)
    feb_offsets = (0, 3, 5, 8, 10, 12)
    phase_dates["2월 공식대회"] = [
        feb_start + pd.Timedelta(days=feb_offsets[index])
        for index in range(phase_counts.get("2월 공식대회", 0))
    ]

    may_start = first_weekday_on_or_after(year, 5, 4, 5)
    may_offsets = (0, 4, 7, 11, 14, 18)
    phase_dates["5월 공식대회"] = [
        may_start + pd.Timedelta(days=may_offsets[index])
        for index in range(phase_counts.get("5월 공식대회", 0))
    ]

    july_start = first_weekday_on_or_after(year, 7, 15, 0)
    july_offsets = (0, 3, 6, 9, 12, 15)
    phase_dates["7월 전국대회"] = [
        july_start + pd.Timedelta(days=july_offsets[index])
        for index in range(phase_counts.get("7월 전국대회", 0))
    ]

    october_start = pd.Timestamp(year=year, month=10, day=3)
    october_offsets = (0, 3, 6, 9, 12, 15)
    phase_dates["10월 전국대회"] = [
        october_start + pd.Timedelta(days=october_offsets[index])
        for index in range(phase_counts.get("10월 전국대회", 0))
    ]

    closing_start = first_weekday_on_or_after(year, 11, 2, 5)
    phase_dates["시즌 마무리 연습경기"] = [
        closing_start + pd.Timedelta(days=7 * index)
        for index in range(phase_counts.get("시즌 마무리 연습경기", 0))
    ]

    reserved_dates = {value for values in phase_dates.values() for value in values}

    weekend_candidates = list(
        pd.date_range(
            first_weekday_on_or_after(year, 3, 2, 5),
            first_weekday_on_or_after(year, 9, 28, 5),
            freq="7D",
        )
    )
    weekend_candidates.extend(
        pd.date_range(
            first_weekday_on_or_after(year, 10, 19, 5),
            first_weekday_on_or_after(year, 10, 26, 5),
            freq="7D",
        )
    )
    weekend_dates = [value for value in weekend_candidates if value not in reserved_dates]
    phase_dates["주말리그"] = weekend_dates[: phase_counts.get("주말리그", 0)]

    midweek_candidates = list(
        pd.date_range(
            first_weekday_on_or_after(year, 3, 6, 2),
            first_weekday_on_or_after(year, 10, 29, 2),
            freq="7D",
        )
    )
    midweek_dates = [value for value in midweek_candidates if value not in reserved_dates]
    phase_dates["주중 연습경기"] = midweek_dates[: phase_counts.get("주중 연습경기", 0)]

    return phase_dates


def transform_timestamp(
    value: pd.Timestamp,
    old_dates: list[pd.Timestamp],
    new_dates: list[pd.Timestamp],
) -> pd.Timestamp:
    if pd.isna(value):
        return pd.NaT

    timestamp = pd.Timestamp(value)
    if timestamp <= old_dates[0]:
        return new_dates[0] + (timestamp - old_dates[0])
    if timestamp >= old_dates[-1]:
        return new_dates[-1] + (timestamp - old_dates[-1])

    index = bisect_right(old_dates, timestamp) - 1
    left_old = old_dates[index]
    right_old = old_dates[index + 1]
    left_new = new_dates[index]
    right_new = new_dates[index + 1]

    total_seconds = (right_old - left_old).total_seconds()
    if total_seconds == 0:
        return left_new

    ratio = (timestamp - left_old).total_seconds() / total_seconds
    new_span = (right_new - left_new).total_seconds()
    return left_new + pd.to_timedelta(round(new_span * ratio), unit="s")


def second_monday(year: int, month: int) -> pd.Timestamp:
    first = first_weekday_on_or_after(year, month, 1, 0)
    return first + pd.Timedelta(days=7)


def third_monday(year: int, month: int) -> pd.Timestamp:
    return second_monday(year, month) + pd.Timedelta(days=7)


def normalize_date(value: Any) -> date | None:
    if pd.isna(value):
        return None
    return pd.Timestamp(value).to_pydatetime().date()


def normalize_datetime(value: Any) -> datetime | None:
    if pd.isna(value):
        return None
    timestamp = min(pd.Timestamp(value), END_OF_2025)
    return timestamp.to_pydatetime().replace(second=0, microsecond=0)


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


def combine_date_and_time(target_date: pd.Timestamp, source_value: Any) -> pd.Timestamp:
    if pd.isna(source_value):
        return pd.NaT
    source = pd.Timestamp(source_value)
    return target_date + pd.Timedelta(hours=source.hour, minutes=source.minute)


def with_offset(values: Iterable[Any], offset: pd.Timedelta | None = None) -> list[pd.Timestamp]:
    timestamps: list[pd.Timestamp] = []
    for value in values:
        if pd.isna(value):
            continue
        timestamp = pd.Timestamp(value)
        if offset is not None:
            timestamp += offset
        timestamps.append(timestamp)
    return timestamps
