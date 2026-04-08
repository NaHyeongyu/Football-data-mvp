from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        yield connection
    finally:
        connection.close()
