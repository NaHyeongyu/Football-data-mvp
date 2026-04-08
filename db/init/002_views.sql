DROP VIEW IF EXISTS football.player_match_facts;
DROP VIEW IF EXISTS football.player_current_injury_status;
DROP VIEW IF EXISTS football.player_latest_physical_profile;

CREATE OR REPLACE VIEW football.player_latest_physical_profile AS
SELECT DISTINCT ON (pp.player_id)
    pp.player_id,
    p.name,
    pp.physical_data_id,
    pp.height_cm,
    pp.weight_kg,
    pp.body_fat_percentage,
    pp.bmi,
    pp.muscle_mass_kg,
    pp.created_at
FROM football.physical_profiles AS pp
JOIN football.players AS p
    ON p.player_id = pp.player_id
ORDER BY pp.player_id, pp.created_at DESC;


CREATE OR REPLACE VIEW football.player_current_injury_status AS
SELECT
    p.player_id,
    p.name,
    p.status AS roster_status,
    latest.injury_id,
    latest.injury_date,
    latest.injury_type,
    latest.injury_part,
    latest.severity_level,
    latest.status AS injury_status,
    latest.expected_return_date,
    latest.actual_return_date,
    latest.occurred_during
FROM football.players AS p
LEFT JOIN LATERAL (
    SELECT
        i.injury_id,
        i.injury_date,
        i.injury_type,
        i.injury_part,
        i.severity_level,
        i.status,
        i.expected_return_date,
        i.actual_return_date,
        i.occurred_during
    FROM football.injuries AS i
    WHERE i.player_id = p.player_id
    ORDER BY i.injury_date DESC, i.created_at DESC NULLS LAST
    LIMIT 1
) AS latest
    ON TRUE;


CREATE OR REPLACE VIEW football.player_match_facts AS
SELECT
    pms.match_player_id,
    m.match_id,
    m.match_date,
    m.match_type,
    o.opponent_team_name AS opponent_team,
    s.stadium_name AS stadium,
    p.player_id,
    p.name AS player_name,
    pms.position,
    pms.minutes_played,
    pms.goals,
    pms.assists,
    pms.shots,
    pms.pass_accuracy,
    pms.cross_accuracy,
    mgs.total_distance,
    mgs.max_speed,
    mgs.sprint_count
FROM football.player_match_stats AS pms
JOIN football.matches AS m
    ON m.match_id = pms.match_id
JOIN football.players AS p
    ON p.player_id = pms.player_id
JOIN football.opponent_teams AS o
    ON o.opponent_team_id = m.opponent_team_id
JOIN football.stadiums AS s
    ON s.stadium_id = m.stadium_id
LEFT JOIN football.match_gps_stats AS mgs
    ON mgs.match_id = pms.match_id
   AND mgs.player_id = pms.player_id;
