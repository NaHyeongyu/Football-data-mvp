from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if __package__ in {None, ""}:
    if str(ROOT_DIR) not in sys.path:
        sys.path.append(str(ROOT_DIR))

    from db.workbook.normalize_schema_loaders import load_workbook_data
    from db.workbook.normalize_schema_normalizers import normalize_workbook
    from db.workbook.normalize_schema_output import (
        apply_temporal_formats,
        ensure_readme_sheet,
        reorder_workbook_sheets,
        replace_sheets,
    )
    from db.workbook.normalize_schema_shared import DEFAULT_WORKBOOK_PATH
    from db.workbook.workbook_enums import apply_enum_reference
else:
    from .normalize_schema_loaders import load_workbook_data
    from .normalize_schema_normalizers import normalize_workbook
    from .normalize_schema_output import (
        apply_temporal_formats,
        ensure_readme_sheet,
        reorder_workbook_sheets,
        replace_sheets,
    )
    from .normalize_schema_shared import DEFAULT_WORKBOOK_PATH
    from .workbook_enums import apply_enum_reference


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize the virtual players workbook schema.")
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook_path = args.workbook.resolve()
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    loaded = load_workbook_data(workbook_path)
    normalized_frames = normalize_workbook(loaded)
    replace_sheets(workbook_path, normalized_frames)
    apply_temporal_formats(workbook_path)
    ensure_readme_sheet(workbook_path, loaded.readme)
    apply_enum_reference(workbook_path)
    reorder_workbook_sheets(workbook_path)
    print(f"normalized {workbook_path}")


if __name__ == "__main__":
    main()
