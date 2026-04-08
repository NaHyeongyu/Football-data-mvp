from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if __package__ in {None, ""}:
    if str(ROOT_DIR) not in sys.path:
        sys.path.append(str(ROOT_DIR))

    from db.workbook.calendar_update_loaders import (
        build_player_directory,
        load_frames,
        populate_player_identifiers,
        prepare_source_frames,
    )
    from db.workbook.calendar_update_output import (
        apply_temporal_formats,
        build_output_frames,
        write_frames,
    )
    from db.workbook.calendar_update_shared import DEFAULT_WORKBOOK_PATH, WorkbookFrames
    from db.workbook.calendar_update_transforms import (
        align_physical_profiles,
        align_physical_tests,
        align_review_dates,
        build_match_transforms,
        compute_player_activity_bounds,
        rebuild_injury_frame,
        rebuild_match_player_frame,
        rebuild_scoped_identifiers,
        rebuild_training_frame,
        update_player_activity_metadata,
    )
else:
    from .calendar_update_loaders import (
        build_player_directory,
        load_frames,
        populate_player_identifiers,
        prepare_source_frames,
    )
    from .calendar_update_output import (
        apply_temporal_formats,
        build_output_frames,
        write_frames,
    )
    from .calendar_update_shared import DEFAULT_WORKBOOK_PATH, WorkbookFrames
    from .calendar_update_transforms import (
        align_physical_profiles,
        align_physical_tests,
        align_review_dates,
        build_match_transforms,
        compute_player_activity_bounds,
        rebuild_injury_frame,
        rebuild_match_player_frame,
        rebuild_scoped_identifiers,
        rebuild_training_frame,
        update_player_activity_metadata,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild workbook calendar dates for matches and dependent sheets.")
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK_PATH)
    return parser.parse_args()


def update_workbook_calendar(workbook_path: Path) -> WorkbookFrames:
    loaded = load_frames(workbook_path)
    frames = loaded.frames
    prepare_source_frames(frames)

    directory = build_player_directory(frames["player_info"])
    populate_player_identifiers(frames, directory)

    # Rebuild the central event calendars first so dependent sheets can map against stable dates.
    transforms = build_match_transforms(frames["match_data"])
    frames["match_data"]["match_date"] = frames["match_data"]["match_id"].map(transforms.match_id_to_date)
    frames["match_player_data"] = rebuild_match_player_frame(
        frames["match_player_data"],
        frames["match_data"],
        directory,
        loaded.source_columns["match_player_data"],
    )

    training_frame, training_dates_by_year = rebuild_training_frame(frames["training_data"], transforms)
    frames["training_data"] = training_frame

    align_review_dates(frames["evaluations"], frames["counseling"])
    align_physical_tests(frames["physical_test_data"], directory)
    align_physical_profiles(frames["physical_data"], directory)
    frames["injury_history"] = rebuild_injury_frame(frames["injury_history"], transforms, training_dates_by_year)

    first_activity_by_player, last_activity_by_player = compute_player_activity_bounds(
        player_info=frames["player_info"],
        match_player=frames["match_player_data"],
        physical_data=frames["physical_data"],
        evaluations=frames["evaluations"],
        counseling=frames["counseling"],
        injuries=frames["injury_history"],
    )
    update_player_activity_metadata(frames["player_info"], first_activity_by_player, last_activity_by_player)
    rebuild_scoped_identifiers(frames)
    return build_output_frames(frames, loaded.gps_sheet_mode, loaded.source_columns)


def main() -> None:
    args = parse_args()
    workbook_path = args.workbook.resolve()
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    output_frames = update_workbook_calendar(workbook_path)
    write_frames(workbook_path, output_frames)
    apply_temporal_formats(workbook_path, list(output_frames))
    print(f"updated {workbook_path}")


if __name__ == "__main__":
    main()
