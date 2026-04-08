from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db.scripts.load_virtual_players_workbook_db import (  # noqa: E402
    fetch_table_counts,
    initialize_schema,
    load_prepared_workbook,
    wait_for_connection,
)
from db.scripts.load_virtual_players_workbook_prepare import load_frames, prepare_workbook  # noqa: E402
from db.scripts.load_virtual_players_workbook_shared import (  # noqa: E402
    DEFAULT_DATABASE_URL,
    DEFAULT_WORKBOOK_PATH,
    TRUNCATE_SQL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load the virtual players workbook into PostgreSQL.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--workbook", default=str(DEFAULT_WORKBOOK_PATH))
    parser.add_argument("--retries", type=int, default=20)
    parser.add_argument("--retry-delay", type=float, default=1.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook_path = Path(args.workbook).resolve()
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    prepared = prepare_workbook(load_frames(workbook_path))

    with wait_for_connection(args.database_url, args.retries, args.retry_delay) as conn:
        with conn.cursor() as cursor:
            initialize_schema(cursor)
            cursor.execute(TRUNCATE_SQL)
            load_prepared_workbook(cursor, prepared)

        conn.commit()
        counts = fetch_table_counts(conn)

    print(f"Loaded workbook: {workbook_path}")
    for label, value in counts.items():
        print(f"- {label}: {value}")


if __name__ == "__main__":
    main()
