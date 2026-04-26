from __future__ import annotations

import time
from collections.abc import Iterable, Iterator, Sequence
from numbers import Integral, Real
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from psycopg import sql

from .load_virtual_players_workbook_shared import COUNT_QUERIES, INIT_SQL_FILES, LOOKUP_SPECS, PreparedWorkbook, TABLE_COPY_SPECS


def _py_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real) and float(value).is_integer():
        return int(value)
    return value


def execute_sql_file(cursor: psycopg.Cursor[Any], path: Path) -> None:
    cursor.execute(path.read_text(encoding="utf-8"))


def initialize_schema(cursor: psycopg.Cursor[Any]) -> None:
    for path in INIT_SQL_FILES:
        execute_sql_file(cursor, path)


def iter_frame_rows(frame: pd.DataFrame, columns: Sequence[str]) -> Iterator[tuple[Any, ...]]:
    selected_frame = frame.loc[:, list(columns)]
    for row in selected_frame.itertuples(index=False, name=None):
        yield tuple(_py_value(value) for value in row)


def copy_rows(
    cursor: psycopg.Cursor[Any],
    table_name: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[Any]],
) -> None:
    statement = sql.SQL("COPY {} ({}) FROM STDIN").format(
        sql.Identifier("football", table_name),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
    )
    # Stream rows directly into COPY so large workbook loads do not duplicate frame data in memory.
    with cursor.copy(statement) as copy:
        for row in rows:
            copy.write_row(row)


def load_prepared_workbook(cursor: psycopg.Cursor[Any], prepared: PreparedWorkbook) -> None:
    for spec in LOOKUP_SPECS:
        lookup = prepared.lookup_loads[spec.table_name]
        copy_rows(cursor, lookup.table_name, lookup.columns, lookup.rows)

    for spec in TABLE_COPY_SPECS:
        frame = prepared.table_frames[spec.frame_name]
        columns = spec.columns or tuple(frame.columns.tolist())
        copy_rows(cursor, spec.table_name, columns, iter_frame_rows(frame, columns))

    cursor.execute("SELECT football.refresh_evaluation_labels()")


def wait_for_connection(database_url: str, retries: int, retry_delay: float) -> psycopg.Connection[Any]:
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            return psycopg.connect(database_url)
        except Exception as exc:  # pragma: no cover - operational retry path
            last_error = exc
            time.sleep(retry_delay)
    raise RuntimeError(f"Could not connect to database: {last_error}") from last_error


def fetch_table_counts(conn: psycopg.Connection[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cursor:
        for label, query in COUNT_QUERIES.items():
            cursor.execute(query)
            counts[label] = int(cursor.fetchone()[0])
    return counts
