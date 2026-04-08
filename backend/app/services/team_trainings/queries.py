from __future__ import annotations


TEAM_TRAININGS_LIST_QUERY = """
SELECT
    t.training_id,
    t.training_date,
    t.session_name::text AS session_name,
    t.training_type::text AS training_type,
    t.training_focus::text AS training_focus,
    t.intensity_level::text AS intensity_level,
    c.coach_name,
    l.location_name AS location,
    t.start_time AS start_at,
    t.end_time AS end_at,
    gps.participant_count,
    gps.total_distance
FROM football.trainings AS t
JOIN football.coaches AS c
    ON c.coach_id = t.coach_id
JOIN football.training_locations AS l
    ON l.training_location_id = t.training_location_id
LEFT JOIN (
    SELECT
        training_id,
        COUNT(DISTINCT player_id) AS participant_count,
        SUM(total_distance) AS total_distance
    FROM football.training_gps_stats
    GROUP BY training_id
) AS gps
    ON gps.training_id = t.training_id
WHERE t.training_date <= %s
"""
