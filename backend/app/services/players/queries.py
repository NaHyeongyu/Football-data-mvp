from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd
from psycopg import sql

from ...db import get_connection


PLAYER_BASE_CTES = """
WITH match_summary AS (
    SELECT
        pms.player_id,
        COUNT(*)::int AS appearances,
        COALESCE(SUM(pms.minutes_played), 0)::int AS total_minutes,
        COALESCE(SUM(pms.goals), 0)::int AS total_goals,
        COALESCE(SUM(pms.assists), 0)::int AS total_assists,
        MAX(m.match_date) AS latest_match_date
    FROM football.player_match_stats AS pms
    JOIN football.matches AS m
        ON m.match_id = pms.match_id
    GROUP BY pms.player_id
),
recent_form AS (
    SELECT
        ranked.player_id,
        ROUND(AVG(ranked.form_score)::numeric, 2)::double precision AS recent_form_score
    FROM (
        SELECT
            pms.player_id,
            ROW_NUMBER() OVER (
                PARTITION BY pms.player_id
                ORDER BY m.match_date DESC, pms.match_player_id DESC
            ) AS row_number,
            (
                COALESCE(pms.minutes_played, 0) * 0.04 +
                COALESCE(pms.goals, 0) * 20 +
                COALESCE(pms.assists, 0) * 12 +
                COALESCE(pms.shots_on_target, 0) * 3 +
                COALESCE(pms.key_passes, 0) * 2 +
                COALESCE(pms.pass_accuracy, 0) * 10
            ) AS form_score
        FROM football.player_match_stats AS pms
        JOIN football.matches AS m
            ON m.match_id = pms.match_id
    ) AS ranked
    WHERE ranked.row_number <= 5
    GROUP BY ranked.player_id
)
"""


PLAYER_SELECT = """
SELECT
    p.player_id,
    p.name,
    p.jersey_number,
    p.date_of_birth,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.date_of_birth))::int AS age,
    p.primary_position::text AS primary_position,
    p.secondary_position::text AS secondary_position,
    p.foot::text AS foot,
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
    lp.created_at AS physical_measured_at,
    cis.injury_id,
    cis.injury_date,
    cis.injury_type,
    cis.injury_part,
    cis.severity_level::text AS severity_level,
    cis.injury_status::text AS injury_status,
    cis.expected_return_date,
    cis.actual_return_date,
    cis.occurred_during::text AS occurred_during,
    COALESCE(ms.appearances, 0) AS appearances,
    COALESCE(ms.total_minutes, 0) AS total_minutes,
    COALESCE(ms.total_goals, 0) AS total_goals,
    COALESCE(ms.total_assists, 0) AS total_assists,
    rf.recent_form_score,
    ms.latest_match_date
FROM football.players AS p
LEFT JOIN football.player_latest_physical_profile AS lp
    ON lp.player_id = p.player_id
LEFT JOIN football.player_current_injury_status AS cis
    ON cis.player_id = p.player_id
LEFT JOIN match_summary AS ms
    ON ms.player_id = p.player_id
LEFT JOIN recent_form AS rf
    ON rf.player_id = p.player_id
"""


ROSTER_POSITIONS_SQL = """
SELECT
    player_id,
    primary_position::text AS primary_position
FROM football.players
"""


RECENT_MATCHES_SQL = """
WITH ranked AS (
    SELECT
        pms.match_player_id,
        pms.player_id,
        m.match_id,
        m.match_date,
        m.match_type::text AS match_type,
        o.opponent_team_name AS opponent_team,
        s.stadium_name AS stadium,
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
        mgs.sprint_count,
        ROW_NUMBER() OVER (
            PARTITION BY pms.player_id
            ORDER BY m.match_date DESC, pms.match_player_id DESC
        ) AS row_number
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
    WHERE pms.player_id = %s
)
SELECT
    match_player_id,
    player_id,
    match_id,
    match_date,
    match_type,
    opponent_team,
    stadium,
    minutes_played,
    goals,
    assists,
    shots,
    shots_on_target,
    key_passes,
    pass_accuracy,
    mistakes,
    yellow_cards,
    red_cards,
    aerial_duels_won,
    aerial_duels_total,
    ground_duels_won,
    ground_duels_total,
    total_distance,
    max_speed,
    sprint_count
FROM ranked
WHERE row_number <= %s
ORDER BY match_date DESC, match_player_id DESC
"""


FORM_MATCHES_BY_PLAYERS_SQL = """
WITH ranked AS (
    SELECT
        pms.match_player_id,
        pms.player_id,
        m.match_id,
        m.match_date,
        m.match_type::text AS match_type,
        o.opponent_team_name AS opponent_team,
        s.stadium_name AS stadium,
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
        mgs.sprint_count,
        ROW_NUMBER() OVER (
            PARTITION BY pms.player_id
            ORDER BY m.match_date DESC, pms.match_player_id DESC
        ) AS row_number
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
    WHERE pms.player_id = ANY(%s)
)
SELECT
    match_player_id,
    player_id,
    match_id,
    match_date,
    match_type,
    opponent_team,
    stadium,
    minutes_played,
    goals,
    assists,
    shots,
    shots_on_target,
    key_passes,
    pass_accuracy,
    mistakes,
    yellow_cards,
    red_cards,
    aerial_duels_won,
    aerial_duels_total,
    ground_duels_won,
    ground_duels_total,
    total_distance,
    max_speed,
    sprint_count
FROM ranked
WHERE row_number <= %s
ORDER BY player_id, match_date DESC, match_player_id DESC
"""


def _build_player_filters(
    q: str | None,
    position: str | None,
    status: str | None,
) -> tuple[sql.SQL, list[Any]]:
    conditions: list[sql.Composable] = []
    params: list[Any] = []

    if q:
        conditions.append(
            sql.SQL(
                "(p.name ILIKE %s OR p.player_id ILIKE %s OR COALESCE(p.previous_team, '') ILIKE %s)"
            )
        )
        wildcard = f"%{q.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    if position:
        conditions.append(sql.SQL("(p.primary_position::text = %s OR p.secondary_position::text = %s)"))
        params.extend([position, position])

    if status:
        conditions.append(sql.SQL("p.status::text = %s"))
        params.append(status)

    if not conditions:
        return sql.SQL(""), params

    return sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions), params


def _fetch_form_match_frame(player_ids: Sequence[str], matches_per_player: int = 10) -> pd.DataFrame:
    if not player_ids:
        return pd.DataFrame()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(FORM_MATCHES_BY_PLAYERS_SQL, [list(player_ids), matches_per_player])
            rows = cursor.fetchall()

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _fetch_roster_positions() -> pd.DataFrame:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(ROSTER_POSITIONS_SQL)
            rows = cursor.fetchall()
    if not rows:
        return pd.DataFrame(columns=["player_id", "primary_position"])
    return pd.DataFrame(rows)
