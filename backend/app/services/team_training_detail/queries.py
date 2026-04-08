from __future__ import annotations


TRAINING_META_QUERY = """
SELECT
    t.training_id,
    t.training_date,
    t.session_name::text AS session_name,
    t.training_type::text AS training_type,
    t.training_focus::text AS training_focus,
    t.training_detail::text AS training_detail,
    t.notes::text AS notes,
    t.start_time AS start_at,
    t.end_time AS end_at,
    t.intensity_level::text AS intensity_level,
    c.coach_name,
    l.location_name AS location
FROM football.trainings AS t
JOIN football.coaches AS c
    ON c.coach_id = t.coach_id
JOIN football.training_locations AS l
    ON l.training_location_id = t.training_location_id
WHERE t.training_id = %s
  AND t.training_date <= %s
"""


TRAINING_PLAYERS_QUERY = """
SELECT
    tgs.training_gps_id,
    tgs.training_id,
    p.player_id,
    p.name,
    p.jersey_number,
    p.primary_position::text AS position,
    tgs.play_time_min,
    tgs.total_distance,
    tgs.avg_speed,
    tgs.distance_0_15_min,
    tgs.distance_15_30_min,
    tgs.distance_30_45_min,
    tgs.distance_45_60_min,
    tgs.distance_60_75_min,
    tgs.distance_75_90_min,
    tgs.max_speed,
    tgs.sprint_count,
    tgs.sprint_distance,
    tgs.distance_speed_0_5,
    tgs.distance_speed_5_10,
    tgs.distance_speed_10_15,
    tgs.distance_speed_15_20,
    tgs.distance_speed_20_25,
    tgs.distance_speed_25_plus,
    tgs.accel_count,
    tgs.decel_count,
    tgs.hi_accel_count,
    tgs.hi_decel_count,
    tgs.cod_count
FROM football.training_gps_stats AS tgs
JOIN football.players AS p
    ON p.player_id = tgs.player_id
JOIN football.trainings AS t
    ON t.training_id = tgs.training_id
WHERE tgs.training_id = %s
  AND t.training_date <= %s
"""


TRAINING_LEADER_SPECS: list[tuple[str, str, str | None]] = [
    ("total_distance", "총 거리", "km"),
    ("sprint_count", "스프린트", "회"),
    ("max_speed", "최고속도", "km/h"),
    ("accel_count", "가속", "회"),
]

NON_DISPLAY_TRAINING_NOTES = {
    "경기 일정과 중복되지 않도록 편성.",
}
