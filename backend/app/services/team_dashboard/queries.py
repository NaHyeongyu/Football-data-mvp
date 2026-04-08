from __future__ import annotations


ROSTER_QUERY = """
SELECT
    player_id,
    name,
    primary_position::text AS primary_position,
    status::text AS status
FROM football.players
"""


INJURIES_QUERY = """
SELECT
    player_id,
    injury_id,
    injury_date,
    injury_part,
    severity_level::text AS severity_level,
    status::text AS injury_status,
    expected_return_date,
    actual_return_date
FROM football.injuries
"""


TRAINING_LOAD_QUERY = """
SELECT
    tgs.player_id,
    t.training_date AS session_date,
    'training'::text AS session_source,
    t.intensity_level::text AS intensity_level,
    tgs.total_distance,
    tgs.play_time_min,
    tgs.sprint_count,
    tgs.hi_accel_count,
    tgs.hi_decel_count,
    tgs.max_speed
FROM football.training_gps_stats AS tgs
JOIN football.trainings AS t
    ON t.training_id = tgs.training_id
"""


MATCH_LOAD_QUERY = """
SELECT
    mgs.player_id,
    m.match_date AS session_date,
    'match'::text AS session_source,
    NULL::text AS intensity_level,
    mgs.total_distance,
    COALESCE(pms.minutes_played, mgs.play_time_min)::double precision AS play_time_min,
    mgs.sprint_count,
    mgs.hi_accel_count,
    mgs.hi_decel_count,
    mgs.max_speed
FROM football.match_gps_stats AS mgs
JOIN football.matches AS m
    ON m.match_id = mgs.match_id
LEFT JOIN football.player_match_stats AS pms
    ON pms.match_id = mgs.match_id
   AND pms.player_id = mgs.player_id
"""


TEAM_MATCHES_QUERY = """
SELECT
    pms.match_player_id,
    pms.player_id,
    pms.position::text AS position,
    m.match_id,
    m.match_date,
    m.match_type::text AS match_type,
    o.opponent_team_name AS opponent_team,
    m.goals_for,
    m.goals_against,
    pms.minutes_played,
    pms.goals,
    pms.assists,
    pms.shots,
    pms.shots_on_target,
    pms.key_passes,
    pms.pass_accuracy,
    pms.mistakes,
    pms.yellow_cards,
    pms.red_cards,
    pms.aerial_duels_won,
    pms.aerial_duels_total,
    pms.ground_duels_won,
    pms.ground_duels_total,
    mgs.total_distance,
    mgs.max_speed,
    mgs.sprint_count
FROM football.player_match_stats AS pms
JOIN football.matches AS m
    ON m.match_id = pms.match_id
JOIN football.opponent_teams AS o
    ON o.opponent_team_id = m.opponent_team_id
LEFT JOIN football.match_gps_stats AS mgs
    ON mgs.match_id = pms.match_id
   AND mgs.player_id = pms.player_id
"""


PHYSICAL_PROFILES_QUERY = """
SELECT
    player_id,
    created_at,
    weight_kg,
    body_fat_percentage,
    muscle_mass_kg
FROM football.physical_profiles
"""
