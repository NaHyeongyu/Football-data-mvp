from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from ..db import get_connection


def fetch_frame(query: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or [])
            columns = [column.name for column in (cursor.description or [])]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
