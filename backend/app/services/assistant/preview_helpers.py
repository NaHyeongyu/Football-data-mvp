from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from ...schemas import AssistantQueryStep
from .answer_formatters import (
    _display_date,
    _format_activity_leader_answer,
    _format_number,
    _format_percent_detail,
)


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _build_playbook_answer(
    *,
    question: str,
    active_playbooks: set[str],
    sql_query: str,
    row_count: int | None,
    preview: Sequence[dict[str, object | None]],
) -> str | None:
    del question
    if not (
        "latest_match_activity_leader" in active_playbooks
        or "latest_official_match_activity_leader" in active_playbooks
    ):
        return None
    if not preview:
        return None

    lowered_query = sql_query.lower()
    if not any(marker in lowered_query for marker in ("match_date", "latest_match", "latest_official_match", "football.matches")):
        return None
    if row_count != 1:
        return None
    if "order by" not in lowered_query or "limit 1" not in lowered_query:
        return None
    if "latest_official_match_activity_leader" in active_playbooks and not (
        "match_type = '공식'" in sql_query or 'match_type = "공식"' in sql_query
    ):
        return None

    top_row = preview[0]
    if not isinstance(top_row, Mapping):
        return None

    player_name = _normalize_optional_text(top_row.get("player_name") or top_row.get("name"))
    if not player_name:
        return None

    match_label = (
        "가장 최근 공식 경기"
        if "latest_official_match_activity_leader" in active_playbooks
        else "가장 최근 경기"
    )
    return _format_activity_leader_answer(
        top_row=top_row,
        match_label=match_label,
    )


def _build_fallback_answer_from_preview(
    steps: Sequence[AssistantQueryStep],
) -> str | None:
    best_step = _select_best_preview_step(steps)
    if not best_step or not best_step.preview:
        return None

    top_row = best_step.preview[0]
    if not isinstance(top_row, Mapping):
        return None

    player_name = _normalize_optional_text(top_row.get("player_name") or top_row.get("name"))
    if not player_name:
        return _build_generic_preview_answer(best_step)
    if any(key in top_row for key in ("total_distance", "sprint_count", "minutes_played")):
        return _format_activity_leader_answer(
            top_row=top_row,
            match_label="가장 최근 경기",
        )
    return _build_generic_preview_answer(best_step)


def _should_prefer_preview_fallback(
    steps: Sequence[AssistantQueryStep],
) -> bool:
    best_step = _select_best_preview_step(steps)
    if not best_step or best_step.row_count is None:
        return False
    return best_step.row_count <= 5


def _build_generic_preview_answer(step: AssistantQueryStep) -> str | None:
    preview_rows = [
        row
        for row in step.preview[:3]
        if isinstance(row, Mapping)
    ]
    if not preview_rows:
        return None

    row_summaries = [_summarize_preview_row(row) for row in preview_rows]
    row_summaries = [summary for summary in row_summaries if summary]
    if not row_summaries:
        return None

    if step.row_count == 1:
        return "조회 결과는 " + row_summaries[0] + "입니다."

    if step.row_count is not None and step.row_count > len(row_summaries):
        return "조회 결과 상위는 " + ", ".join(row_summaries) + "입니다."

    return "조회 결과는 " + ", ".join(row_summaries) + "입니다."


def _summarize_preview_row(row: Mapping[str, object | None]) -> str | None:
    label_key = next(
        (
            key
            for key in (
                "player_name",
                "name",
                "opponent_team_name",
                "opponent_team",
                "topic",
                "position",
            )
            if _normalize_optional_text(row.get(key))
        ),
        None,
    )
    label = _normalize_optional_text(row.get(label_key)) if label_key else None

    detail_bits: list[str] = []
    for key, value in row.items():
        if key == label_key or key in {"player_id", "match_id", "training_id", "injury_id", "evaluation_id", "counseling_id"}:
            continue
        detail = _format_preview_detail(key, value)
        if detail:
            detail_bits.append(detail)
        if len(detail_bits) >= 3:
            break

    if label and detail_bits:
        return f"{label}(" + ", ".join(detail_bits) + ")"
    if label:
        return label
    if detail_bits:
        return ", ".join(detail_bits)
    return None


def _format_preview_detail(key: str, value: object | None) -> str | None:
    if value in (None, "", [], {}):
        return None

    if isinstance(value, bool):
        return f"{_preview_field_label(key)} {'예' if value else '아니오'}"

    if key.endswith("_date") or key.endswith("_at"):
        date_value = _display_date(value)
        return f"{_preview_field_label(key)} {date_value}" if date_value else None

    if isinstance(value, (int, float, Decimal)):
        if key != "acute_chronic_ratio" and any(token in key for token in ("accuracy", "ratio", "possession")):
            percent_detail = _format_percent_detail(_preview_field_label(key), value)
            if percent_detail:
                return percent_detail
        unit = _preview_field_unit(key)
        return f"{_preview_field_label(key)} {_format_number(value)}{unit}"

    text = _normalize_optional_text(value)
    if not text:
        return None
    return f"{_preview_field_label(key)} {text}"


def _preview_field_label(key: str) -> str:
    mapping = {
        "match_date": "경기일",
        "training_date": "훈련일",
        "expected_return_date": "복귀 예정일",
        "injury_status": "부상 상태",
        "injury_type": "부상 유형",
        "injury_part": "부상 부위",
        "recent_matches": "최근 경기",
        "recent_sessions": "최근 세션",
        "minutes_played": "출전 시간",
        "total_distance": "이동거리",
        "avg_total_distance": "평균 이동거리",
        "sprint_count": "스프린트",
        "avg_sprint_count": "평균 스프린트",
        "acute_load_7d": "7일 load",
        "acute_chronic_ratio": "ACWR",
        "technical": "technical",
        "tactical": "tactical",
        "physical": "physical",
        "mental": "mental",
        "note_count": "상담 건수",
        "roster_count": "총원",
        "available_count": "가용",
        "unavailable_count": "이탈",
        "rehab_count": "재활",
        "goals_for": "득점",
        "goals_against": "실점",
        "shots": "슈팅",
        "shots_on_target": "유효슈팅",
        "pass_accuracy": "패스 정확도",
        "duel_win_rate": "경합 승률",
        "evaluation_date": "평가일",
        "counseling_date": "상담일",
        "session_name": "세션",
        "intensity_level": "강도",
    }
    return mapping.get(key, key.replace("_", " "))


def _preview_field_unit(key: str) -> str:
    mapping = {
        "minutes_played": "분",
        "sprint_count": "회",
        "avg_sprint_count": "회",
        "recent_matches": "경기",
        "recent_sessions": "회",
        "note_count": "건",
        "roster_count": "명",
        "available_count": "명",
        "unavailable_count": "명",
        "rehab_count": "명",
    }
    return mapping.get(key, "")


def _select_best_preview_step(
    steps: Sequence[AssistantQueryStep],
) -> AssistantQueryStep | None:
    scored_steps: list[tuple[int, int, AssistantQueryStep]] = []
    for step in steps:
        if step.action != "sql" or step.error or not step.preview:
            continue
        top_row = step.preview[0]
        if not isinstance(top_row, Mapping):
            continue

        score = 0
        if step.row_count == 1:
            score += 5
        if "player_name" in top_row or "name" in top_row:
            score += 4
        if any(key in top_row for key in ("total_distance", "sprint_count", "minutes_played")):
            score += 4
        if "match_date" in top_row:
            score += 1
        score += min(len(top_row), 6)
        scored_steps.append((score, step.step, step))

    if not scored_steps:
        return None

    return max(scored_steps, key=lambda item: (item[0], item[1]))[2]
