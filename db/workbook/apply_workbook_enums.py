from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db.workbook.workbook_enums import WORKBOOK_PATH, apply_enum_reference


def main() -> None:
    apply_enum_reference(WORKBOOK_PATH)
    print(f"applied enum validation to {WORKBOOK_PATH}")


if __name__ == "__main__":
    main()
