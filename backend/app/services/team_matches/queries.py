from __future__ import annotations


TEAM_MATCHES_LIST_QUERY = """
SELECT
    pms.match_player_id,
    pms.player_id,
    pms.position::text AS position,
    m.match_id,
    m.match_date,
    m.match_type::text AS match_type,
    o.opponent_team_name AS opponent_team,
    s.stadium_name AS stadium_name,
    m.goals_for,
    m.goals_against,
    m.possession_for,
    m.possession_against,
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
JOIN football.stadiums AS s
    ON s.stadium_id = m.stadium_id
LEFT JOIN football.match_gps_stats AS mgs
    ON mgs.match_id = pms.match_id
   AND mgs.player_id = pms.player_id
WHERE m.match_date <= %s
"""
