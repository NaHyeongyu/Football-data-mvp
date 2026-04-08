from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Any

import pandas as pd

from .calendar_update_loaders import build_year_date_index
from .calendar_update_shared import (
    CALENDAR_END_DATE,
    END_OF_2025,
    MATCH_PLAYER_CONTEXT_COLUMNS,
    PHYSICAL_CHECKPOINTS,
    MatchTransforms,
    PlayerDirectory,
    WorkbookFrames,
    build_phase_dates,
    build_year_scoped_ids,
    combine_date_and_time,
    second_monday,
    third_monday,
    transform_timestamp,
    with_offset,
)


def resolve_training_target_date(
    original_date: pd.Timestamp,
    transformed_date: pd.Timestamp,
    match_dates: list[pd.Timestamp],
    training_type: str,
) -> pd.Timestamp:
    normalized_original = original_date.normalize()
    if training_type == "pre_match":
        next_index = bisect_right(match_dates, normalized_original)
        if next_index < len(match_dates):
            return match_dates[next_index] - pd.Timedelta(days=1)
    if training_type == "recovery":
        previous_index = bisect_left(match_dates, normalized_original) - 1
        if previous_index >= 0:
            return match_dates[previous_index] + pd.Timedelta(days=1)
    return transformed_date.normalize()


def build_match_transforms(match_data: pd.DataFrame) -> MatchTransforms:
    match_id_to_date: dict[str, pd.Timestamp] = {}
    old_dates_by_year: dict[int, list[pd.Timestamp]] = {}
    new_dates_by_year: dict[int, list[pd.Timestamp]] = {}

    for year, frame in match_data.groupby("year", sort=True):
        phase_counts = frame["phase"].value_counts().to_dict()
        phase_dates = build_phase_dates(int(year), phase_counts)
        phase_positions: defaultdict[str, int] = defaultdict(int)

        old_dates = frame["match_date"].sort_values().drop_duplicates().tolist()
        new_dates: list[pd.Timestamp] = []
        for row in frame.itertuples(index=False):
            position = phase_positions[row.phase]
            phase_positions[row.phase] += 1
            new_date = phase_dates[row.phase][position]
            match_id_to_date[row.match_id] = new_date
            new_dates.append(new_date)

        old_dates_by_year[int(year)] = old_dates
        new_dates_by_year[int(year)] = sorted(pd.Series(new_dates).drop_duplicates().tolist())

    remapped = match_data.copy()
    remapped["match_date"] = remapped["match_id"].map(match_id_to_date)
    return MatchTransforms(
        match_id_to_date=match_id_to_date,
        old_dates_by_year=old_dates_by_year,
        new_dates_by_year=new_dates_by_year,
        match_dates_by_year=build_year_date_index(remapped, "match_date"),
    )


def rebuild_match_player_frame(
    match_player: pd.DataFrame,
    match_data: pd.DataFrame,
    directory: PlayerDirectory,
    source_columns: Sequence[str],
) -> pd.DataFrame:
    base = match_player.drop(columns=[*MATCH_PLAYER_CONTEXT_COLUMNS, "player_name", "player_birth_day"], errors="ignore").copy()
    context = match_data.set_index("match_id")
    base["match_date"] = base["match_id"].map(context["match_date"])

    for column in source_columns:
        if column in {"match_date", "player_name", "player_birth_day"}:
            continue
        if column in context.columns and column not in base.columns:
            base[column] = base["match_id"].map(context[column])

    if "player_name" in source_columns:
        base["player_name"] = base["player_id"].map(directory.name_by_id)
    if "player_birth_day" in source_columns:
        base["player_birth_day"] = base["player_id"].map(directory.birth_date_by_id)

    return base


def rebuild_training_frame(training: pd.DataFrame, transforms: MatchTransforms) -> tuple[pd.DataFrame, dict[int, list[pd.Timestamp]]]:
    rows: list[dict[str, Any]] = []
    for year, frame in training.groupby("year", sort=True):
        year_int = int(year)
        old_dates = transforms.old_dates_by_year[year_int]
        new_dates = transforms.new_dates_by_year[year_int]
        match_dates = transforms.match_dates_by_year[year_int]

        for row in frame.sort_values("training_date").itertuples(index=False):
            original_date = pd.Timestamp(row.training_date)
            transformed_date = transform_timestamp(original_date, old_dates, new_dates)
            # Pre-match and recovery sessions should stay aligned to the nearest match cadence.
            target_date = resolve_training_target_date(
                original_date=original_date,
                transformed_date=transformed_date,
                match_dates=match_dates,
                training_type=str(row.training_type),
            ).normalize()

            record = row._asdict()
            record["training_date"] = target_date
            record["start_time"] = combine_date_and_time(target_date, row.start_time)
            record["end_time"] = combine_date_and_time(target_date, row.end_time)
            record["created_at"] = combine_date_and_time(target_date, row.created_at)
            record["updated_at"] = combine_date_and_time(target_date, row.updated_at)
            rows.append(record)

    training_frame = pd.DataFrame(rows).drop(columns=["year"], errors="ignore")
    return training_frame, build_year_date_index(training_frame, "training_date")


def build_monthly_anchor_calendar(
    years: Iterable[int],
    anchor_builder: Any,
) -> dict[tuple[int, int], pd.Timestamp]:
    return {
        (year, month): anchor_builder(year, month)
        for year in sorted(set(int(year) for year in years))
        for month in range(1, 13)
    }


def map_monthly_anchor(value: Any, calendar: dict[tuple[int, int], pd.Timestamp]) -> pd.Timestamp:
    if pd.isna(value):
        return pd.NaT
    timestamp = pd.Timestamp(value)
    return calendar[(timestamp.year, timestamp.month)]


def align_review_dates(evaluations: pd.DataFrame, counseling: pd.DataFrame) -> None:
    years = set(pd.to_datetime(evaluations["evaluation_date"], errors="coerce").dropna().dt.year.tolist())
    years.update(pd.to_datetime(counseling["counseling_date"], errors="coerce").dropna().dt.year.tolist())

    evaluation_calendar = build_monthly_anchor_calendar(years, second_monday)
    counseling_calendar = build_monthly_anchor_calendar(years, third_monday)
    evaluations["evaluation_date"] = evaluations["evaluation_date"].map(lambda value: map_monthly_anchor(value, evaluation_calendar))
    counseling["counseling_date"] = counseling["counseling_date"].map(lambda value: map_monthly_anchor(value, counseling_calendar))


def align_physical_tests(physical_test: pd.DataFrame, directory: PlayerDirectory) -> None:
    group_column = "player_id" if "player_id" in physical_test.columns else "player_name"
    for (group_value, year), group in physical_test.groupby([group_column, "year"], sort=True):
        checkpoints = PHYSICAL_CHECKPOINTS.get(int(year))
        if checkpoints is None:
            raise ValueError(f"No physical test checkpoints configured for year={year}")
        ordered_indices = group.sort_values("test_date").index.tolist()
        if len(ordered_indices) > len(checkpoints):
            raise ValueError(f"Too many physical tests for player={group_value} year={year}")

        player_id = str(group_value) if group_column == "player_id" else directory.player_id_by_name[group_value]
        birth_date = directory.birth_date_by_id[player_id]
        player_name = directory.name_by_id[player_id]
        for index, checkpoint in zip(ordered_indices, checkpoints):
            physical_test.at[index, "test_date"] = checkpoint
            if "player_birth_day" in physical_test.columns:
                physical_test.at[index, "player_birth_day"] = birth_date
            if "player_name" in physical_test.columns:
                physical_test.at[index, "player_name"] = player_name


def align_physical_profiles(physical_data: pd.DataFrame, directory: PlayerDirectory) -> None:
    group_column = "player_id" if "player_id" in physical_data.columns else "player_name"
    for (group_value, year), group in physical_data.groupby([group_column, "year"], sort=True):
        checkpoints = PHYSICAL_CHECKPOINTS.get(int(year))
        if checkpoints is None:
            raise ValueError(f"No physical profile checkpoints configured for year={year}")
        ordered_indices = group.sort_values("created_at").index.tolist()
        if len(ordered_indices) > len(checkpoints):
            raise ValueError(f"Too many physical profiles for player={group_value} year={year}")

        player_id = str(group_value) if group_column == "player_id" else directory.player_id_by_name[group_value]
        birth_date = directory.birth_date_by_id[player_id]
        player_name = directory.name_by_id[player_id]
        for index, checkpoint in zip(ordered_indices, checkpoints):
            source_timestamp = pd.Timestamp(physical_data.at[index, "created_at"])
            physical_data.at[index, "created_at"] = combine_date_and_time(checkpoint, source_timestamp)
            if "player_birth_day" in physical_data.columns:
                physical_data.at[index, "player_birth_day"] = birth_date
            if "player_name" in physical_data.columns:
                physical_data.at[index, "player_name"] = player_name


def snap_to_nearest_date(candidate: pd.Timestamp, pool: list[pd.Timestamp]) -> pd.Timestamp:
    if not pool:
        return candidate
    return min(pool, key=lambda value: abs((value - candidate).days))


def rebuild_injury_frame(
    injuries: pd.DataFrame,
    transforms: MatchTransforms,
    training_dates_by_year: dict[int, list[pd.Timestamp]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in injuries.itertuples(index=False):
        year = int(pd.Timestamp(row.injury_date).year)
        candidate = transform_timestamp(
            row.injury_date,
            transforms.old_dates_by_year[year],
            transforms.new_dates_by_year[year],
        ).normalize()
        if str(row.occurred_during).lower() == "match":
            pool = transforms.match_dates_by_year.get(year, [])
        else:
            pool = training_dates_by_year.get(year, [])

        snapped = snap_to_nearest_date(candidate, pool)
        expected_gap = 0 if pd.isna(row.expected_return_date) else int((pd.Timestamp(row.expected_return_date) - pd.Timestamp(row.injury_date)).days)
        actual_gap = None
        if pd.notna(row.actual_return_date):
            actual_gap = int((pd.Timestamp(row.actual_return_date) - pd.Timestamp(row.injury_date)).days)

        record = row._asdict()
        record["injury_date"] = snapped
        record["expected_return_date"] = min(snapped + pd.Timedelta(days=expected_gap), CALENDAR_END_DATE)
        if actual_gap is None:
            record["actual_return_date"] = pd.NaT
        else:
            record["actual_return_date"] = min(snapped + pd.Timedelta(days=actual_gap), CALENDAR_END_DATE)
        record["created_at"] = snapped + pd.Timedelta(hours=18)
        record["updated_at"] = (
            pd.Timestamp(record["actual_return_date"]) + pd.Timedelta(hours=10)
            if pd.notna(record["actual_return_date"])
            else pd.Timestamp(record["expected_return_date"]) + pd.Timedelta(hours=10)
        )
        rows.append(record)

    return pd.DataFrame(rows)


def compute_player_activity_bounds(
    player_info: pd.DataFrame,
    match_player: pd.DataFrame,
    physical_data: pd.DataFrame,
    evaluations: pd.DataFrame,
    counseling: pd.DataFrame,
    injuries: pd.DataFrame,
) -> tuple[dict[str, pd.Timestamp], dict[str, pd.Timestamp]]:
    first_activity_by_player: dict[str, pd.Timestamp] = {}
    last_activity_by_player: dict[str, pd.Timestamp] = {}

    for player_id in player_info["player_id"]:
        timestamps: list[pd.Timestamp] = []
        timestamps.extend(with_offset(match_player.loc[match_player["player_id"] == player_id, "match_date"], pd.Timedelta(hours=18)))
        timestamps.extend(with_offset(physical_data.loc[physical_data["player_id"] == player_id, "created_at"]))
        timestamps.extend(with_offset(evaluations.loc[evaluations["player_id"] == player_id, "evaluation_date"], pd.Timedelta(hours=17)))
        timestamps.extend(
            with_offset(
                counseling.loc[counseling["player_id"] == player_id, "counseling_date"],
                pd.Timedelta(hours=17, minutes=30),
            )
        )

        injury_values = injuries.loc[
            injuries["player_id"] == player_id,
            ["injury_date", "expected_return_date", "actual_return_date", "updated_at"],
        ].to_numpy().ravel()
        timestamps.extend(with_offset(injury_values))

        if not timestamps:
            raise ValueError(f"No activity timestamps available for player_id={player_id}")

        ordered = sorted(timestamps)
        first_activity_by_player[player_id] = ordered[0]
        last_activity_by_player[player_id] = min(ordered[-1], END_OF_2025)

    return first_activity_by_player, last_activity_by_player


def update_player_activity_metadata(
    player_info: pd.DataFrame,
    first_activity_by_player: dict[str, pd.Timestamp],
    last_activity_by_player: dict[str, pd.Timestamp],
) -> None:
    joined_at_values = []
    floor = pd.Timestamp("2023-01-02 09:00:00")
    for index, player_id in enumerate(player_info["player_id"]):
        baseline = first_activity_by_player[player_id] - pd.Timedelta(days=21 + (index % 3) * 7)
        joined_at_values.append(max(baseline, floor))

    player_info["joined_at"] = joined_at_values
    player_info["updated_at"] = player_info["player_id"].map(last_activity_by_player)


def rebuild_scoped_identifiers(frames: WorkbookFrames) -> None:
    frames["physical_test_data"]["physical_test_id"] = build_year_scoped_ids(frames["physical_test_data"], "test_date", "PTEST", 4)
    frames["physical_data"]["physical_data_id"] = build_year_scoped_ids(frames["physical_data"], "created_at", "PDATA", 4)
    frames["match_player_data"]["match_player_id"] = build_year_scoped_ids(frames["match_player_data"], "match_date", "MPL", 5)
    frames["evaluations"]["evaluation_id"] = build_year_scoped_ids(frames["evaluations"], "evaluation_date", "EVAL", 4)
    frames["counseling"]["counseling_id"] = build_year_scoped_ids(frames["counseling"], "counseling_date", "COUN", 4)
