from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ...db import get_connection
from ..injury_risk import build_player_injury_risk_report


@dataclass(frozen=True)
class StructuredEvidence:
    tool: str
    title: str
    reason: str
    rows: list[dict[str, object | None]]


def collect_structured_evidence(question: str) -> list[StructuredEvidence]:
    normalized = _normalize_question(question)
    players = resolve_players_from_question(question)
    evidence: list[StructuredEvidence] = [fetch_dataset_snapshot()]

    if players:
        for player_id, player_name in players[:2]:
            evidence.append(fetch_player_profile(player_id=player_id, player_name=player_name))
            if _contains_any(normalized, ("경기", "폼", "활동량", "match", "출전", "최근")):
                evidence.append(fetch_player_recent_matches(player_id=player_id, player_name=player_name))
            if _contains_any(normalized, ("훈련", "부하", "workload", "load", "training")):
                evidence.append(fetch_player_recent_trainings(player_id=player_id, player_name=player_name))
            if _contains_any(normalized, ("부상", "재활", "복귀", "위험", "injury")):
                evidence.append(fetch_player_injury_history(player_id=player_id, player_name=player_name))
        return [item for item in evidence if item.rows]

    if _contains_any(normalized, ("부상위험", "부상 위험", "위험도", "injury risk", "risk")):
        risk_evidence = fetch_injury_risk_leaders()
        if risk_evidence.rows:
            evidence.append(risk_evidence)

    if _contains_any(normalized, ("부상", "재활", "복귀", "injury")):
        injury_evidence = fetch_current_injury_watch()
        if injury_evidence.rows:
            evidence.append(injury_evidence)

    if _contains_any(normalized, ("훈련", "부하", "workload", "load", "training")):
        training_evidence = fetch_training_load_leaders()
        if training_evidence.rows:
            evidence.append(training_evidence)

    if _contains_any(normalized, ("경기", "폼", "활동량", "match", "최근", "선수 추천")):
        form_evidence = fetch_recent_match_form_leaders()
        if form_evidence.rows:
            evidence.append(form_evidence)

    if _contains_any(normalized, ("평가", "상담", "멘탈", "evaluation", "counseling")):
        evaluation_evidence = fetch_latest_evaluation_leaders()
        if evaluation_evidence.rows:
            evidence.append(evaluation_evidence)

    return [item for item in evidence if item.rows]


def resolve_players_from_question(question: str, *, limit: int = 2) -> list[tuple[str, str]]:
    query = """
        SELECT player_id, name
        FROM football.players
        ORDER BY LENGTH(name) DESC, name
    """
    normalized = question.casefold()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    resolved: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        name = str(row["name"])
        if name.casefold() in normalized and name not in seen:
            resolved.append((str(row["player_id"]), name))
            seen.add(name)
        if len(resolved) >= limit:
            break
    return resolved


def fetch_dataset_snapshot() -> StructuredEvidence:
    query = """
        SELECT
            (SELECT COUNT(*) FROM football.players)::int AS player_count,
            (SELECT COUNT(*) FROM football.matches)::int AS match_count,
            (SELECT MAX(match_date) FROM football.matches) AS latest_match_date,
            (SELECT COUNT(*) FROM football.trainings)::int AS training_count,
            (SELECT MAX(training_date) FROM football.trainings) AS latest_training_date,
            (SELECT COUNT(*) FROM football.injuries)::int AS injury_count,
            (SELECT COUNT(*) FROM football.evaluations)::int AS evaluation_count,
            (SELECT COUNT(*) FROM football.counseling_notes)::int AS counseling_count
    """
    return StructuredEvidence(
        tool="dataset_snapshot",
        title="데이터셋 스냅샷",
        reason="질문 답변의 기준 날짜와 데이터 범위를 확인합니다.",
        rows=_fetch_rows(query),
    )


def fetch_player_profile(*, player_id: str, player_name: str) -> StructuredEvidence:
    query = """
        SELECT
            p.player_id,
            p.name,
            p.jersey_number,
            p.primary_position::text AS primary_position,
            p.secondary_position::text AS secondary_position,
            p.foot::text AS foot,
            p.nationality,
            p.status::text AS status,
            p.previous_team,
            lp.height_cm,
            lp.weight_kg,
            lp.body_fat_percentage,
            lp.bmi,
            lp.muscle_mass_kg,
            lp.created_at AS physical_measured_at,
            cis.injury_date,
            cis.injury_type,
            cis.injury_part,
            cis.injury_status::text AS injury_status,
            cis.expected_return_date,
            latest_evaluation.evaluation_date,
            latest_evaluation.technical,
            latest_evaluation.tactical,
            latest_evaluation.physical,
            latest_evaluation.mental,
            latest_evaluation.coach_comment,
            latest_counseling.counseling_date,
            latest_counseling.topic::text AS counseling_topic,
            latest_counseling.summary AS counseling_summary
        FROM football.players AS p
        LEFT JOIN football.player_latest_physical_profile AS lp
            ON lp.player_id = p.player_id
        LEFT JOIN football.player_current_injury_status AS cis
            ON cis.player_id = p.player_id
        LEFT JOIN LATERAL (
            SELECT evaluation_date, technical, tactical, physical, mental, coach_comment
            FROM football.evaluations
            WHERE player_id = p.player_id
            ORDER BY evaluation_date DESC, evaluation_id DESC
            LIMIT 1
        ) AS latest_evaluation
            ON TRUE
        LEFT JOIN LATERAL (
            SELECT counseling_date, topic, summary
            FROM football.counseling_notes
            WHERE player_id = p.player_id
            ORDER BY counseling_date DESC, counseling_id DESC
            LIMIT 1
        ) AS latest_counseling
            ON TRUE
        WHERE p.player_id = %s
    """
    return StructuredEvidence(
        tool="get_player_profile",
        title=f"{player_name} 프로필",
        reason="질문에 특정 선수가 포함되어 기본 프로필, 최신 피지컬, 부상, 평가, 상담 정보를 조회합니다.",
        rows=_fetch_rows(query, [player_id]),
    )


def fetch_player_recent_matches(*, player_id: str, player_name: str) -> StructuredEvidence:
    query = """
        SELECT
            match_date,
            match_type,
            opponent_team,
            minutes_played,
            goals,
            assists,
            shots,
            pass_accuracy,
            total_distance,
            sprint_count,
            max_speed
        FROM football.player_match_facts
        WHERE player_id = %s
        ORDER BY match_date DESC, match_player_id DESC
        LIMIT 5
    """
    return StructuredEvidence(
        tool="get_player_recent_matches",
        title=f"{player_name} 최근 경기",
        reason="선수의 최근 경기 흐름과 활동량을 확인합니다.",
        rows=_fetch_rows(query, [player_id]),
    )


def fetch_player_recent_trainings(*, player_id: str, player_name: str) -> StructuredEvidence:
    query = """
        SELECT
            t.training_date,
            t.session_name::text AS session_name,
            t.training_focus::text AS training_focus,
            t.intensity_level::text AS intensity_level,
            tgs.total_distance,
            tgs.play_time_min,
            tgs.sprint_count,
            tgs.accel_count,
            tgs.decel_count,
            tgs.max_speed
        FROM football.training_gps_stats AS tgs
        JOIN football.trainings AS t
            ON t.training_id = tgs.training_id
        WHERE tgs.player_id = %s
        ORDER BY t.training_date DESC, t.training_id DESC
        LIMIT 5
    """
    return StructuredEvidence(
        tool="get_player_recent_trainings",
        title=f"{player_name} 최근 훈련",
        reason="선수의 최근 훈련 부하와 세션 강도를 확인합니다.",
        rows=_fetch_rows(query, [player_id]),
    )


def fetch_player_injury_history(*, player_id: str, player_name: str) -> StructuredEvidence:
    query = """
        SELECT
            injury_date,
            injury_type,
            injury_part,
            severity_level::text AS severity_level,
            status::text AS injury_status,
            expected_return_date,
            actual_return_date,
            injury_mechanism,
            occurred_during::text AS occurred_during,
            notes
        FROM football.injuries
        WHERE player_id = %s
        ORDER BY injury_date DESC, injury_id DESC
        LIMIT 5
    """
    return StructuredEvidence(
        tool="get_player_injury_history",
        title=f"{player_name} 부상 이력",
        reason="부상/재활/복귀 관련 질문이라 선수의 부상 기록과 원인 메모를 조회합니다.",
        rows=_fetch_rows(query, [player_id]),
    )


def fetch_current_injury_watch() -> StructuredEvidence:
    query = """
        SELECT
            p.name,
            p.primary_position::text AS primary_position,
            cis.injury_date,
            cis.injury_type,
            cis.injury_part,
            cis.injury_status::text AS injury_status,
            cis.expected_return_date
        FROM football.player_current_injury_status AS cis
        JOIN football.players AS p
            ON p.player_id = cis.player_id
        WHERE cis.injury_id IS NOT NULL
          AND (cis.actual_return_date IS NULL OR cis.injury_status::text = 'rehab' OR p.status::text = 'injured')
        ORDER BY cis.expected_return_date ASC NULLS LAST, cis.injury_date DESC
        LIMIT 10
    """
    return StructuredEvidence(
        tool="get_current_injury_watch",
        title="현재 부상/재활 현황",
        reason="팀 단위 부상, 재활, 복귀 가능성을 확인합니다.",
        rows=_fetch_rows(query),
    )


def fetch_injury_risk_leaders() -> StructuredEvidence:
    report = build_player_injury_risk_report(limit=5, risk_band=None)
    rows = [
        _json_safe(
            {
                "snapshot_date": item.snapshot_date,
                "player_id": item.player_id,
                "name": item.name,
                "primary_position": item.primary_position,
                "status": item.status,
                "overall_risk_score": item.overall_risk_score,
                "risk_band": item.risk_band,
                "reasons": item.reasons,
                "acute_load_7d": item.factors.acute_load_7d,
                "acute_chronic_ratio": item.factors.acute_chronic_ratio,
                "sprint_ratio": item.factors.sprint_ratio,
            }
        )
        for item in report.items[:5]
    ]
    return StructuredEvidence(
        tool="get_injury_risk_leaders",
        title="부상 위험도 상위 선수",
        reason="부상 위험도 모델 결과를 조회합니다.",
        rows=rows,
    )


def fetch_training_load_leaders() -> StructuredEvidence:
    query = """
        WITH anchor AS (
            SELECT MAX(training_date) AS latest_training_date
            FROM football.trainings
        )
        SELECT
            p.name,
            p.primary_position::text AS primary_position,
            MAX(t.training_date) AS latest_training_date,
            COUNT(*)::int AS recent_sessions,
            ROUND(AVG(tgs.total_distance)::numeric, 2)::double precision AS avg_total_distance,
            ROUND(AVG(tgs.sprint_count)::numeric, 2)::double precision AS avg_sprint_count,
            ROUND(AVG(tgs.max_speed)::numeric, 2)::double precision AS avg_max_speed,
            SUM(CASE WHEN t.intensity_level::text = 'high' THEN 1 ELSE 0 END)::int AS high_sessions
        FROM football.training_gps_stats AS tgs
        JOIN football.trainings AS t
            ON t.training_id = tgs.training_id
        JOIN football.players AS p
            ON p.player_id = tgs.player_id
        CROSS JOIN anchor AS a
        WHERE t.training_date >= a.latest_training_date - INTERVAL '14 days'
        GROUP BY p.player_id, p.name, p.primary_position
        ORDER BY avg_total_distance DESC NULLS LAST, avg_sprint_count DESC NULLS LAST
        LIMIT 5
    """
    return StructuredEvidence(
        tool="get_training_load_leaders",
        title="최근 14일 훈련 부하 상위",
        reason="훈련량/부하 관련 질문이라 최근 14일 훈련 GPS 상위 선수를 조회합니다.",
        rows=_fetch_rows(query),
    )


def fetch_recent_match_form_leaders() -> StructuredEvidence:
    query = """
        WITH anchor AS (
            SELECT MAX(match_date) AS latest_match_date
            FROM football.matches
        )
        SELECT
            pmf.player_name AS name,
            p.primary_position::text AS primary_position,
            MAX(pmf.match_date) AS latest_match_date,
            COUNT(*)::int AS recent_matches,
            ROUND(AVG(pmf.minutes_played)::numeric, 2)::double precision AS avg_minutes,
            ROUND(AVG(pmf.total_distance)::numeric, 2)::double precision AS avg_total_distance,
            ROUND(AVG(pmf.sprint_count)::numeric, 2)::double precision AS avg_sprint_count,
            SUM(pmf.goals)::int AS goals,
            SUM(pmf.assists)::int AS assists
        FROM football.player_match_facts AS pmf
        JOIN football.players AS p
            ON p.player_id = pmf.player_id
        CROSS JOIN anchor AS a
        WHERE pmf.match_date >= a.latest_match_date - INTERVAL '21 days'
        GROUP BY pmf.player_id, pmf.player_name, p.primary_position
        ORDER BY recent_matches DESC, avg_total_distance DESC NULLS LAST, avg_sprint_count DESC NULLS LAST
        LIMIT 5
    """
    return StructuredEvidence(
        tool="get_recent_match_form_leaders",
        title="최근 21일 경기 폼 상위",
        reason="최근 경기 폼과 활동량 상위 선수를 조회합니다.",
        rows=_fetch_rows(query),
    )


def fetch_latest_evaluation_leaders() -> StructuredEvidence:
    query = """
        WITH latest AS (
            SELECT DISTINCT ON (e.player_id)
                e.player_id,
                e.evaluation_date,
                e.technical,
                e.tactical,
                e.physical,
                e.mental,
                e.coach_comment
            FROM football.evaluations AS e
            ORDER BY e.player_id, e.evaluation_date DESC, e.evaluation_id DESC
        )
        SELECT
            p.name,
            p.primary_position::text AS primary_position,
            latest.evaluation_date,
            ROUND(((latest.technical + latest.tactical + latest.physical + latest.mental) / 4.0)::numeric, 2)::double precision AS average_score,
            latest.technical,
            latest.tactical,
            latest.physical,
            latest.mental,
            latest.coach_comment
        FROM latest
        JOIN football.players AS p
            ON p.player_id = latest.player_id
        ORDER BY average_score DESC
        LIMIT 5
    """
    return StructuredEvidence(
        tool="get_latest_evaluation_leaders",
        title="최신 평가 상위 선수",
        reason="평가/상담 관련 질문이라 최신 코치 평가 데이터를 조회합니다.",
        rows=_fetch_rows(query),
    )


def _fetch_rows(query: str, params: list[object] | None = None) -> list[dict[str, object | None]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or [])
            rows = cursor.fetchall()
    return [_json_safe(dict(row)) for row in rows]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _normalize_question(question: str) -> str:
    return question.strip().casefold().replace(" ", "")


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    normalized_terms = tuple(term.casefold().replace(" ", "") for term in terms)
    return any(term in value for term in normalized_terms)
