from __future__ import annotations


MATCH_META_QUERY = """
SELECT
    m.match_id,
    m.match_date,
    m.match_type::text AS match_type,
    o.opponent_team_name AS opponent_team,
    s.stadium_name,
    m.goals_for,
    m.goals_against,
    m.possession_for,
    m.possession_against,
    mts.assists,
    mts.shots,
    mts.shots_on_target,
    mts.key_passes,
    mts.pass_accuracy,
    mts.crosses_attempted,
    mts.crosses_succeeded,
    mts.cross_accuracy,
    mts.duels_won,
    mts.duels_total,
    mts.interceptions,
    mts.recoveries,
    mts.mistakes
FROM football.matches AS m
JOIN football.opponent_teams AS o
    ON o.opponent_team_id = m.opponent_team_id
JOIN football.stadiums AS s
    ON s.stadium_id = m.stadium_id
LEFT JOIN football.match_team_stats AS mts
    ON mts.match_id = m.match_id
WHERE m.match_id = %s
  AND m.match_date <= %s
"""


MATCH_PLAYERS_QUERY = """
SELECT
    pms.match_player_id,
    pms.match_id,
    m.match_date,
    pms.player_id,
    p.name,
    p.jersey_number,
    pms.position::text AS position,
    pms.start_position::text AS start_position,
    pms.substitute_in,
    pms.substitute_out,
    pms.minutes_played,
    pms.goals,
    pms.assists,
    pms.shots,
    pms.shots_on_target,
    pms.key_passes,
    pms.pass_accuracy,
    pms.recoveries,
    pms.interceptions,
    pms.mistakes,
    pms.yellow_cards,
    pms.red_cards,
    pms.aerial_duels_won,
    pms.aerial_duels_total,
    pms.ground_duels_won,
    pms.ground_duels_total,
    mgs.total_distance,
    mgs.play_time_min,
    mgs.avg_speed,
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
    mgs.max_speed,
    mgs.accel_count,
    mgs.decel_count,
    mgs.hi_accel_count,
    mgs.hi_decel_count
FROM football.player_match_stats AS pms
JOIN football.players AS p
    ON p.player_id = pms.player_id
LEFT JOIN football.match_gps_stats AS mgs
    ON mgs.match_id = pms.match_id
   AND mgs.player_id = pms.player_id
JOIN football.matches AS m
    ON m.match_id = pms.match_id
WHERE pms.match_id = %s
  AND m.match_date <= %s
"""
