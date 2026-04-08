DO $$
BEGIN
    CREATE TYPE football.evaluation_trend_enum AS ENUM (
        '큰 하락',
        '하락',
        '보통',
        '발전',
        '많은 발전'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

ALTER TABLE football.evaluations
    ADD COLUMN IF NOT EXISTS evaluation_delta DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS evaluation_trend football.evaluation_trend_enum,
    ADD COLUMN IF NOT EXISTS evaluation_trend_code SMALLINT CHECK (evaluation_trend_code BETWEEN 1 AND 5),
    ADD COLUMN IF NOT EXISTS coach_comment_raw TEXT;

CREATE OR REPLACE FUNCTION football.refresh_evaluation_labels()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE football.evaluations AS evaluation
    SET
        evaluation_delta = scored.evaluation_delta,
        evaluation_trend = scored.evaluation_trend,
        evaluation_trend_code = scored.evaluation_trend_code,
        coach_comment_raw = scored.raw_comment,
        coach_comment = scored.standardized_comment
    FROM (
        WITH ordered AS (
            SELECT
                evaluation_id,
                player_id,
                evaluation_date,
                technical,
                tactical,
                physical,
                mental,
                COALESCE(coach_comment_raw, coach_comment) AS raw_comment,
                (technical + tactical + physical + mental) / 4.0 AS evaluation_average,
                LAG((technical + tactical + physical + mental) / 4.0)
                    OVER (PARTITION BY player_id ORDER BY evaluation_date, evaluation_id) AS previous_average,
                LAG(evaluation_id)
                    OVER (PARTITION BY player_id ORDER BY evaluation_date, evaluation_id) AS previous_evaluation_id,
                LAG(evaluation_date)
                    OVER (PARTITION BY player_id ORDER BY evaluation_date, evaluation_id) AS previous_evaluation_date
            FROM football.evaluations
        ),
        normalized AS (
            SELECT
                evaluation_id,
                player_id,
                evaluation_date,
                raw_comment,
                previous_evaluation_id,
                previous_evaluation_date,
                CASE
                    WHEN previous_average IS NULL THEN NULL
                    ELSE ROUND((evaluation_average - previous_average)::numeric, 2)::DOUBLE PRECISION
                END AS evaluation_delta,
                CASE
                    WHEN previous_average IS NULL THEN '보통'::football.evaluation_trend_enum
                    WHEN evaluation_average - previous_average <= -8 THEN '큰 하락'::football.evaluation_trend_enum
                    WHEN evaluation_average - previous_average <= -2 THEN '하락'::football.evaluation_trend_enum
                    WHEN evaluation_average - previous_average < 2 THEN '보통'::football.evaluation_trend_enum
                    WHEN evaluation_average - previous_average < 8 THEN '발전'::football.evaluation_trend_enum
                    ELSE '많은 발전'::football.evaluation_trend_enum
                END AS evaluation_trend,
                CASE
                    WHEN previous_average IS NULL THEN 3
                    WHEN evaluation_average - previous_average <= -8 THEN 1
                    WHEN evaluation_average - previous_average <= -2 THEN 2
                    WHEN evaluation_average - previous_average < 2 THEN 3
                    WHEN evaluation_average - previous_average < 8 THEN 4
                    ELSE 5
                END AS evaluation_trend_code
            FROM ordered
        ),
        match_summary AS (
            SELECT
                normalized.evaluation_id,
                COUNT(pms.match_player_id) FILTER (WHERE pms.match_player_id IS NOT NULL) AS match_count,
                CASE
                    WHEN COALESCE(SUM(COALESCE(pms.passes_attempted, 0)), 0) > 0 THEN
                        ROUND(
                            (
                                SUM(COALESCE(pms.passes_completed, 0))::NUMERIC
                                / SUM(COALESCE(pms.passes_attempted, 0))::NUMERIC
                            ) * 100,
                            1
                        )::DOUBLE PRECISION
                    ELSE NULL
                END AS pass_success_pct,
                CASE
                    WHEN COALESCE(
                        SUM(COALESCE(pms.aerial_duels_total, 0) + COALESCE(pms.ground_duels_total, 0)),
                        0
                    ) > 0 THEN
                        ROUND(
                            (
                                SUM(COALESCE(pms.aerial_duels_won, 0) + COALESCE(pms.ground_duels_won, 0))::NUMERIC
                                / SUM(COALESCE(pms.aerial_duels_total, 0) + COALESCE(pms.ground_duels_total, 0))::NUMERIC
                            ) * 100,
                            1
                        )::DOUBLE PRECISION
                    ELSE NULL
                END AS duel_win_pct,
                ROUND(COALESCE(AVG(pms.minutes_played), 0)::NUMERIC, 1)::DOUBLE PRECISION AS minutes_average,
                ROUND(
                    COALESCE(
                        AVG(
                            pms.minutes_played * 0.04
                            + pms.goals * 20
                            + pms.assists * 12
                            + pms.shots_on_target * 3
                            + pms.key_passes * 2
                            + COALESCE(pms.pass_accuracy, 0) * 100 * 0.01
                        ),
                        0
                    )::NUMERIC,
                    2
                )::DOUBLE PRECISION AS impact_score
            FROM normalized
            LEFT JOIN football.matches AS match_record
                ON (
                    normalized.previous_evaluation_date IS NULL
                    OR match_record.match_date > normalized.previous_evaluation_date
                )
               AND match_record.match_date <= normalized.evaluation_date
            LEFT JOIN football.player_match_stats AS pms
                ON pms.match_id = match_record.match_id
               AND pms.player_id = normalized.player_id
            GROUP BY normalized.evaluation_id
        ),
        paired AS (
            SELECT
                normalized.evaluation_id,
                normalized.raw_comment,
                normalized.evaluation_delta,
                normalized.evaluation_trend,
                normalized.evaluation_trend_code,
                COALESCE(current_summary.match_count, 0) AS match_count,
                current_summary.pass_success_pct,
                current_summary.duel_win_pct,
                COALESCE(current_summary.impact_score, 0) AS impact_score,
                COALESCE(current_summary.minutes_average, 0) AS minutes_average,
                previous_summary.pass_success_pct AS previous_pass_success_pct,
                previous_summary.duel_win_pct AS previous_duel_win_pct,
                COALESCE(previous_summary.impact_score, 0) AS previous_impact_score,
                COALESCE(previous_summary.minutes_average, 0) AS previous_minutes_average
            FROM normalized
            LEFT JOIN match_summary AS current_summary
                ON current_summary.evaluation_id = normalized.evaluation_id
            LEFT JOIN match_summary AS previous_summary
                ON previous_summary.evaluation_id = normalized.previous_evaluation_id
        ),
        deltas AS (
            SELECT
                evaluation_id,
                raw_comment,
                evaluation_delta,
                evaluation_trend,
                evaluation_trend_code,
                match_count,
                CASE
                    WHEN pass_success_pct IS NOT NULL AND previous_pass_success_pct IS NOT NULL THEN
                        ROUND((pass_success_pct - previous_pass_success_pct)::NUMERIC, 1)::DOUBLE PRECISION
                    ELSE NULL
                END AS pass_delta,
                CASE
                    WHEN duel_win_pct IS NOT NULL AND previous_duel_win_pct IS NOT NULL THEN
                        ROUND((duel_win_pct - previous_duel_win_pct)::NUMERIC, 1)::DOUBLE PRECISION
                    ELSE NULL
                END AS duel_delta,
                ROUND((impact_score - previous_impact_score)::NUMERIC, 2)::DOUBLE PRECISION AS impact_delta,
                ROUND((minutes_average - previous_minutes_average)::NUMERIC, 1)::DOUBLE PRECISION AS minutes_delta
            FROM paired
        ),
        signal_candidates AS (
            SELECT
                evaluation_id,
                evaluation_trend_code,
                1 AS priority,
                ABS(COALESCE(pass_delta, 0)) AS weight,
                CASE
                    WHEN pass_delta >= 1.5 THEN '최근 경기에서 패스 능력이 향상됐습니다.'
                    WHEN pass_delta <= -1.5 THEN '최근 경기에서 패스 정확도가 내려가 보완이 필요합니다.'
                    ELSE NULL
                END AS signal_text,
                CASE
                    WHEN pass_delta >= 1.5 THEN 'positive'
                    WHEN pass_delta <= -1.5 THEN 'negative'
                    ELSE NULL
                END AS signal_tone
            FROM deltas

            UNION ALL

            SELECT
                evaluation_id,
                evaluation_trend_code,
                2 AS priority,
                ABS(COALESCE(duel_delta, 0)) AS weight,
                CASE
                    WHEN duel_delta >= 4 THEN '경합 부분에서 발전이 보입니다.'
                    WHEN duel_delta <= -4 THEN '경합 장면 대응 보완이 필요합니다.'
                    ELSE NULL
                END AS signal_text,
                CASE
                    WHEN duel_delta >= 4 THEN 'positive'
                    WHEN duel_delta <= -4 THEN 'negative'
                    ELSE NULL
                END AS signal_tone
            FROM deltas

            UNION ALL

            SELECT
                evaluation_id,
                evaluation_trend_code,
                3 AS priority,
                ABS(impact_delta) AS weight,
                CASE
                    WHEN impact_delta >= 0.2 THEN '경기 영향력이 좋아졌습니다.'
                    WHEN impact_delta <= -0.2 THEN '경기 영향력이 줄어들었습니다.'
                    ELSE NULL
                END AS signal_text,
                CASE
                    WHEN impact_delta >= 0.2 THEN 'positive'
                    WHEN impact_delta <= -0.2 THEN 'negative'
                    ELSE NULL
                END AS signal_tone
            FROM deltas

            UNION ALL

            SELECT
                evaluation_id,
                evaluation_trend_code,
                4 AS priority,
                ABS(minutes_delta) AS weight,
                CASE
                    WHEN minutes_delta >= 12 THEN '출전 시간이 늘며 역할이 커졌습니다.'
                    WHEN minutes_delta <= -12 THEN '출전 시간이 줄어 역할 유지가 과제입니다.'
                    ELSE NULL
                END AS signal_text,
                CASE
                    WHEN minutes_delta >= 12 THEN 'positive'
                    WHEN minutes_delta <= -12 THEN 'negative'
                    ELSE NULL
                END AS signal_tone
            FROM deltas
        ),
        ranked_signals AS (
            SELECT
                evaluation_id,
                evaluation_trend_code,
                signal_text,
                ROW_NUMBER() OVER (PARTITION BY evaluation_id ORDER BY weight DESC, priority ASC) AS signal_rank
            FROM signal_candidates
            WHERE signal_text IS NOT NULL
              AND (
                  (evaluation_trend_code >= 4 AND signal_tone = 'positive')
                  OR (evaluation_trend_code <= 2 AND signal_tone = 'negative')
                  OR evaluation_trend_code = 3
              )
        ),
        selected_signals AS (
            SELECT
                evaluation_id,
                STRING_AGG(signal_text, ' ' ORDER BY signal_rank) AS summary_text
            FROM ranked_signals
            WHERE signal_rank <= CASE WHEN evaluation_trend_code = 3 THEN 1 ELSE 2 END
            GROUP BY evaluation_id
        )
        SELECT
            CASE
                WHEN deltas.evaluation_delta IS NULL THEN '보통. 첫 월간 평가입니다. 최근 경기 흐름을 기준선으로 잡습니다.'
                WHEN deltas.match_count = 0 THEN deltas.evaluation_trend::TEXT || '. 이달 경기 기록이 적어 코멘트는 제한적으로 남깁니다.'
                ELSE
                    deltas.evaluation_trend::TEXT
                    || '. '
                    || COALESCE(
                        selected_signals.summary_text,
                        CASE
                            WHEN deltas.evaluation_trend_code >= 4 THEN '최근 경기 흐름이 전월보다 좋아졌습니다.'
                            WHEN deltas.evaluation_trend_code <= 2 THEN '최근 경기에서 보완이 필요한 흐름이 보입니다.'
                            ELSE '최근 경기 흐름은 전월과 비슷합니다.'
                        END
                    )
            END AS standardized_comment,
            deltas.evaluation_id,
            deltas.raw_comment,
            deltas.evaluation_delta,
            deltas.evaluation_trend,
            deltas.evaluation_trend_code
        FROM deltas
        LEFT JOIN selected_signals
            ON selected_signals.evaluation_id = deltas.evaluation_id
    ) AS scored
    WHERE evaluation.evaluation_id = scored.evaluation_id;
END;
$$;

SELECT football.refresh_evaluation_labels();
