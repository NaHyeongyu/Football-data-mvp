from __future__ import annotations

from datetime import date

import pandas as pd


def _resolve_snapshot_date(
    as_of_date: date | None,
    training_load: pd.DataFrame,
    match_load: pd.DataFrame,
    match_stats: pd.DataFrame,
    physical_profiles: pd.DataFrame,
    injuries: pd.DataFrame,
) -> pd.Timestamp:
    if as_of_date is not None:
        return pd.Timestamp(as_of_date)

    candidates: list[pd.Timestamp] = []
    for frame, column in [
        (training_load, "session_date"),
        (match_load, "session_date"),
        (match_stats, "match_date"),
        (physical_profiles, "created_at"),
        (injuries, "actual_return_date"),
        (injuries, "injury_date"),
    ]:
        if frame.empty or column not in frame.columns:
            continue
        values = pd.to_datetime(frame[column], errors="coerce").dropna()
        if not values.empty:
            candidates.append(values.max().normalize())

    if not candidates:
        raise RuntimeError("No dated team records were found.")
    return max(candidates)


def _resolve_load_snapshot_date(
    training_load: pd.DataFrame,
    match_load: pd.DataFrame,
    snapshot_ts: pd.Timestamp,
) -> pd.Timestamp:
    candidates: list[pd.Timestamp] = []
    for frame in [training_load, match_load]:
        if frame.empty or "session_date" not in frame.columns:
            continue
        values = pd.to_datetime(frame["session_date"], errors="coerce").dropna()
        if not values.empty:
            candidates.append(values.max().normalize())
    if not candidates:
        return snapshot_ts
    return min(snapshot_ts, max(candidates))


__all__ = [
    "_resolve_load_snapshot_date",
    "_resolve_snapshot_date",
]
