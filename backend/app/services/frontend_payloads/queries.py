from __future__ import annotations


TEAM_NAME = "전북현대 U18"
FRONTEND_MIN_SEASON_YEAR = 2023
FRONTEND_MAX_SEASON_YEAR = 2025

PLAYERS_QUERY = """
SELECT
    p.player_id,
    p.name,
    p.date_of_birth,
    p.jersey_number,
    p.primary_position::text AS primary_position,
    p.secondary_position::text AS secondary_position,
    p.foot,
    p.nationality,
    p.status::text AS status,
    p.profile_image_url,
    p.joined_at,
    p.previous_team,
    p.updated_at,
    lp.height_cm,
    lp.weight_kg,
    lp.body_fat_percentage,
    lp.bmi,
    lp.muscle_mass_kg,
    lp.created_at AS physical_measured_at
FROM football.players AS p
LEFT JOIN football.player_latest_physical_profile AS lp
    ON lp.player_id = p.player_id
ORDER BY p.jersey_number NULLS LAST, p.name
"""

CURRENT_INJURY_QUERY = """
SELECT
    player_id,
    injury_id,
    injury_date,
    injury_type,
    injury_part,
    severity_level::text AS severity_level,
    injury_status::text AS injury_status,
    expected_return_date,
    actual_return_date,
    occurred_during
FROM football.player_current_injury_status
"""

INJURY_HISTORY_QUERY = """
SELECT
    injury_id,
    player_id,
    injury_date,
    injury_type,
    injury_part,
    severity_level::text AS severity_level,
    status::text AS injury_status,
    expected_return_date,
    actual_return_date,
    occurred_during,
    notes
FROM football.injuries
WHERE injury_date <= %s
ORDER BY injury_date DESC, injury_id DESC
"""

MATCH_LOG_QUERY = """
SELECT
    pms.match_player_id,
    pms.match_id,
    pms.player_id,
    p.name AS player_name,
    p.date_of_birth,
    p.primary_position::text AS registered_position,
    p.secondary_position::text AS secondary_position,
    p.foot,
    p.status::text AS roster_status,
    m.match_date,
    m.match_type::text AS match_type,
    o.opponent_team_name AS opponent_team,
    s.stadium_name,
    m.goals_for,
    m.goals_against,
    pms.position::text AS position_played,
    pms.start_position::text AS start_position,
    pms.substitute_in,
    pms.substitute_out,
    pms.minutes_played,
    pms.goals,
    pms.assists,
    pms.shots,
    pms.shots_on_target,
    pms.key_passes,
    pms.passes_attempted,
    pms.passes_completed,
    pms.pass_accuracy,
    pms.take_ons_attempted,
    pms.take_ons_succeeded,
    pms.tackles_succeeded,
    pms.interceptions,
    pms.clearances,
    pms.saves,
    pms.mistakes,
    pms.yellow_cards,
    pms.red_cards,
    pms.aerial_duels_total,
    pms.aerial_duels_won,
    pms.aerial_duels_lost,
    pms.ground_duels_total,
    pms.ground_duels_won,
    pms.ground_duels_lost,
    mgs.match_gps_id,
    mgs.total_distance,
    mgs.play_time_min,
    mgs.avg_speed,
    mgs.max_speed,
    mgs.distance_0_15_min,
    mgs.distance_15_30_min,
    mgs.distance_30_45_min,
    mgs.distance_45_60_min,
    mgs.distance_60_75_min,
    mgs.distance_75_90_min,
    mgs.sprint_count,
    mgs.sprint_distance,
    mgs.distance_speed_0_5,
    mgs.distance_speed_5_10,
    mgs.distance_speed_10_15,
    mgs.distance_speed_15_20,
    mgs.distance_speed_20_25,
    mgs.distance_speed_25_plus,
    mgs.cod_count,
    mgs.accel_count,
    mgs.decel_count,
    mgs.hi_accel_count,
    mgs.hi_decel_count
FROM football.player_match_stats AS pms
JOIN football.players AS p
    ON p.player_id = pms.player_id
JOIN football.matches AS m
    ON m.match_id = pms.match_id
JOIN football.opponent_teams AS o
    ON o.opponent_team_id = m.opponent_team_id
JOIN football.stadiums AS s
    ON s.stadium_id = m.stadium_id
LEFT JOIN football.match_gps_stats AS mgs
    ON mgs.match_id = pms.match_id
   AND mgs.player_id = pms.player_id
WHERE m.match_date <= %s
ORDER BY m.match_date DESC, pms.match_player_id DESC
"""

PHYSICAL_TESTS_QUERY = """
SELECT
    pt.physical_test_id,
    pt.player_id,
    p.name AS player_name,
    p.primary_position::text AS registered_position,
    pt.test_date,
    pt.sprint_10m,
    pt.sprint_30m,
    pt.sprint_50m,
    pt.sprint_100m,
    pt.vertical_jump_cm,
    pt.agility_t_test_sec,
    pt.agility_shuttle_run_sec,
    profile.height_cm,
    profile.weight_kg,
    profile.body_fat_percentage,
    profile.muscle_mass_kg
FROM football.physical_tests AS pt
JOIN football.players AS p
    ON p.player_id = pt.player_id
LEFT JOIN LATERAL (
    SELECT
        pp.height_cm,
        pp.weight_kg,
        pp.body_fat_percentage,
        pp.muscle_mass_kg
    FROM football.physical_profiles AS pp
    WHERE pp.player_id = pt.player_id
      AND pp.created_at::date <= pt.test_date
    ORDER BY pp.created_at DESC, pp.physical_data_id DESC
    LIMIT 1
) AS profile
    ON TRUE
WHERE pt.test_date <= %s
ORDER BY pt.test_date DESC, pt.physical_test_id DESC
"""

COUNSELING_QUERY = """
SELECT
    counseling_id,
    player_id,
    counseling_date,
    topic,
    summary
FROM football.counseling_notes
WHERE counseling_date <= %s
ORDER BY counseling_date DESC, counseling_id DESC
"""

__all__ = [
    "COUNSELING_QUERY",
    "CURRENT_INJURY_QUERY",
    "FRONTEND_MAX_SEASON_YEAR",
    "FRONTEND_MIN_SEASON_YEAR",
    "INJURY_HISTORY_QUERY",
    "MATCH_LOG_QUERY",
    "PHYSICAL_TESTS_QUERY",
    "PLAYERS_QUERY",
    "TEAM_NAME",
]
