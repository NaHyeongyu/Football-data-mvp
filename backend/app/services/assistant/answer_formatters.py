from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _subject_particle(name: str) -> str:
    if not name:
        return "이"

    last_char = name[-1]
    code_point = ord(last_char)
    if 0xAC00 <= code_point <= 0xD7A3:
        return "이" if (code_point - 0xAC00) % 28 else "가"
    return "이"


def _translate_occurrence_context(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()
    mapping = {
        "training": "훈련",
        "match": "경기",
        "gym": "웨이트",
        "rehab": "재활",
    }
    return mapping.get(normalized, value)


def _format_activity_leader_answer(
    *,
    top_row: Mapping[str, object | None],
    match_label: str,
) -> str:
    player_name = _normalize_optional_text(top_row.get("player_name") or top_row.get("name")) or "해당 선수"
    subject = _subject_particle(player_name)
    match_date = _normalize_optional_text(top_row.get("match_date"))

    metrics: list[str] = []
    total_distance = top_row.get("total_distance")
    sprint_count = top_row.get("sprint_count")
    minutes_played = top_row.get("minutes_played")

    if total_distance is not None:
        metrics.append(f"총 이동거리(total_distance) {total_distance}")
    if sprint_count is not None:
        metrics.append(f"스프린트 {sprint_count}회")
    if minutes_played is not None:
        metrics.append(f"출전 시간 {minutes_played}분")

    date_prefix = f"{match_date} 기준, " if match_date else ""
    if metrics:
        metric_text = ", ".join(metrics)
        return f"{date_prefix}{player_name}{subject} {match_label}에서 활동량이 가장 많았습니다. 조회 결과는 {metric_text}입니다."

    return f"{date_prefix}{player_name}{subject} {match_label}에서 활동량이 가장 많았습니다."


def _format_injury_cause_answer(
    *,
    top_row: Mapping[str, object | None],
) -> str:
    player_name = _normalize_optional_text(top_row.get("name") or top_row.get("player_name")) or "해당 선수"
    injury_date = _normalize_optional_text(top_row.get("injury_date"))
    injury_type = _normalize_optional_text(top_row.get("injury_type"))
    injury_part = _normalize_optional_text(top_row.get("injury_part"))
    severity_level = _normalize_optional_text(top_row.get("severity_level"))
    injury_mechanism = _normalize_optional_text(top_row.get("injury_mechanism"))
    occurred_during = _translate_occurrence_context(_normalize_optional_text(top_row.get("occurred_during")))
    notes = _normalize_optional_text(top_row.get("notes"))

    intro_bits = [bit for bit in (injury_part, injury_type) if bit]
    intro = ", ".join(intro_bits) if intro_bits else "가장 최근 부상"
    date_prefix = f"{injury_date} 기준, " if injury_date else ""

    detail_parts = []
    if severity_level:
        detail_parts.append(f"중증도는 {severity_level}")
    if injury_mechanism:
        detail_parts.append(f"기록된 발생 메커니즘은 {injury_mechanism}")
    if occurred_during:
        detail_parts.append(f"발생 시점은 {occurred_during}")

    detail_text = ". ".join(detail_parts)
    if detail_text:
        detail_text = f" {detail_text}."

    if notes:
        return (
            f"{date_prefix}{player_name}의 가장 최근 부상 기록을 보면 {intro}입니다."
            f"{detail_text} 비고에는 '{notes}'라고 남아 있어, 현재 데이터 기준으로는 이 기록이 부상 원인 분석의 핵심 근거입니다."
        )

    if detail_text:
        return (
            f"{date_prefix}{player_name}의 가장 최근 부상 기록을 보면 {intro}입니다."
            f"{detail_text} 현재 데이터 기준으로는 이 기록이 부상 원인 분석의 핵심 근거입니다."
        )

    return (
        f"{date_prefix}{player_name}의 가장 최근 부상 기록은 {intro}이지만, "
        "원인을 직접 설명하는 injury_mechanism이나 notes가 없어 정확한 원인 분석은 어렵습니다."
    )


def _format_current_injury_watch_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "현재 부상 또는 재활 상태로 잡혀 있는 선수는 없습니다."

    names = [str(row["name"]).strip() for row in rows if row.get("name")]
    deduped_names = list(dict.fromkeys(name for name in names if name))
    if not deduped_names:
        return "현재 부상 또는 재활 상태 선수의 이름을 확인하지 못했습니다."

    joined_names = ", ".join(deduped_names)
    return f"현재 부상 또는 재활 상태로 잡혀 있는 선수는 {joined_names}입니다."


def _format_position_availability_summary_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    position_filter: str | None,
) -> str:
    if not rows:
        if position_filter is not None:
            return f"{_position_filter_label(position_filter)} 기준 가용 현황 데이터를 찾지 못했습니다."
        return "포지션별 가용 현황 데이터를 찾지 못했습니다."

    if position_filter is not None:
        position_label = _position_filter_label(position_filter)
        unavailable_rows = [row for row in rows if bool(row.get("unavailable_flag"))]
        available_count = len(rows) - len(unavailable_rows)

        if not unavailable_rows:
            return f"{position_label} 기준 현재 {len(rows)}명 모두 가용 상태입니다."

        unavailable_summaries = []
        for row in unavailable_rows:
            name = _normalize_optional_text(row.get("name")) or "해당 선수"
            injury_label = ", ".join(
                bit
                for bit in (
                    _normalize_optional_text(row.get("injury_part")),
                    _normalize_optional_text(row.get("injury_type")),
                )
                if bit
            )
            detail_bits = [
                injury_label or None,
                _translate_injury_status(_normalize_optional_text(row.get("injury_status"))),
            ]
            expected_return_date = _display_date(row.get("expected_return_date"))
            if expected_return_date:
                detail_bits.append(f"복귀 예정 {expected_return_date}")
            unavailable_summaries.append(
                _format_ranked_summary(
                    name,
                    [detail for detail in detail_bits if detail],
                )
            )

        return (
            f"{position_label} 기준 현재 가용 {available_count}명 / 이탈 {len(unavailable_rows)}명입니다. "
            "이탈 선수는 "
            + ", ".join(unavailable_summaries)
            + "입니다."
        )

    summaries = []
    for row in rows:
        position = _position_filter_label(_normalize_optional_text(row.get("position")) or "기타")
        available_count = int(row.get("available_count") or 0)
        unavailable_count = int(row.get("unavailable_count") or 0)
        rehab_count = int(row.get("rehab_count") or 0)
        roster_count = int(row.get("roster_count") or 0)
        nearest_return_date = _display_date(row.get("nearest_return_date"))
        detail_bits = [
            f"총 {roster_count}명",
            f"가용 {available_count}명",
            f"이탈 {unavailable_count}명",
        ]
        if rehab_count > 0:
            detail_bits.append(f"재활 {rehab_count}명")
        if nearest_return_date:
            detail_bits.append(f"가장 빠른 복귀 {nearest_return_date}")
        summaries.append(f"{position}(" + ", ".join(detail_bits) + ")")

    return "포지션별 가용 현황은 " + ", ".join(summaries) + "입니다."


def _format_combined_workload_summary_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    mode: str,
    question: str,
    player_name: str | None,
) -> str:
    if not rows:
        if player_name is not None:
            return f"{player_name}의 최근 경기+훈련 통합 부하 데이터를 찾지 못했습니다."
        return "최근 경기+훈련 통합 부하를 비교할 수 있는 데이터를 찾지 못했습니다."

    top_row = rows[0]
    latest_session_date = _display_date(top_row.get("latest_session_date"))
    prefix = f"{latest_session_date} 기준, " if latest_session_date else ""

    def workload_bits(row: Mapping[str, object | None]) -> list[str]:
        bits = [
            _format_metric_detail("최근 세션", row.get("sessions_7d"), unit="회"),
            _format_metric_detail("훈련", row.get("training_sessions_7d"), unit="회"),
            _format_metric_detail("경기", row.get("match_sessions_7d"), unit="회"),
            _format_metric_detail("통합 load", row.get("acute_load_7d")),
            _format_metric_detail("이동거리", row.get("total_distance_7d")),
            _format_metric_detail("스프린트", row.get("sprint_count_7d"), unit="회"),
        ]
        ratio = row.get("acute_chronic_ratio")
        if ratio is not None:
            bits.append(f"ACWR {_format_number(ratio)}")
        baseline = row.get("chronic_load_baseline")
        if baseline not in (None, 0):
            bits.append(f"baseline {_format_number(baseline)}")
        return [bit for bit in bits if bit]

    if player_name is not None:
        detail_text = ", ".join(workload_bits(top_row))
        ratio = float(top_row["acute_chronic_ratio"]) if top_row.get("acute_chronic_ratio") is not None else None
        if mode == "trend" and ratio is not None:
            signal = "spike 신호" if ratio >= 1.22 else "drop 신호" if ratio <= 0.78 else "안정 구간"
            if detail_text:
                return f"{prefix}{player_name}의 최근 7일 경기+훈련 통합 부하는 {detail_text}이며, 현재 기준으로는 {signal}입니다."
            return f"{prefix}{player_name}의 최근 7일 경기+훈련 통합 부하는 현재 기준으로는 {signal}입니다."
        if detail_text:
            return f"{prefix}{player_name}의 최근 7일 경기+훈련 통합 부하는 {detail_text}입니다."
        return f"{prefix}{player_name}의 최근 7일 경기+훈련 통합 부하를 확인했습니다."

    if mode == "trend":
        if len(rows) == 1:
            name = _normalize_optional_text(top_row.get("name")) or "해당 선수"
            detail_text = ", ".join(workload_bits(top_row))
            if detail_text:
                return f"{prefix}최근 7일 경기+훈련 통합 부하 상승폭이 가장 큰 선수는 {name}입니다. {detail_text}입니다."
            return f"{prefix}최근 7일 경기+훈련 통합 부하 상승폭이 가장 큰 선수는 {name}입니다."

        summaries = [
            _format_ranked_summary(
                _normalize_optional_text(row.get("name")) or "해당 선수",
                workload_bits(row),
            )
            for row in rows
        ]
        return f"{prefix}최근 7일 경기+훈련 통합 부하 상승폭이 큰 선수는 " + ", ".join(summaries) + "입니다."

    if len(rows) == 1:
        name = _normalize_optional_text(top_row.get("name")) or "해당 선수"
        detail_text = ", ".join(workload_bits(top_row))
        if detail_text:
            return f"{prefix}최근 7일 경기+훈련 통합 부하가 가장 높은 선수는 {name}입니다. {detail_text}입니다."
        return f"{prefix}최근 7일 경기+훈련 통합 부하가 가장 높은 선수는 {name}입니다."

    summaries = [
        _format_ranked_summary(
            _normalize_optional_text(row.get("name")) or "해당 선수",
            workload_bits(row),
        )
        for row in rows
    ]
    return f"{prefix}최근 7일 경기+훈련 통합 부하 상위는 " + ", ".join(summaries) + "입니다."


def _format_player_profile_summary_answer(
    row: Mapping[str, object | None],
) -> str:
    name = _normalize_optional_text(row.get("name")) or "해당 선수"
    jersey_number = _normalize_optional_text(row.get("jersey_number"))
    primary_position = _normalize_optional_text(row.get("primary_position"))
    secondary_position = _normalize_optional_text(row.get("secondary_position"))
    foot = _translate_foot(_normalize_optional_text(row.get("foot")))
    nationality = _normalize_optional_text(row.get("nationality"))
    roster_status = _translate_roster_status(_normalize_optional_text(row.get("status")))
    previous_team = _normalize_optional_text(row.get("previous_team"))

    intro_bits = []
    if jersey_number:
        intro_bits.append(f"등번호 {jersey_number}번")
    if primary_position:
        position_text = f"주포지션 {primary_position}"
        if secondary_position:
            position_text += f", 부포지션 {secondary_position}"
        intro_bits.append(position_text)
    if foot:
        intro_bits.append(foot)
    if nationality:
        intro_bits.append(f"{nationality} 출신")
    if roster_status:
        intro_bits.append(f"현재 roster status는 {roster_status}")

    physical_date = _display_date(row.get("physical_profile_date"))
    physical_bits = [
        bit
        for bit in (
            _format_metric_detail("신장", row.get("height_cm"), unit="cm"),
            _format_metric_detail("체중", row.get("weight_kg"), unit="kg"),
            _format_metric_detail("체지방", row.get("body_fat_percentage"), unit="%"),
            _format_metric_detail("BMI", row.get("bmi")),
            _format_metric_detail("근육량", row.get("muscle_mass_kg"), unit="kg"),
        )
        if bit
    ]

    injury_type = _normalize_optional_text(row.get("injury_type"))
    injury_part = _normalize_optional_text(row.get("injury_part"))
    injury_status = _translate_injury_status(_normalize_optional_text(row.get("injury_status")))
    injury_date = _display_date(row.get("injury_date"))
    expected_return_date = _display_date(row.get("expected_return_date"))

    test_date = _display_date(row.get("physical_test_date"))
    test_bits = [
        bit
        for bit in (
            _format_metric_detail("10m", row.get("sprint_10m"), unit="초"),
            _format_metric_detail("30m", row.get("sprint_30m"), unit="초"),
            _format_metric_detail("수직점프", row.get("vertical_jump_cm"), unit="cm"),
            _format_metric_detail("T-test", row.get("agility_t_test_sec"), unit="초"),
        )
        if bit
    ]

    evaluation_date = _display_date(row.get("evaluation_date"))
    evaluation_bits = [
        bit
        for bit in (
            _format_metric_detail("technical", row.get("technical")),
            _format_metric_detail("tactical", row.get("tactical")),
            _format_metric_detail("physical", row.get("physical")),
            _format_metric_detail("mental", row.get("mental")),
        )
        if bit
    ]

    counseling_date = _display_date(row.get("counseling_date"))
    counseling_topic = _normalize_optional_text(row.get("counseling_topic"))

    sentences = []
    if intro_bits:
        sentence = f"{name}은 " + ", ".join(intro_bits) + "입니다."
        if previous_team:
            sentence += f" 이전 팀은 {previous_team}입니다."
        sentences.append(sentence)
    else:
        sentences.append(f"{name}의 기본 프로필을 정리했습니다.")

    if physical_bits:
        prefix = f"최신 체성분({physical_date} 기준)은 " if physical_date else "최신 체성분은 "
        sentences.append(prefix + ", ".join(physical_bits) + "입니다.")

    if injury_type or injury_status:
        injury_label = ", ".join(part for part in (injury_part, injury_type) if part)
        injury_sentence = "현재 등록된 부상 상태는 "
        if injury_date:
            injury_sentence += f"{injury_date} 기준 "
        injury_sentence += injury_label or "부상 기록"
        if injury_status:
            injury_sentence += f"로 {injury_status} 상태"
        if expected_return_date:
            injury_sentence += f"이며 복귀 예정일은 {expected_return_date}"
        sentences.append(injury_sentence + "입니다.")
    else:
        sentences.append("현재 등록된 부상 또는 재활 상태는 없습니다.")

    if test_bits:
        prefix = f"최근 체력 테스트({test_date})는 " if test_date else "최근 체력 테스트는 "
        sentences.append(prefix + ", ".join(test_bits) + "입니다.")
    if evaluation_bits:
        prefix = f"최근 평가({evaluation_date})는 " if evaluation_date else "최근 평가는 "
        evaluation_text = prefix + ", ".join(evaluation_bits)
        coach_comment = _normalize_optional_text(row.get("coach_comment"))
        if coach_comment:
            evaluation_text += f"이고 코치 코멘트는 '{coach_comment}'입니다."
        else:
            evaluation_text += "입니다."
        sentences.append(evaluation_text)
    if counseling_topic:
        prefix = f"최근 상담({counseling_date})은 " if counseling_date else "최근 상담은 "
        counseling_summary = _normalize_optional_text(row.get("counseling_summary"))
        if counseling_summary:
            sentences.append(prefix + f"'{counseling_topic}' 주제였고 요약은 '{counseling_summary}'입니다.")
        else:
            sentences.append(prefix + f"'{counseling_topic}' 주제입니다.")

    return " ".join(sentences)


def _format_physical_change_answer(
    row: Mapping[str, object | None],
) -> str:
    name = _normalize_optional_text(row.get("name")) or "해당 선수"
    latest_profile_date = _display_date(row.get("latest_profile_date"))
    latest_test_date = _display_date(row.get("latest_test_date"))

    body_comp_bits = [
        bit
        for bit in (
            _format_delta_detail(
                "체중",
                latest_value=row.get("latest_weight_kg"),
                previous_value=row.get("previous_weight_kg"),
                unit="kg",
            ),
            _format_delta_detail(
                "체지방",
                latest_value=row.get("latest_body_fat_percentage"),
                previous_value=row.get("previous_body_fat_percentage"),
                unit="%",
                delta_unit="%p",
            ),
            _format_delta_detail(
                "BMI",
                latest_value=row.get("latest_bmi"),
                previous_value=row.get("previous_bmi"),
            ),
            _format_delta_detail(
                "근육량",
                latest_value=row.get("latest_muscle_mass_kg"),
                previous_value=row.get("previous_muscle_mass_kg"),
                unit="kg",
            ),
        )
        if bit
    ]

    test_bits = [
        bit
        for bit in (
            _format_delta_detail(
                "10m",
                latest_value=row.get("latest_sprint_10m"),
                previous_value=row.get("previous_sprint_10m"),
                unit="초",
            ),
            _format_delta_detail(
                "30m",
                latest_value=row.get("latest_sprint_30m"),
                previous_value=row.get("previous_sprint_30m"),
                unit="초",
            ),
            _format_delta_detail(
                "수직점프",
                latest_value=row.get("latest_vertical_jump_cm"),
                previous_value=row.get("previous_vertical_jump_cm"),
                unit="cm",
            ),
            _format_delta_detail(
                "T-test",
                latest_value=row.get("latest_agility_t_test_sec"),
                previous_value=row.get("previous_agility_t_test_sec"),
                unit="초",
            ),
        )
        if bit
    ]

    sentences = []
    if body_comp_bits:
        prefix = f"{name}의 최근 체성분 변화는 {latest_profile_date} 기준 " if latest_profile_date else f"{name}의 최근 체성분 변화는 "
        sentences.append(prefix + ", ".join(body_comp_bits) + "입니다.")
    if test_bits:
        prefix = f"최근 체력 테스트 변화는 {latest_test_date} 기준 " if latest_test_date else "최근 체력 테스트 변화는 "
        sentences.append(prefix + ", ".join(test_bits) + "입니다.")

    if sentences:
        return " ".join(sentences)
    return f"{name}의 피지컬 변화 데이터를 비교할 수 있을 만큼 충분히 찾지 못했습니다."


def _format_evaluation_summary_answer(
    row: Mapping[str, object | None],
) -> str:
    name = _normalize_optional_text(row.get("name")) or "해당 선수"
    evaluation_date = _display_date(row.get("latest_evaluation_date"))
    latest_scores = {
        "technical": row.get("latest_technical"),
        "tactical": row.get("latest_tactical"),
        "physical": row.get("latest_physical"),
        "mental": row.get("latest_mental"),
    }
    valid_scores = {label: float(value) for label, value in latest_scores.items() if value is not None}
    if not valid_scores:
        return f"{name}의 최신 평가 데이터를 찾지 못했습니다."

    highest_score = max(valid_scores.values())
    lowest_score = min(valid_scores.values())
    strongest = "/".join(label for label, value in valid_scores.items() if value == highest_score)
    weakest = "/".join(label for label, value in valid_scores.items() if value == lowest_score)

    score_text = ", ".join(f"{label} {_format_number(value)}" for label, value in valid_scores.items())
    sentences = [
        f"{name}의 최신 평가({evaluation_date})는 {score_text}입니다."
        if evaluation_date
        else f"{name}의 최신 평가는 {score_text}입니다."
    ]
    sentences.append(f"가장 높은 항목은 {strongest}, 가장 낮은 항목은 {weakest}입니다.")

    change_bits = [
        bit
        for bit in (
            _format_score_change("technical", row.get("latest_technical"), row.get("previous_technical")),
            _format_score_change("tactical", row.get("latest_tactical"), row.get("previous_tactical")),
            _format_score_change("physical", row.get("latest_physical"), row.get("previous_physical")),
            _format_score_change("mental", row.get("latest_mental"), row.get("previous_mental")),
        )
        if bit
    ]
    if change_bits:
        previous_date = _display_date(row.get("previous_evaluation_date"))
        prefix = f"직전 평가({previous_date}) 대비 " if previous_date else "직전 평가 대비 "
        sentences.append(prefix + ", ".join(change_bits) + "였습니다.")

    coach_comment = _normalize_optional_text(row.get("latest_coach_comment"))
    if coach_comment:
        sentences.append(f"코치 코멘트는 '{coach_comment}'입니다.")

    return " ".join(sentences)


def _format_counseling_summary_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "상담 기록을 찾지 못했습니다."

    latest_row = rows[0]
    name = _normalize_optional_text(latest_row.get("name")) or "해당 선수"
    counseling_date = _display_date(latest_row.get("counseling_date"))
    topic = _normalize_optional_text(latest_row.get("topic")) or "상담"
    summary = _normalize_optional_text(latest_row.get("summary"))

    date_prefix = f"{counseling_date} 기준, " if counseling_date else ""
    if summary:
        intro = f"{date_prefix}{name}의 최근 상담은 '{topic}' 주제였고 요약은 '{summary}'입니다."
    else:
        intro = f"{date_prefix}{name}의 최근 상담은 '{topic}' 주제입니다."

    if len(rows) == 1:
        return intro

    topic_counter = Counter(
        _normalize_optional_text(row.get("topic")) or "기타"
        for row in rows
    )
    topic_summary = ", ".join(f"{item} {count}회" for item, count in topic_counter.most_common())
    recent_entries = ", ".join(
        f"{_display_date(row.get('counseling_date'))} {(_normalize_optional_text(row.get('topic')) or '상담')}"
        for row in rows
    )
    return intro + f" 최근 {len(rows)}건을 보면 {topic_summary} 순으로 기록돼 있었고, 최근 흐름은 {recent_entries}입니다."


def _format_player_recent_match_summary_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "최근 경기 기록을 찾지 못했습니다."

    top_row = rows[0]
    player_name = _normalize_optional_text(top_row.get("player_name")) or "해당 선수"
    if len(rows) == 1:
        match_date = _display_date(top_row.get("match_date"))
        match_type = _normalize_optional_text(top_row.get("match_type"))
        opponent_team = _normalize_optional_text(top_row.get("opponent_team"))
        intro_bits = [bit for bit in (match_type, opponent_team) if bit]
        intro = ", ".join(intro_bits) if intro_bits else "최근 경기"
        detail_bits = [
            bit
            for bit in (
                _format_metric_detail("출전 시간", top_row.get("minutes_played"), unit="분"),
                _format_metric_detail("득점", top_row.get("goals")),
                _format_metric_detail("도움", top_row.get("assists")),
                _format_metric_detail("슈팅", top_row.get("shots")),
                _format_percent_detail("패스 정확도", top_row.get("pass_accuracy")),
                _format_metric_detail("이동거리", top_row.get("total_distance")),
                _format_metric_detail("스프린트", top_row.get("sprint_count"), unit="회"),
            )
            if bit
        ]
        prefix = f"{match_date} 기준, " if match_date else ""
        return f"{prefix}{player_name}의 최근 경기({intro}) 기록은 " + ", ".join(detail_bits) + "입니다."

    summaries = []
    for row in rows:
        match_date = _display_date(row.get("match_date")) or "최근 경기"
        match_type = _normalize_optional_text(row.get("match_type"))
        opponent_team = _normalize_optional_text(row.get("opponent_team"))
        label_parts = [match_date]
        if match_type:
            label_parts.append(match_type)
        if opponent_team:
            label_parts.append(opponent_team)
        summaries.append(
            " ".join(label_parts)
            + " "
            + ", ".join(
                bit
                for bit in (
                    _format_metric_detail("득점", row.get("goals")),
                    _format_metric_detail("도움", row.get("assists")),
                    _format_metric_detail("이동거리", row.get("total_distance")),
                    _format_metric_detail("스프린트", row.get("sprint_count"), unit="회"),
                )
                if bit
            )
        )
    return f"{player_name}의 최근 경기 흐름은 " + " / ".join(summaries) + "입니다."


def _format_player_recent_training_summary_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "최근 훈련 기록을 찾지 못했습니다."

    top_row = rows[0]
    player_name = _normalize_optional_text(top_row.get("name")) or "해당 선수"
    if len(rows) == 1:
        training_date = _display_date(top_row.get("training_date"))
        session_name = _normalize_optional_text(top_row.get("session_name"))
        training_focus = _normalize_optional_text(top_row.get("training_focus"))
        intensity = _normalize_optional_text(top_row.get("intensity_level"))
        intro_bits = [bit for bit in (session_name, training_focus, f"강도 {intensity}" if intensity else None) if bit]
        intro = ", ".join(intro_bits) if intro_bits else "최근 훈련"
        detail_bits = [
            bit
            for bit in (
                _format_metric_detail("이동거리", top_row.get("total_distance")),
                _format_metric_detail("스프린트", top_row.get("sprint_count"), unit="회"),
                _format_metric_detail("가속", top_row.get("accel_count"), unit="회"),
                _format_metric_detail("감속", top_row.get("decel_count"), unit="회"),
            )
            if bit
        ]
        prefix = f"{training_date} 기준, " if training_date else ""
        return f"{prefix}{player_name}의 최근 훈련({intro}) 기록은 " + ", ".join(detail_bits) + "입니다."

    summaries = []
    for row in rows:
        training_date = _display_date(row.get("training_date")) or "최근 훈련"
        session_name = _normalize_optional_text(row.get("session_name"))
        label = f"{training_date} {session_name}".strip() if session_name else training_date
        summaries.append(
            label
            + " "
            + ", ".join(
                bit
                for bit in (
                    _format_metric_detail("이동거리", row.get("total_distance")),
                    _format_metric_detail("스프린트", row.get("sprint_count"), unit="회"),
                    _format_metric_detail("가속", row.get("accel_count"), unit="회"),
                )
                if bit
            )
        )
    return f"{player_name}의 최근 훈련 흐름은 " + " / ".join(summaries) + "입니다."


def _format_return_to_play_timeline_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "복귀 일정을 추적 중인 선수가 없습니다."

    if len(rows) == 1:
        row = rows[0]
        name = _normalize_optional_text(row.get("name")) or "해당 선수"
        injury_date = _display_date(row.get("injury_date"))
        injury_label = ", ".join(
            part for part in (
                _normalize_optional_text(row.get("injury_part")),
                _normalize_optional_text(row.get("injury_type")),
            ) if part
        )
        injury_status = _translate_injury_status(_normalize_optional_text(row.get("injury_status")))
        expected_return_date = _display_date(row.get("expected_return_date"))
        if expected_return_date:
            return (
                f"{name}의 현재 복귀 일정은 {expected_return_date} 예정입니다. "
                f"{injury_date + ' 기준, ' if injury_date else ''}{injury_label or '부상'} 상태는 {injury_status or '추적 중'}입니다."
            )
        return f"{name}의 현재 부상 상태는 {injury_label or '부상'}이며, 아직 등록된 복귀 예정일은 없습니다."

    summaries = []
    for row in rows:
        name = _normalize_optional_text(row.get("name")) or "해당 선수"
        expected_return_date = _display_date(row.get("expected_return_date")) or "미정"
        injury_status = _translate_injury_status(_normalize_optional_text(row.get("injury_status"))) or "추적 중"
        summaries.append(f"{name}({expected_return_date}, {injury_status})")
    return "현재 복귀 일정 기준으로 보면 " + ", ".join(summaries) + " 순입니다."


def _format_physical_leaderboard_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    metric: str,
    direction: str,
) -> str:
    if not rows:
        return "피지컬 순위를 계산할 데이터를 찾지 못했습니다."
    metric_label = _physical_metric_label(metric)
    direction_label = "상위" if direction == "DESC" else "하위"
    summaries = [
        _format_ranked_summary(
            _normalize_optional_text(row.get("name")) or "해당 선수",
            [
                _format_metric_detail(metric_label, row.get(metric), unit=_physical_metric_unit(metric)),
                _format_metric_detail("체중", row.get("weight_kg"), unit="kg") if metric != "weight_kg" else None,
                _format_metric_detail("근육량", row.get("muscle_mass_kg"), unit="kg") if metric != "muscle_mass_kg" else None,
                _format_metric_detail("체지방", row.get("body_fat_percentage"), unit="%") if metric != "body_fat_percentage" else None,
            ],
        )
        for row in rows
    ]
    latest_date = _display_date(rows[0].get("created_at"))
    prefix = f"{latest_date} 기준, " if latest_date else ""
    return f"{prefix}{metric_label} {direction_label}는 " + ", ".join(summaries) + "입니다."


def _format_physical_test_leaderboard_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    metric: str,
    direction: str,
) -> str:
    if not rows:
        return "체력 테스트 순위를 계산할 데이터를 찾지 못했습니다."
    metric_label = _physical_test_metric_label(metric)
    direction_label = "상위" if direction == "DESC" and metric == "vertical_jump_cm" else "상위"
    if metric in {"sprint_10m", "sprint_30m", "agility_t_test_sec"} and direction == "ASC":
        direction_label = "상위"
    elif metric in {"sprint_10m", "sprint_30m", "agility_t_test_sec"} and direction == "DESC":
        direction_label = "하위"
    test_date = _display_date(rows[0].get("test_date"))
    summaries = [
        _format_ranked_summary(
            _normalize_optional_text(row.get("name")) or "해당 선수",
            [_format_metric_detail(metric_label, row.get(metric), unit=_physical_test_metric_unit(metric))],
        )
        for row in rows
    ]
    prefix = f"{test_date} 기준, " if test_date else ""
    return f"{prefix}{metric_label} {direction_label}는 " + ", ".join(summaries) + "입니다."


def _format_evaluation_leaderboard_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    metric: str,
    direction: str,
) -> str:
    if not rows:
        return "평가 순위를 계산할 데이터를 찾지 못했습니다."
    metric_label = metric
    direction_label = "상위" if direction == "DESC" else "하위"
    evaluation_date = _display_date(rows[0].get("evaluation_date"))
    summaries = [
        _format_ranked_summary(
            _normalize_optional_text(row.get("name")) or "해당 선수",
            [
                _format_metric_detail(metric_label, row.get(metric)),
                _format_metric_detail("technical", row.get("technical")) if metric != "technical" else None,
                _format_metric_detail("tactical", row.get("tactical")) if metric != "tactical" else None,
                _format_metric_detail("physical", row.get("physical")) if metric != "physical" else None,
                _format_metric_detail("mental", row.get("mental")) if metric != "mental" else None,
            ],
        )
        for row in rows
    ]
    prefix = f"{evaluation_date} 기준, " if evaluation_date else ""
    return f"{prefix}{metric_label} 평가 {direction_label}는 " + ", ".join(summaries) + "입니다."


def _format_counseling_topic_summary_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "최근 상담 주제를 집계할 데이터가 없습니다."
    latest_date = _display_date(rows[0].get("latest_date"))
    summaries = [
        f"{_normalize_optional_text(row.get('topic')) or '기타'} {_format_number(row.get('note_count'))}건"
        for row in rows
    ]
    prefix = f"{latest_date} 기준 최근 60일 상담 주제는 " if latest_date else "최근 60일 상담 주제는 "
    return prefix + ", ".join(summaries) + " 순입니다."


def _format_roster_lookup_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    position_filter: str | None,
    foot_filter: str | None,
    status_filter: str | None,
) -> str:
    if not rows:
        return "조건에 맞는 선수를 찾지 못했습니다."
    filter_bits = []
    if position_filter:
        filter_bits.append(_position_filter_label(position_filter))
    if foot_filter:
        filter_bits.append(_translate_foot(foot_filter) or foot_filter)
    if status_filter:
        filter_bits.append(_translate_roster_status(status_filter) or status_filter)
    prefix = "조건에 맞는 선수는 " if filter_bits else "조회된 선수는 "
    if filter_bits:
        prefix = f"{', '.join(filter_bits)} 기준 선수는 "
    summaries = [
        _format_ranked_summary(
            _normalize_optional_text(row.get("name")) or "해당 선수",
            [
                _format_metric_detail("등번호", row.get("jersey_number"), unit="번"),
                _format_position_summary(
                    _normalize_optional_text(row.get("primary_position")),
                    _normalize_optional_text(row.get("secondary_position")),
                ),
                _translate_foot(_normalize_optional_text(row.get("foot"))),
            ],
        )
        for row in rows
    ]
    return prefix + ", ".join(summaries) + "입니다."


def _format_team_recent_match_summary_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "최근 팀 경기 요약 데이터를 찾지 못했습니다."
    if len(rows) == 1:
        row = rows[0]
        match_date = _display_date(row.get("match_date"))
        opponent = _normalize_optional_text(row.get("opponent_team_name")) or "상대팀"
        match_type = _normalize_optional_text(row.get("match_type")) or "경기"
        detail_bits = [
            _format_scoreline(row.get("goals_for"), row.get("goals_against")),
            _format_percent_detail("점유율", row.get("possession_for")),
            _format_metric_detail("슈팅", row.get("shots")),
            _format_metric_detail("유효슈팅", row.get("shots_on_target")),
            _format_percent_detail("패스 정확도", row.get("pass_accuracy")),
            _format_percent_detail("경합 승률", row.get("duel_win_rate")),
        ]
        details = ", ".join(bit for bit in detail_bits if bit)
        prefix = f"{match_date} {match_type} {opponent}전은 " if match_date else f"{match_type} {opponent}전은 "
        return prefix + details + "입니다."

    summaries = []
    for row in rows:
        match_date = _display_date(row.get("match_date")) or "최근 경기"
        opponent = _normalize_optional_text(row.get("opponent_team_name")) or "상대팀"
        summaries.append(
            f"{match_date} {opponent}전 "
            + ", ".join(
                bit
                for bit in (
                    _format_scoreline(row.get("goals_for"), row.get("goals_against")),
                    _format_metric_detail("슈팅", row.get("shots")),
                    _format_metric_detail("유효슈팅", row.get("shots_on_target")),
                )
                if bit
            )
        )
    return "최근 팀 경기 흐름은 " + " / ".join(summaries) + "입니다."


def _format_position_recent_form_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    position_filter: str,
    metric: str,
) -> str:
    if not rows:
        return "해당 포지션의 최근 폼 데이터를 찾지 못했습니다."
    metric_label = {
        "avg_total_distance": "평균 이동거리",
        "avg_sprint_count": "평균 스프린트",
        "avg_minutes": "평균 출전 시간",
    }.get(metric, metric)
    summaries = [
        _format_ranked_summary(
            _normalize_optional_text(row.get("player_name")) or "해당 선수",
            [
                _format_metric_detail("최근 경기", row.get("recent_matches"), unit="경기"),
                _format_metric_detail(metric_label, row.get(metric), unit="회" if metric == "avg_sprint_count" else ("분" if metric == "avg_minutes" else "")),
                _format_metric_detail("평균 이동거리", row.get("avg_total_distance")) if metric != "avg_total_distance" else None,
                _format_metric_detail("평균 스프린트", row.get("avg_sprint_count"), unit="회") if metric != "avg_sprint_count" else None,
            ],
        )
        for row in rows
    ]
    return f"{_position_filter_label(position_filter)} 기준 최근 폼 상위는 " + ", ".join(summaries) + "입니다."


def _format_player_comparison_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if len(rows) < 2:
        return "두 선수 비교에 필요한 데이터를 충분히 찾지 못했습니다."
    summaries = []
    for row in rows:
        name = _normalize_optional_text(row.get("name")) or "해당 선수"
        bits = [
            _format_metric_detail("최근 경기", row.get("recent_matches"), unit="경기"),
            _format_metric_detail("평균 이동거리", row.get("avg_total_distance")),
            _format_metric_detail("평균 스프린트", row.get("avg_sprint_count"), unit="회"),
            _format_metric_detail("득점", row.get("total_goals")),
            _format_metric_detail("도움", row.get("total_assists")),
            _format_metric_detail("physical", row.get("physical")),
            _format_metric_detail("technical", row.get("technical")),
            _format_metric_detail("tactical", row.get("tactical")),
            _format_metric_detail("mental", row.get("mental")),
        ]
        summaries.append(f"{name}(" + ", ".join(bit for bit in bits if bit) + ")")
    return "비교 결과는 " + " / ".join(summaries) + "입니다."


def _format_opponent_match_lookup_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "상대팀 기준 경기 기록을 찾지 못했습니다."
    opponent = _normalize_optional_text(rows[0].get("opponent_team_name")) or "상대팀"
    if len(rows) == 1:
        row = rows[0]
        match_date = _display_date(row.get("match_date"))
        match_type = _normalize_optional_text(row.get("match_type")) or "경기"
        bits = [
            _format_scoreline(row.get("goals_for"), row.get("goals_against")),
            _format_percent_detail("점유율", row.get("possession_for")),
            _format_metric_detail("슈팅", row.get("shots")),
            _format_metric_detail("유효슈팅", row.get("shots_on_target")),
            _format_percent_detail("패스 정확도", row.get("pass_accuracy")),
        ]
        return f"{match_date} {match_type} {opponent}전 기록은 " + ", ".join(bit for bit in bits if bit) + "입니다."

    summaries = []
    for row in rows:
        match_date = _display_date(row.get("match_date")) or "최근 경기"
        summaries.append(
            f"{match_date} "
            + ", ".join(
                bit
                for bit in (
                    _format_scoreline(row.get("goals_for"), row.get("goals_against")),
                    _format_metric_detail("슈팅", row.get("shots")),
                    _format_metric_detail("유효슈팅", row.get("shots_on_target")),
                )
                if bit
            )
        )
    return f"{opponent} 상대 최근 경기 흐름은 " + " / ".join(summaries) + "입니다."


def _format_training_load_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    mode: str,
    question: str,
) -> str:
    if not rows:
        return "훈련 부하를 비교할 수 있는 데이터를 찾지 못했습니다."

    if mode == "latest":
        top_row = rows[0]
        training_date = _normalize_optional_text(top_row.get("training_date"))
        session_name = _normalize_optional_text(top_row.get("session_name"))
        intensity_level = _normalize_optional_text(top_row.get("intensity_level"))
        session_bits = [bit for bit in (session_name, f"강도 {intensity_level}" if intensity_level else None) if bit]
        session_label = ", ".join(session_bits) if session_bits else "최신 훈련"
        prefix = f"{training_date} 기준, " if training_date else ""

        if len(rows) == 1:
            player_name = _normalize_optional_text(top_row.get("name")) or "해당 선수"
            detail_bits = [
                bit
                for bit in (
                    _format_metric_detail("총 이동거리", top_row.get("total_distance")),
                    _format_metric_detail("스프린트", top_row.get("sprint_count"), unit="회"),
                    _format_metric_detail("가속", top_row.get("accel_count"), unit="회"),
                    _format_metric_detail("감속", top_row.get("decel_count"), unit="회"),
                )
                if bit
            ]
            if detail_bits:
                return f"{prefix}가장 최근 훈련({session_label}) 기준 활동량이 가장 높은 선수는 {player_name}입니다. " + ", ".join(detail_bits) + "입니다."
            return f"{prefix}가장 최근 훈련({session_label}) 기준 활동량이 가장 높은 선수는 {player_name}입니다."

        summaries = [
            _format_ranked_summary(
                _normalize_optional_text(row.get("name")) or "해당 선수",
                [
                    _format_metric_detail("이동거리", row.get("total_distance")),
                    _format_metric_detail("스프린트", row.get("sprint_count"), unit="회"),
                    _format_metric_detail("가속", row.get("accel_count"), unit="회"),
                ],
            )
            for row in rows
        ]
        return f"{prefix}가장 최근 훈련({session_label}) 기준 활동량 상위는 " + ", ".join(summaries) + "입니다."

    if mode == "trend":
        focus = "직전 14일 훈련 부하가 이전 14일 대비 가장 많이 오른"
        top_row = rows[0]
        latest_training_date = _normalize_optional_text(top_row.get("latest_training_date"))
        prefix = f"{latest_training_date} 기준, " if latest_training_date else ""
        distance_ratio = float(top_row["distance_ratio"]) if top_row.get("distance_ratio") is not None else None
        sprint_ratio = float(top_row["sprint_ratio"]) if top_row.get("sprint_ratio") is not None else None
        high_sessions = int(top_row.get("recent_high_sessions") or 0)
        has_clear_spike = (
            (distance_ratio is not None and distance_ratio >= 1.15)
            or (sprint_ratio is not None and sprint_ratio >= 1.15)
            or high_sessions >= 2
        )
        if len(rows) == 1:
            player_name = _normalize_optional_text(top_row.get("name")) or "해당 선수"
            detail_bits = [
                bit
                for bit in (
                    _format_ratio_detail(
                        "평균 이동거리",
                        recent_value=top_row.get("recent_avg_total_distance"),
                        prior_value=top_row.get("prior_avg_total_distance"),
                        ratio=top_row.get("distance_ratio"),
                    ),
                    _format_ratio_detail(
                        "평균 스프린트",
                        recent_value=top_row.get("recent_avg_sprint_count"),
                        prior_value=top_row.get("prior_avg_sprint_count"),
                        ratio=top_row.get("sprint_ratio"),
                        unit="회",
                    ),
                    _format_metric_detail("최근 high 강도 세션", top_row.get("recent_high_sessions"), unit="회"),
                )
                if bit
            ]
            if not has_clear_spike:
                if detail_bits:
                    return (
                        f"{prefix}직전 14일 훈련 부하가 이전 14일 대비 뚜렷하게 급격히 오른 선수는 보이지 않았습니다. "
                        f"상대적으로는 {player_name}의 변화폭이 가장 컸고, "
                        + ", ".join(detail_bits)
                        + "입니다."
                    )
                return f"{prefix}직전 14일 훈련 부하가 이전 14일 대비 뚜렷하게 급격히 오른 선수는 보이지 않았습니다."
            if detail_bits:
                return f"{prefix}{focus} 선수는 {player_name}입니다. " + ", ".join(detail_bits) + "입니다."
            return f"{prefix}{focus} 선수는 {player_name}입니다."

        summaries = [
            _format_ranked_summary(
                _normalize_optional_text(row.get("name")) or "해당 선수",
                [
                    _format_ratio_detail(
                        "이동거리",
                        recent_value=row.get("recent_avg_total_distance"),
                        prior_value=row.get("prior_avg_total_distance"),
                        ratio=row.get("distance_ratio"),
                    ),
                    _format_ratio_detail(
                        "스프린트",
                        recent_value=row.get("recent_avg_sprint_count"),
                        prior_value=row.get("prior_avg_sprint_count"),
                        ratio=row.get("sprint_ratio"),
                        unit="회",
                    ),
                    _format_metric_detail("high 강도", row.get("recent_high_sessions"), unit="회"),
                ],
            )
            for row in rows
        ]
        return f"{prefix}직전 14일 훈련 부하 상승폭이 큰 선수는 " + ", ".join(summaries) + "입니다."

    top_row = rows[0]
    latest_training_date = _normalize_optional_text(top_row.get("latest_training_date"))
    prefix = f"{latest_training_date} 기준, " if latest_training_date else ""

    if len(rows) == 1:
        player_name = _normalize_optional_text(top_row.get("name")) or "해당 선수"
        detail_bits = [
            bit
            for bit in (
                _format_metric_detail("최근 세션 수", top_row.get("recent_sessions"), unit="회"),
                _format_metric_detail("평균 이동거리", top_row.get("avg_total_distance")),
                _format_metric_detail("평균 스프린트", top_row.get("avg_sprint_count"), unit="회"),
                _format_metric_detail("high 강도 세션", top_row.get("high_sessions"), unit="회"),
            )
            if bit
        ]
        if detail_bits:
            return f"{prefix}최근 14일 훈련 부하가 가장 높은 선수는 {player_name}입니다. " + ", ".join(detail_bits) + "입니다."
        return f"{prefix}최근 14일 훈련 부하가 가장 높은 선수는 {player_name}입니다."

    summaries = [
        _format_ranked_summary(
            _normalize_optional_text(row.get("name")) or "해당 선수",
            [
                _format_metric_detail("평균 이동거리", row.get("avg_total_distance")),
                _format_metric_detail("평균 스프린트", row.get("avg_sprint_count"), unit="회"),
                _format_metric_detail("high 강도", row.get("high_sessions"), unit="회"),
            ],
        )
        for row in rows
    ]
    return f"{prefix}최근 14일 훈련 부하 상위는 " + ", ".join(summaries) + "입니다."


def _format_recent_match_form_answer(
    *,
    rows: Sequence[Mapping[str, object | None]],
    mode: str,
    question: str,
) -> str:
    if not rows:
        return "최근 경기 폼을 비교할 수 있는 데이터를 찾지 못했습니다."

    top_row = rows[0]
    latest_match_date = _normalize_optional_text(top_row.get("latest_match_date"))
    prefix = f"{latest_match_date} 기준, " if latest_match_date else ""

    if mode in {"trend_up", "trend_down"}:
        label = "가장 떨어진" if mode == "trend_down" else "가장 올라온"
        if len(rows) == 1:
            player_name = _normalize_optional_text(top_row.get("player_name")) or "해당 선수"
            detail_bits = [
                bit
                for bit in (
                    _format_ratio_detail(
                        "평균 이동거리",
                        recent_value=top_row.get("recent_avg_total_distance"),
                        prior_value=top_row.get("prior_avg_total_distance"),
                        ratio=top_row.get("distance_ratio"),
                    ),
                    _format_ratio_detail(
                        "평균 스프린트",
                        recent_value=top_row.get("recent_avg_sprint_count"),
                        prior_value=top_row.get("prior_avg_sprint_count"),
                        ratio=top_row.get("sprint_ratio"),
                        unit="회",
                    ),
                )
                if bit
            ]
            if detail_bits:
                return f"{prefix}최근 21일 경기 폼이 이전 21일 대비 {label} 선수는 {player_name}입니다. " + ", ".join(detail_bits) + "입니다."
            return f"{prefix}최근 21일 경기 폼이 이전 21일 대비 {label} 선수는 {player_name}입니다."

        summaries = [
            _format_ranked_summary(
                _normalize_optional_text(row.get("player_name")) or "해당 선수",
                [
                    _format_ratio_detail(
                        "이동거리",
                        recent_value=row.get("recent_avg_total_distance"),
                        prior_value=row.get("prior_avg_total_distance"),
                        ratio=row.get("distance_ratio"),
                    ),
                    _format_ratio_detail(
                        "스프린트",
                        recent_value=row.get("recent_avg_sprint_count"),
                        prior_value=row.get("prior_avg_sprint_count"),
                        ratio=row.get("sprint_ratio"),
                        unit="회",
                    ),
                ],
            )
            for row in rows
        ]
        return f"{prefix}최근 21일 경기 폼 변화폭 기준으로 보면 {label} 선수는 " + ", ".join(summaries) + "입니다."

    if len(rows) == 1:
        player_name = _normalize_optional_text(top_row.get("player_name")) or "해당 선수"
        detail_bits = [
            bit
            for bit in (
                _format_metric_detail("최근 경기 수", top_row.get("recent_matches"), unit="경기"),
                _format_metric_detail("평균 이동거리", top_row.get("avg_total_distance")),
                _format_metric_detail("평균 스프린트", top_row.get("avg_sprint_count"), unit="회"),
            )
            if bit
        ]
        if detail_bits:
            return f"{prefix}최근 21일 경기 폼이 가장 좋은 선수는 {player_name}입니다. " + ", ".join(detail_bits) + "입니다."
        return f"{prefix}최근 21일 경기 폼이 가장 좋은 선수는 {player_name}입니다."

    summaries = [
        _format_ranked_summary(
            _normalize_optional_text(row.get("player_name")) or "해당 선수",
            [
                _format_metric_detail("최근 경기", row.get("recent_matches"), unit="경기"),
                _format_metric_detail("평균 이동거리", row.get("avg_total_distance")),
                _format_metric_detail("평균 스프린트", row.get("avg_sprint_count"), unit="회"),
            ],
        )
        for row in rows
    ]
    return f"{prefix}최근 21일 경기 폼 상위는 " + ", ".join(summaries) + "입니다."


def _format_ranked_summary(name: str, detail_bits: Sequence[str | None]) -> str:
    details = ", ".join(bit for bit in detail_bits if bit)
    if not details:
        return name
    return f"{name}({details})"


def _format_metric_detail(label: str, value: Any, *, unit: str = "") -> str | None:
    if value is None:
        return None
    return f"{label} {_format_number(value)}{unit}"


def _format_percent_detail(label: str, value: Any) -> str | None:
    if value is None:
        return None
    numeric = float(value)
    if numeric <= 1:
        numeric *= 100
    return f"{label} {_format_number(numeric)}%"


def _format_scoreline(goals_for: Any, goals_against: Any) -> str | None:
    if goals_for is None or goals_against is None:
        return None
    return f"스코어 {_format_number(goals_for)}-{_format_number(goals_against)}"


def _format_delta_detail(
    label: str,
    *,
    latest_value: Any,
    previous_value: Any,
    unit: str = "",
    delta_unit: str | None = None,
) -> str | None:
    if latest_value is None:
        return None
    if previous_value is None:
        return f"{label} {_format_number(latest_value)}{unit}"

    latest_float = float(latest_value)
    previous_float = float(previous_value)
    delta = latest_float - previous_float
    effective_delta_unit = delta_unit if delta_unit is not None else unit
    delta_prefix = "+" if delta > 0 else ""
    delta_text = f"{delta_prefix}{_format_number(delta)}{effective_delta_unit}"
    return (
        f"{label} {_format_number(latest_value)}{unit}"
        f"(이전 {_format_number(previous_value)}{unit}, 변화 {delta_text})"
    )


def _format_score_change(label: str, latest_value: Any, previous_value: Any) -> str | None:
    if latest_value is None or previous_value is None:
        return None
    delta = float(latest_value) - float(previous_value)
    delta_prefix = "+" if delta > 0 else ""
    return f"{label} {delta_prefix}{_format_number(delta)}"


def _format_ratio_detail(
    label: str,
    *,
    recent_value: Any,
    prior_value: Any,
    ratio: Any,
    unit: str = "",
) -> str | None:
    if recent_value is None:
        return None
    ratio_value = float(ratio) if ratio is not None else None
    if prior_value is not None and ratio_value is not None:
        return (
            f"{label} {_format_number(recent_value)}{unit}로 이전 {_format_number(prior_value)}{unit} 대비 "
            f"{ratio_value:.2f}배"
        )
    return f"{label} {_format_number(recent_value)}{unit}"


def _ratio(pre_value: Any, base_value: Any) -> float | None:
    if pre_value is None or base_value is None:
        return None

    pre_float = float(pre_value)
    base_float = float(base_value)
    if base_float <= 0:
        return None
    return pre_float / base_float


def _format_number(value: Any) -> str:
    if value is None:
        return "-"

    numeric = float(value)
    if abs(numeric - round(numeric)) < 1e-9:
        return str(int(round(numeric)))
    return f"{numeric:.2f}".rstrip("0").rstrip(".")


def _display_date(value: Any) -> str | None:
    text = _normalize_optional_text(value)
    if text is None:
        return None
    return text.split("T", maxsplit=1)[0]


def _translate_foot(value: str | None) -> str | None:
    mapping = {
        "left": "왼발",
        "right": "오른발",
        "both": "양발",
    }
    if value is None:
        return None
    return mapping.get(value.strip().lower(), value)


def _translate_roster_status(value: str | None) -> str | None:
    mapping = {
        "active": "활동 가능",
        "inactive": "비활성",
        "loan": "임대",
    }
    if value is None:
        return None
    return mapping.get(value.strip().lower(), value)


def _translate_injury_status(value: str | None) -> str | None:
    mapping = {
        "rehab": "재활",
        "injured": "부상",
        "available": "출전 가능",
    }
    if value is None:
        return None
    return mapping.get(value.strip().lower(), value)


def _physical_metric_label(metric: str) -> str:
    mapping = {
        "weight_kg": "체중",
        "body_fat_percentage": "체지방",
        "muscle_mass_kg": "근육량",
        "bmi": "BMI",
    }
    return mapping.get(metric, metric)


def _physical_metric_unit(metric: str) -> str:
    mapping = {
        "weight_kg": "kg",
        "body_fat_percentage": "%",
        "muscle_mass_kg": "kg",
        "bmi": "",
    }
    return mapping.get(metric, "")


def _physical_test_metric_label(metric: str) -> str:
    mapping = {
        "sprint_10m": "10m",
        "sprint_30m": "30m",
        "vertical_jump_cm": "수직점프",
        "agility_t_test_sec": "T-test",
    }
    return mapping.get(metric, metric)


def _physical_test_metric_unit(metric: str) -> str:
    mapping = {
        "sprint_10m": "초",
        "sprint_30m": "초",
        "vertical_jump_cm": "cm",
        "agility_t_test_sec": "초",
    }
    return mapping.get(metric, "")


def _position_filter_label(position_filter: str) -> str:
    mapping = {
        "GK": "골키퍼",
        "CB": "센터백",
        "RB": "라이트백",
        "LB": "레프트백",
        "DM": "수비형 미드필더",
        "CM": "중앙 미드필더",
        "AM": "공격형 미드필더",
        "RW": "라이트 윙",
        "LW": "레프트 윙",
        "ST": "스트라이커",
        "CF": "센터포워드",
        "FULLBACK": "풀백",
        "WINGER": "윙어",
        "MIDFIELDER": "미드필더",
    }
    return mapping.get(position_filter, position_filter)


def _format_position_summary(primary_position: str | None, secondary_position: str | None) -> str | None:
    if primary_position and secondary_position and secondary_position != primary_position:
        return f"{primary_position}/{secondary_position}"
    return primary_position or secondary_position


def _format_pre_injury_workload_answer(
    rows: Sequence[Mapping[str, object | None]],
) -> str:
    if not rows:
        return "부상 전 workload를 비교할 대상 선수를 찾지 못했습니다."

    flagged_summaries: list[str] = []
    neutral_summaries: list[str] = []

    for row in rows:
        name = _normalize_optional_text(row.get("name")) or "해당 선수"
        injury_date = _normalize_optional_text(row.get("injury_date")) or "해당 부상일"
        injury_type = _normalize_optional_text(row.get("injury_type"))
        injury_part = _normalize_optional_text(row.get("injury_part"))
        injury_label = ", ".join(part for part in (injury_part, injury_type) if part)

        training_distance_ratio = _ratio(row.get("pre7_training_avg_distance"), row.get("base_training_avg_distance"))
        training_sprint_ratio = _ratio(row.get("pre7_training_avg_sprints"), row.get("base_training_avg_sprints"))
        match_distance_ratio = _ratio(row.get("pre7_match_avg_distance"), row.get("base_match_avg_distance"))
        match_sprint_ratio = _ratio(row.get("pre7_match_avg_sprints"), row.get("base_match_avg_sprints"))
        high_training_sessions = int(row.get("pre7_high_training_sessions") or 0)

        detail_bits: list[str] = []
        flagged = False

        if match_distance_ratio is not None and match_distance_ratio >= 1.25:
            flagged = True
            detail_bits.append(
                "경기 평균 이동거리 "
                f"{_format_number(row.get('pre7_match_avg_distance'))}로 baseline {_format_number(row.get('base_match_avg_distance'))} 대비 "
                f"{match_distance_ratio:.2f}배"
            )
        if match_sprint_ratio is not None and match_sprint_ratio >= 1.25:
            flagged = True
            detail_bits.append(
                "경기 평균 스프린트 "
                f"{_format_number(row.get('pre7_match_avg_sprints'))}회로 baseline {_format_number(row.get('base_match_avg_sprints'))}회 대비 "
                f"{match_sprint_ratio:.2f}배"
            )
        if training_distance_ratio is not None and training_distance_ratio >= 1.15:
            flagged = True
            detail_bits.append(
                "훈련 평균 이동거리 "
                f"{_format_number(row.get('pre7_training_avg_distance'))}로 baseline {_format_number(row.get('base_training_avg_distance'))} 대비 "
                f"{training_distance_ratio:.2f}배"
            )
        if training_sprint_ratio is not None and training_sprint_ratio >= 1.15:
            flagged = True
            detail_bits.append(
                "훈련 평균 스프린트 "
                f"{_format_number(row.get('pre7_training_avg_sprints'))}회로 baseline {_format_number(row.get('base_training_avg_sprints'))}회 대비 "
                f"{training_sprint_ratio:.2f}배"
            )
        if high_training_sessions > 0:
            flagged = True
            detail_bits.append(f"부상 전 7일 안에 high 강도 훈련 {high_training_sessions}회")

        intro = f"{injury_date} 부상({injury_label}) 기준 {name}"
        if flagged and detail_bits:
            flagged_summaries.append(f"{intro}: " + ", ".join(detail_bits))
            continue

        neutral_bits: list[str] = []
        if training_distance_ratio is not None:
            neutral_bits.append(
                "훈련 평균 이동거리 "
                f"{_format_number(row.get('pre7_training_avg_distance'))} / baseline {_format_number(row.get('base_training_avg_distance'))}"
            )
        if training_sprint_ratio is not None:
            neutral_bits.append(
                "훈련 평균 스프린트 "
                f"{_format_number(row.get('pre7_training_avg_sprints'))}회 / baseline {_format_number(row.get('base_training_avg_sprints'))}회"
            )
        if neutral_bits:
            neutral_summaries.append(f"{intro}: 뚜렷한 spike는 크지 않았습니다. " + ", ".join(neutral_bits))
        else:
            neutral_summaries.append(f"{intro}: 비교 가능한 baseline 데이터가 충분하지 않았습니다.")

    if flagged_summaries and neutral_summaries:
        return (
            "부상 전 workload 신호를 보면 뚜렷한 상승이 확인되는 선수와 그렇지 않은 선수가 갈립니다. "
            + " / ".join(flagged_summaries + neutral_summaries)
        )
    if flagged_summaries:
        return "부상 전 workload 신호를 보면 다음 선수들에서 상대적으로 높은 부하가 확인됩니다. " + " / ".join(flagged_summaries)

    return "현재 확인 가능한 부상 전 workload 데이터에서는 뚜렷한 spike가 크게 보이지 않습니다. " + " / ".join(neutral_summaries)
