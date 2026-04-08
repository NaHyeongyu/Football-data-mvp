from __future__ import annotations


MATCH_CALENDAR_QUERY = """
SELECT
    m.match_id AS event_id,
    'match'::text AS event_type,
    m.match_date AS event_date,
    NULL::timestamp AS start_at,
    NULL::timestamp AS end_at,
    CONCAT('vs ', o.opponent_team_name) AS title,
    m.match_type::text AS category,
    NULL::text AS detail,
    s.stadium_name AS location,
    o.opponent_team_name AS opponent_team,
    NULL::text AS intensity_level,
    NULL::text AS coach_name,
    m.goals_for AS score_for,
    m.goals_against AS score_against
FROM football.matches AS m
JOIN football.opponent_teams AS o
    ON o.opponent_team_id = m.opponent_team_id
JOIN football.stadiums AS s
    ON s.stadium_id = m.stadium_id
WHERE m.match_date <= %s
"""


TRAINING_CALENDAR_QUERY = """
SELECT
    t.training_id AS event_id,
    'training'::text AS event_type,
    t.training_date AS event_date,
    t.start_time AS start_at,
    t.end_time AS end_at,
    t.session_name::text AS title,
    t.training_type::text AS category,
    CONCAT(t.training_focus::text, ' · ', t.training_detail) AS detail,
    l.location_name AS location,
    NULL::text AS opponent_team,
    t.intensity_level::text AS intensity_level,
    c.coach_name AS coach_name,
    NULL::integer AS score_for,
    NULL::integer AS score_against
FROM football.trainings AS t
JOIN football.training_locations AS l
    ON l.training_location_id = t.training_location_id
JOIN football.coaches AS c
    ON c.coach_id = t.coach_id
WHERE t.training_date <= %s
"""


EVENT_COLUMNS = [
    "event_id",
    "event_type",
    "event_date",
    "start_at",
    "end_at",
    "title",
    "category",
    "detail",
    "location",
    "opponent_team",
    "intensity_level",
    "coach_name",
    "score_for",
    "score_against",
]
