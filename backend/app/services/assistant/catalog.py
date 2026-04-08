from __future__ import annotations

import re
from typing import Any


def _normalize_search_text(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def _extract_search_terms(value: str) -> set[str]:
    normalized = re.sub(r"[^0-9a-zA-Z가-힣]+", " ", value.strip().lower())
    return {term for term in normalized.split() if term}


SEARCH_STOPWORDS = {
    "선수",
    "알려줘",
    "보여줘",
    "해줘",
    "봐줘",
    "있어",
    "있나",
    "있는",
    "누구",
    "누가",
    "뭐",
    "좀",
    "top",
    "player",
    "players",
    "leader",
    "list",
}


def _extract_informative_terms(value: str) -> set[str]:
    return {term for term in _extract_search_terms(value) if term not in SEARCH_STOPWORDS}


SCHEMA_OBJECT_HINTS: dict[str, dict[str, Any]] = {
    "football.players": {
        "description": "Master roster table for player identity, position, nationality, and current roster status.",
        "keywords": ["선수", "로스터", "포지션", "국적", "status", "roster"],
        "preferred_for": ["player profile", "roster status", "basic player lookup"],
        "join_keys": [
            "player_id -> football.player_match_stats.player_id",
            "player_id -> football.match_gps_stats.player_id",
            "player_id -> football.injuries.player_id",
        ],
    },
    "football.matches": {
        "description": "Match header table. Owns the authoritative match_date, match_type, and scoreline.",
        "keywords": ["경기", "최근 경기", "가장 최근 경기", "공식 경기", "연습 경기", "match", "일정", "score"],
        "preferred_for": ["latest match filtering", "official/practice match filtering", "match date filtering", "scoreline lookup"],
        "join_keys": [
            "match_id -> football.player_match_stats.match_id",
            "match_id -> football.match_gps_stats.match_id",
        ],
    },
    "football.player_match_stats": {
        "description": "Raw per-player match stats. Does not include match_date, opponent_team, stadium, or GPS distance columns.",
        "keywords": ["경기 기록", "출전", "패스", "슈팅", "수비", "raw match stats"],
        "preferred_for": ["raw technical match stats"],
        "join_keys": [
            "match_id -> football.matches.match_id",
            "player_id -> football.players.player_id",
        ],
        "warnings": [
            "Do not filter or order by match_date here without joining football.matches.",
            "Do not expect total_distance or sprint_count here without joining football.match_gps_stats or using football.player_match_facts.",
        ],
    },
    "football.match_gps_stats": {
        "description": "Raw per-player match GPS workload table. Contains total_distance, sprint_count, accel_count, decel_count, and speed metrics.",
        "keywords": ["활동량", "거리", "스프린트", "가속", "감속", "gps", "load"],
        "preferred_for": ["match workload", "activity leaders", "distance and sprint metrics"],
        "join_keys": [
            "match_id + player_id -> football.player_match_stats.match_id + player_id",
            "match_id -> football.matches.match_id",
        ],
    },
    "football.trainings": {
        "description": "Training session header table with training_date, intensity_level, coach, and session metadata.",
        "keywords": ["훈련", "세션", "training", "강도", "코치"],
        "preferred_for": ["training session filtering", "training calendar"],
        "join_keys": [
            "training_id -> football.training_gps_stats.training_id",
        ],
    },
    "football.training_gps_stats": {
        "description": "Raw per-player training GPS workload table. Use for overall training load, distance, sprint, acceleration, and deceleration.",
        "keywords": ["훈련 활동량", "훈련 부하", "training load", "거리", "스프린트", "가속"],
        "preferred_for": ["training workload", "training activity leaders"],
        "join_keys": [
            "training_id -> football.trainings.training_id",
            "player_id -> football.players.player_id",
        ],
    },
    "football.injuries": {
        "description": "Historical injury log with injury_date, mechanism, occurred_during context, notes, severity, rehab status, and return dates.",
        "keywords": ["부상", "재활", "복귀", "injury", "rehab", "원인", "메커니즘", "발생"],
        "preferred_for": ["injury history", "injury cause analysis", "return timeline", "rehab tracking"],
        "join_keys": [
            "player_id -> football.players.player_id",
        ],
    },
    "football.player_current_injury_status": {
        "description": "Curated latest injury-status view per player. Best default source for current injury or rehab questions.",
        "keywords": ["현재 부상", "재활 상태", "복귀 예정", "injury status", "availability"],
        "preferred_for": ["current injury watchlist", "return-to-play status", "latest rehab state"],
        "join_keys": [
            "player_id -> football.players.player_id",
        ],
    },
    "football.player_latest_physical_profile": {
        "description": "Curated latest body-composition view per player. Best default source for current weight, body fat, BMI, and muscle mass.",
        "keywords": ["피지컬", "체성분", "체중", "근육량", "body fat", "bmi"],
        "preferred_for": ["current physical profile", "body composition changes"],
        "join_keys": [
            "player_id -> football.players.player_id",
        ],
    },
    "football.physical_profiles": {
        "description": "Historical body-composition records per player. Use when the question is about change over time in weight, body fat, BMI, or muscle mass.",
        "keywords": ["피지컬 변화", "체성분 변화", "체중 변화", "체지방", "근육량", "physical change"],
        "preferred_for": ["historical body composition", "physical trend analysis"],
        "join_keys": [
            "player_id -> football.players.player_id",
        ],
    },
    "football.physical_tests": {
        "description": "Historical physical test results including sprint, jump, and agility measurements.",
        "keywords": ["체력 테스트", "스프린트 테스트", "점프", "민첩성", "agility", "vertical jump"],
        "preferred_for": ["physical test trend analysis", "speed and agility testing"],
        "join_keys": [
            "player_id -> football.players.player_id",
        ],
    },
    "football.evaluations": {
        "description": "Coach evaluation records with technical, tactical, physical, mental scores and coach_comment.",
        "keywords": ["평가", "평가점수", "코치평가", "technical", "tactical", "mental", "coach comment"],
        "preferred_for": ["latest player evaluation", "evaluation trend", "coach feedback"],
        "join_keys": [
            "player_id -> football.players.player_id",
        ],
    },
    "football.counseling_notes": {
        "description": "Counseling note history with counseling_date, topic, and summary for each player.",
        "keywords": ["상담", "멘탈", "상담노트", "counseling", "topic", "summary"],
        "preferred_for": ["counseling summary", "mental support notes", "recent counseling history"],
        "join_keys": [
            "player_id -> football.players.player_id",
        ],
    },
    "football.player_match_facts": {
        "description": "Curated per-player-per-match view already joined with matches, opponent, stadium, and GPS fields. Default source for latest match activity and recent form questions.",
        "keywords": ["최근 경기", "활동량", "상대", "구장", "최근 폼", "match facts", "latest match"],
        "preferred_for": ["latest match activity", "recent match form", "opponent/stadium context", "match leaders"],
        "join_keys": [
            "Already joined to matches, players, opponent_teams, stadiums, and match_gps_stats.",
        ],
    },
}


PLAYBOOK_EXAMPLE_QUESTIONS: dict[str, list[str]] = {
    "pre_injury_workload_analysis": [
        "부상 이전 경기나 훈련에서 강도가 높았던 선수 있어?",
        "다치기 전에 훈련량이 과했던 선수 있나?",
        "부상 전 7일 workload spike 있었어?",
        "부상 직전 훈련 부하가 올라간 선수 알려줘",
        "다치기 전 경기 활동량이 급증한 선수 있어?",
        "부상 전에 고강도 훈련이 많았던 선수는?",
        "부상 직전 스프린트 수가 평소보다 높았어?",
        "부상 전 이동거리가 baseline보다 많이 오른 선수 있어?",
        "재활 들어가기 전에 workload가 과부하였던 케이스 보여줘",
        "부상 직전 1주일 훈련량 비교해줘",
        "부상 전에 경기 load가 튄 선수 찾아줘",
        "다치기 전 7일과 이전 4주를 비교해줘",
        "부상 전 workload 위험 신호가 있었는지 봐줘",
        "injury 전에 training load가 높았는지 확인해줘",
        "부상 이전 match load spike 있는 선수 알려줘",
        "부상 직전 고강도 세션 있었는지 알려줘",
    ],
    "injury_cause_analysis": [
        "박시우의 부상 원인 분석해줘",
        "장서진 왜 다쳤어?",
        "최신 부상 메커니즘 알려줘",
        "부상 원인이 뭐야",
        "어떤 상황에서 다쳤는지 알려줘",
        "injury cause 분석해줘",
        "부상 발생 메커니즘 보여줘",
        "부상 notes 기반으로 설명해줘",
        "훈련 중 다친 건지 경기 중 다친 건지 알려줘",
        "왜 부상 났는지 기록으로 설명해줘",
        "가장 최근 부상 원인 알려줘",
        "부상 당시 상황 분석해줘",
    ],
    "latest_official_match_activity_leader": [
        "가장 최근 공식경기에서 활동량 1위 누구야",
        "최근 공식전 활동량 많은 선수 알려줘",
        "가장 최근 공식 경기에서 제일 많이 뛴 선수는?",
        "직전 공식경기 total distance 1등 누구야",
        "최근 공식전 스프린트 많은 선수 알려줘",
        "공식경기 기준 활동량 최상위 선수는?",
        "마지막 공식전에서 많이 뛴 선수 누구야",
        "latest official match activity leader 알려줘",
        "최근 공식 경기 load leader 누구야",
        "공식전에서 이동거리 가장 높은 선수는?",
        "최근 공식경기 GPS 활동량 1위 알려줘",
        "가장 최근 공식 매치에서 workload 제일 높은 선수는?",
    ],
    "latest_match_activity_leader": [
        "가장 최근 경기 활동량 많은 선수 누구야",
        "가장 최근 경기에서 제일 많이 뛴 선수는?",
        "마지막 경기 total distance 1위는?",
        "최근 경기 스프린트 가장 많은 선수 알려줘",
        "최근 경기 load leader 누구야",
        "직전 경기 GPS 활동량 상위 선수는?",
        "마지막 경기 workload 최고 선수 알려줘",
        "latest match activity leader 알려줘",
        "가장 최근 match에서 많이 뛴 선수 누구야",
        "최근 경기에서 이동거리 제일 높은 선수는?",
        "최근 매치 활동량 top player 누구야",
        "가장 최근 연습경기 포함해서 활동량 1위 누구야",
    ],
    "recent_match_form": [
        "요즘 폼 좋은 선수 누구야",
        "최근 폼이 올라온 선수 알려줘",
        "최근 3주 경기력 좋은 선수는?",
        "최근 경기 활동량 기준 폼 상위 선수는?",
        "요즘 많이 뛰는 선수 누구야",
        "최근 match form leader 알려줘",
        "최근 14일 경기 부하 높은 선수는?",
        "최근 몇 경기 평균 이동거리 높은 선수 알려줘",
        "최근 폼 떨어진 선수 있어?",
        "요즘 스프린트 수 기준 폼 좋은 선수는?",
        "최근 출전 경기에서 꾸준한 선수 알려줘",
        "recent form 좋은 선수 보여줘",
        "최근 경기 기준 평균 load 상위 선수는?",
        "최근 21일간 경기폼이 좋은 선수 알려줘",
        "요즘 match workload top players 보여줘",
        "최근 폼 비교해줘",
    ],
    "current_injury_watch": [
        "지금 부상상태인 선수 이름 알려줘",
        "현재 재활 중인 선수 누구야",
        "지금 못 뛰는 선수 명단 알려줘",
        "현재 injury status 있는 선수 알려줘",
        "지금 부상자 명단 보여줘",
        "현재 availability 문제 있는 선수는?",
        "복귀 전인 선수 누구야",
        "현재 부상 또는 재활 상태 선수 알려줘",
        "재활 중 선수 목록 보여줘",
        "현재 injury watch list 보여줘",
        "지금 다친 선수 누구야",
        "현재 부상 현황 알려줘",
        "다음 경기 출전 어려운 선수 누구야",
        "현재 결장 예상 선수 보여줘",
        "지금 가용 아닌 선수 알려줘",
        "현재 출전 불가 선수 명단 줘",
    ],
    "training_load": [
        "최근 훈련량 많은 선수 누구야",
        "오늘 훈련에서 많이 뛴 선수 알려줘",
        "최근 2주 training load 높은 선수는?",
        "훈련 활동량 top player 누구야",
        "훈련 강도 높은 세션 알려줘",
        "최근 훈련 GPS 부하 상위 선수는?",
        "training load leader 보여줘",
        "최근 훈련 총 이동거리 높은 선수는?",
        "최근 훈련 스프린트 많은 선수는?",
        "가장 최근 훈련 활동량 1위 누구야",
        "훈련에서 가속 감속 많은 선수 알려줘",
        "최근 14일 훈련 부하 비교해줘",
        "최근 training intensity 높은 선수 누구야",
        "최근 훈련 세션별 load 상위권 보여줘",
        "최근 훈련에서 overreaching 의심 선수 있어?",
        "최근 훈련량이 급격히 오른 선수 있어?",
        "훈련 workload 많은 순으로 보여줘",
        "가장 최근 training GPS leaders 알려줘",
        "최근 high intensity training 많은 선수는?",
        "요즘 훈련량 많은 선수 알려줘",
        "최근 훈련 과부하 의심 선수 누구야",
        "직전 14일 훈련 spike 선수 보여줘",
        "훈련 강도 급증한 선수 알려줘",
        "최근 훈련 부하 상승폭 큰 선수 알려줘",
    ],
    "combined_workload_summary": [
        "최근 7일 경기랑 훈련 합쳐서 workload 높은 선수 알려줘",
        "경기와 훈련 통합 부하 상위 선수 보여줘",
        "요즘 경기 훈련 포함해서 가장 많이 뛴 선수 누구야",
        "최근 1주 경기랑 훈련 전체 load 높은 선수는?",
        "경기 훈련 합산해서 과부하 의심 선수 있어?",
        "통합 workload spike 있는 선수 알려줘",
        "최근 7일 overall load leader 보여줘",
        "경기랑 훈련 포함 최근 부하 상승한 선수 알려줘",
        "combined workload top players 보여줘",
        "경기와 훈련을 같이 보면 누가 제일 힘들었어",
        "최근 세션 전체 기준 스프린트 노출 높은 선수 알려줘",
        "최근 7일 acute chronic ratio 높은 선수 보여줘",
    ],
    "position_availability_summary": [
        "센터백 현재 가용 인원 보여줘",
        "포지션별 결장 현황 알려줘",
        "풀백 라인 지금 몇 명 출전 가능해",
        "미드필더 포지션에 부상 공백 있어?",
        "윙어 자리 가용 선수 몇 명이야",
        "포지션별 availability risk 보여줘",
        "현재 스트라이커 포지션 결장 선수 알려줘",
        "골키퍼 라인업 가능한 인원 정리해줘",
        "포지션별 부상 재활 현황 알려줘",
        "센터백 지금 누가 빠져 있어",
    ],
    "player_profile_summary": [
        "오재민 선수 프로필 요약해줘",
        "오재민 기본 정보 알려줘",
        "오재민 포지션이랑 등번호 뭐야",
        "오재민 선수 정보 정리해줘",
        "오재민 로스터 상태랑 프로필 보여줘",
        "오재민 국적이랑 주발 알려줘",
        "오재민 profile summary 보여줘",
        "오재민 신상 정보 알려줘",
        "오재민 현재 상태 한 번에 정리해줘",
        "오재민 기본 프로필이랑 몸상태 같이 보여줘",
        "오재민 선수 카드처럼 요약해줘",
        "오재민 최신 프로필 브리핑해줘",
    ],
    "physical_change_analysis": [
        "오재민 피지컬 변화 알려줘",
        "오재민 체성분 변화 어때",
        "오재민 체중이랑 체지방 변화 봐줘",
        "오재민 근육량 변화 알려줘",
        "오재민 체력 테스트 변화 보여줘",
        "오재민 physical change 분석해줘",
        "오재민 sprint test 추이 알려줘",
        "오재민 최근 피지컬 상태 어때",
        "오재민 최근 체지방 줄었어?",
        "오재민 최근 근육량 늘었는지 알려줘",
        "오재민 30m 기록 좋아졌어?",
        "오재민 점프 기록 변화 봐줘",
    ],
    "evaluation_summary": [
        "오재민 평가 요약해줘",
        "오재민 최근 평가 점수 알려줘",
        "오재민 technical tactical physical mental 점수 보여줘",
        "오재민 coach comment 알려줘",
        "오재민 evaluation summary 봐줘",
        "오재민 최근 평가에서 강점이 뭐야",
        "오재민 평가 추이 알려줘",
        "오재민 코치 평가 어때",
        "오재민 최근 평가에서 약점 뭐야",
        "오재민 평가 좋아졌는지 알려줘",
        "오재민 최신 코치 코멘트 요약해줘",
        "오재민 멘탈 평가 어때",
    ],
    "counseling_summary": [
        "오재민 상담 내용 요약해줘",
        "오재민 최근 상담 기록 알려줘",
        "오재민 멘탈 상담 내용 보여줘",
        "오재민 counseling summary 해줘",
        "오재민 최근 상담 주제가 뭐야",
        "오재민 상담 노트 요약해줘",
        "오재민 최근 코칭 메모 알려줘",
        "오재민 상담 이력 요약해줘",
        "오재민 최근 상담에서 반복된 이슈 뭐야",
        "오재민 상담 분위기 요약해줘",
        "오재민 최근 멘탈 이슈 알려줘",
        "오재민 상담에서 자주 나온 주제 뭐야",
    ],
    "player_recent_match_summary": [
        "오재민 최근 경기 요약해줘",
        "오재민 직전 경기 어땠어",
        "오재민 최근 공식 경기 기록 알려줘",
        "오재민 마지막 경기 스탯 보여줘",
        "오재민 최근 경기 stats 정리해줘",
        "오재민 지난 경기 기록 요약해줘",
        "오재민 최근 3경기 브리핑해줘",
        "오재민 직전 공식전 기록 알려줘",
        "오재민 최근 출전 경기 흐름 정리해줘",
        "오재민 마지막 매치 performance 요약해줘",
    ],
    "player_recent_training_summary": [
        "오재민 최근 훈련 요약해줘",
        "오재민 마지막 훈련 기록 알려줘",
        "오재민 최근 training session 어땠어",
        "오재민 직전 훈련 부하 보여줘",
        "오재민 최근 훈련 stats 정리해줘",
        "오재민 최근 세션 기록 알려줘",
        "오재민 최근 3회 훈련 정리해줘",
        "오재민 가장 최근 세션 intensity 어땠어",
        "오재민 직전 훈련 활동량 요약해줘",
        "오재민 최근 training load 흐름 보여줘",
    ],
    "return_to_play_timeline": [
        "지금 다친 선수들 언제 복귀해",
        "장서진 복귀 예정일 알려줘",
        "복귀 일정 보여줘",
        "누가 먼저 복귀하나",
        "박시우 언제 돌아와",
        "expected return timeline 보여줘",
        "현재 재활 선수 복귀 순서 알려줘",
        "다음 경기 전에 돌아오는 선수 있어?",
        "복귀 예정일 빠른 선수부터 보여줘",
        "지금 부상자들 예상 복귀 시점 정리해줘",
    ],
    "physical_leaderboard": [
        "근육량 가장 많은 선수 누구야",
        "체지방 낮은 선수 순위 보여줘",
        "체중 많이 나가는 선수 알려줘",
        "BMI 높은 선수 top3 보여줘",
        "피지컬 좋은 선수 ranking 보여줘",
        "muscle mass leader 알려줘",
        "체지방 가장 낮은 선수 top5 보여줘",
        "근육량 상위 선수 순위 보여줘",
        "BMI 낮은 선수 알려줘",
        "체중 가벼운 선수 top3 보여줘",
    ],
    "physical_test_leaderboard": [
        "10m 가장 빠른 선수 누구야",
        "30m 스프린트 top3 보여줘",
        "점프 제일 높은 선수 알려줘",
        "민첩성 좋은 선수 순위 보여줘",
        "T-test 빠른 선수 누구야",
        "physical test leader 보여줘",
        "30m 가장 느린 선수도 보여줘",
        "수직점프 top5 알려줘",
        "민첩성 테스트 상위권 보여줘",
        "최신 체력 테스트 leader 누구야",
    ],
    "evaluation_leaderboard": [
        "피지컬 평가 높은 선수 누구야",
        "technical 점수 top3 보여줘",
        "mental 점수 낮은 선수 알려줘",
        "최근 평가 기준 tactical leader 누구야",
        "evaluation ranking 보여줘",
        "코치 평가 좋은 선수 순위 알려줘",
        "technical 평가 가장 좋은 선수 알려줘",
        "mental 점수 높은 선수 순위 보여줘",
        "최근 평가에서 physical 낮은 선수 알려줘",
        "tactical 상위 5명 보여줘",
    ],
    "counseling_topic_summary": [
        "최근 상담 주제 뭐가 많아",
        "최근 상담 이슈 요약해줘",
        "팀 전체 counseling theme 보여줘",
        "요즘 멘탈 상담 주제 정리해줘",
        "상담노트에서 많이 나오는 주제 알려줘",
        "최근 상담 topic ranking 보여줘",
        "최근 60일 상담 주제 순위 보여줘",
        "상담 주제별 건수 정리해줘",
        "요즘 선수단 상담 흐름 알려줘",
        "가장 많이 나온 counseling topic 뭐야",
    ],
    "roster_lookup": [
        "센터백 누구 있어",
        "왼발 선수 목록 보여줘",
        "active 선수 명단 알려줘",
        "GK들 누구야",
        "오른발 풀백 누구 있어",
        "현재 로스터에서 CB 보여줘",
        "현재 활동 가능한 풀백 누구야",
        "스트라이커 명단 보여줘",
        "양발 미드필더 목록 알려줘",
        "골키퍼 로스터 보여줘",
        "미드필더 중 왼발 선수 누구 있어",
        "active 센터백 명단 보여줘",
        "오른발 윙어 목록 알려줘",
        "현재 로스터에서 스트라이커 보여줘",
    ],
    "team_recent_match_summary": [
        "최근 경기 팀 기록 요약해줘",
        "가장 최근 경기 팀 경기력 어땠어",
        "최근 공식전 결과 요약해줘",
        "팀 최근 경기 스탯 보여줘",
        "마지막 경기 팀 summary 알려줘",
        "공식전 팀 퍼포먼스 요약해줘",
        "최근 3경기 팀 흐름 정리해줘",
        "직전 공식전 팀 지표 요약해줘",
        "우리 팀 최근 경기력 브리핑해줘",
        "팀 최근 매치 리포트처럼 정리해줘",
        "최근 3경기 공식전 결과 브리핑해줘",
        "직전 경기 점유율이랑 슈팅 어땠어",
        "최근 경기에서 팀 퍼포먼스 떨어졌어?",
        "가장 최근 매치 팀 데이터 요약해줘",
    ],
    "position_recent_form": [
        "센터백 중 최근 폼 좋은 선수 누구야",
        "풀백 최근 경기폼 상위 보여줘",
        "윙어 중 요즘 많이 뛰는 선수 알려줘",
        "미드필더 최근 폼 비교해줘",
        "ST 중 최근 스프린트 많은 선수 누구야",
        "포지션별 최근 폼 보여줘",
        "센터백 recent form ranking 보여줘",
        "미드필더 중 최근 이동거리 높은 선수 알려줘",
        "윙어 최근 스프린트 상위 보여줘",
        "풀백 중 최근 출전시간 많은 선수 누구야",
    ],
    "player_comparison": [
        "오재민이랑 정우진 비교해줘",
        "오재민과 정우진 최근 폼 비교해줘",
        "오재민 정우진 평가 비교해줘",
        "박시우랑 장서진 상태 비교해줘",
        "두 선수 최근 경기 기록 비교해줘",
        "오재민 vs 정우진 비교해줘",
        "오재민이랑 정우진 누가 더 폼 좋아?",
        "두 선수 최근 21일 load 비교해줘",
        "오재민 장서진 최근 평가 같이 봐줘",
        "박시우 vs 장서진 최근 경기 지표 비교해줘",
    ],
    "opponent_match_lookup": [
        "현대고 상대 최근 경기 결과 알려줘",
        "수원공고 U18 상대로 최근 경기 어땠어",
        "전북현대 U18 상대 전적 보여줘",
        "현대고전 요약해줘",
        "특정 상대팀 경기 결과 알려줘",
        "상대팀 기준 경기 요약 보여줘",
        "현대고 상대로 최근 3경기 흐름 알려줘",
        "수원공고 U18전 팀 지표 요약해줘",
        "특정 상대팀 상대 슈팅 지표 알려줘",
        "상대팀별 최근 경기 브리핑해줘",
    ],
}


QUERY_PLAYBOOKS: list[dict[str, Any]] = [
    {
        "name": "pre_injury_workload_analysis",
        "keywords": [
            "부상이전",
            "부상 이전",
            "다치기전",
            "다치기 전",
            "부상전",
            "부상 전",
            "훈련량",
            "강도",
            "부하",
            "워크로드",
            "load",
            "intensity",
        ],
        "guidance": [
            "For pre-injury workload analysis, compare the 7 days before injury against an earlier baseline window.",
            "Use football.player_current_injury_status or football.injuries to identify the injury_date, then compare football.training_gps_stats + football.trainings and football.player_match_facts before that date.",
            "Do not answer with the current injury roster when the user is asking about pre-injury load, intensity, or workload spikes.",
        ],
        "preferred_objects": [
            "football.player_current_injury_status",
            "football.injuries",
            "football.training_gps_stats",
            "football.trainings",
            "football.player_match_facts",
            "football.players",
        ],
        "example_sql": (
            "WITH target_injury AS ("
            " SELECT player_id, name, injury_date"
            " FROM football.player_current_injury_status"
            " WHERE injury_id IS NOT NULL AND actual_return_date IS NULL"
            " ORDER BY injury_date DESC"
            " LIMIT 1"
            "), training_window AS ("
            " SELECT AVG(tgs.total_distance) AS pre7_avg_distance"
            " FROM football.training_gps_stats AS tgs"
            " JOIN football.trainings AS t ON t.training_id = tgs.training_id"
            " JOIN target_injury AS ti ON ti.player_id = tgs.player_id"
            " WHERE t.training_date >= ti.injury_date - INTERVAL '7 days'"
            "   AND t.training_date < ti.injury_date"
            ") "
            "SELECT * FROM training_window"
        ),
    },
    {
        "name": "injury_cause_analysis",
        "keywords": ["부상원인", "부상 원인", "원인분석", "원인 분석", "injury cause", "왜다쳤", "왜 다쳤", "메커니즘"],
        "guidance": [
            "For injury cause analysis, use football.injuries joined to football.players.",
            "Prefer the latest injury row for the named player, ordered by injury_date DESC.",
            "Use injury_mechanism, occurred_during, and notes as the primary evidence. Do not speculate beyond the stored records.",
        ],
        "preferred_objects": [
            "football.injuries",
            "football.players",
        ],
        "example_sql": (
            "SELECT p.player_id, p.name, i.injury_date, i.injury_type, i.injury_part, "
            "i.severity_level, i.status, i.injury_mechanism, i.occurred_during, i.notes "
            "FROM football.injuries AS i "
            "JOIN football.players AS p ON p.player_id = i.player_id "
            "WHERE p.name = 'TARGET_PLAYER_NAME' "
            "ORDER BY i.injury_date DESC "
            "LIMIT 1"
        ),
    },
    {
        "name": "latest_official_match_activity_leader",
        "keywords": ["공식경기", "공식 경기", "공식전", "official match", "최근공식경기", "가장최근공식경기"],
        "guidance": [
            "For latest official-match activity leaders, isolate the latest football.matches row where match_type = '공식'.",
            "Then join football.player_match_facts on match_id and order by total_distance DESC NULLS LAST, then sprint_count DESC NULLS LAST.",
            "Do not answer from the latest overall match if that match_type is '연습'.",
        ],
        "preferred_objects": [
            "football.player_match_facts",
            "football.matches",
        ],
        "example_sql": (
            "WITH latest_official_match AS ("
            " SELECT match_id, match_date"
            " FROM football.matches"
            " WHERE match_type = '공식'"
            " ORDER BY match_date DESC"
            " LIMIT 1"
            ") "
            "SELECT pmf.player_id, pmf.player_name, pmf.total_distance, pmf.sprint_count, pmf.minutes_played "
            "FROM football.player_match_facts AS pmf "
            "JOIN latest_official_match AS lom ON lom.match_id = pmf.match_id "
            "ORDER BY pmf.total_distance DESC NULLS LAST, pmf.sprint_count DESC NULLS LAST "
            "LIMIT 5"
        ),
    },
    {
        "name": "latest_match_activity_leader",
        "keywords": ["가장최근경기", "최근경기", "최근 경기", "활동량", "distance", "스프린트"],
        "guidance": [
            "For latest-match activity leaders, prefer football.player_match_facts.",
            "Use football.matches only to isolate the latest match_id, then join football.player_match_facts on match_id.",
            "Order by total_distance DESC NULLS LAST, then sprint_count DESC NULLS LAST when answering 활동량 questions.",
        ],
        "preferred_objects": [
            "football.player_match_facts",
            "football.matches",
        ],
        "example_sql": (
            "WITH latest_match AS ("
            " SELECT match_id, match_date"
            " FROM football.matches"
            " ORDER BY match_date DESC"
            " LIMIT 1"
            ") "
            "SELECT pmf.player_id, pmf.player_name, pmf.total_distance, pmf.sprint_count, pmf.minutes_played "
            "FROM football.player_match_facts AS pmf "
            "JOIN latest_match AS lm ON lm.match_id = pmf.match_id "
            "ORDER BY pmf.total_distance DESC NULLS LAST, pmf.sprint_count DESC NULLS LAST "
            "LIMIT 5"
        ),
    },
    {
        "name": "recent_match_form",
        "keywords": ["폼", "요즘", "최근폼", "최근 폼", "recent form"],
        "guidance": [
            "For recent form, aggregate football.player_match_facts over a recent 14- to 28-day window or recent matches.",
            "Use AVG or SUM with explicit windows rather than guessing.",
        ],
        "preferred_objects": [
            "football.player_match_facts",
            "football.matches",
        ],
        "example_sql": (
            "SELECT pmf.player_id, pmf.player_name, COUNT(*) AS recent_matches, "
            "AVG(pmf.total_distance) AS avg_total_distance, AVG(pmf.sprint_count) AS avg_sprint_count "
            "FROM football.player_match_facts AS pmf "
            "WHERE pmf.match_date >= CURRENT_DATE - INTERVAL '21 days' "
            "GROUP BY pmf.player_id, pmf.player_name "
            "ORDER BY avg_total_distance DESC NULLS LAST "
            "LIMIT 10"
        ),
    },
    {
        "name": "current_injury_watch",
        "keywords": [
            "부상",
            "재활",
            "복귀",
            "부상상태",
            "부상 상태",
            "재활중",
            "재활 중",
            "결장",
            "출전 불가",
            "가용",
            "injury",
            "rehab",
            "availability",
        ],
        "guidance": [
            "For current injury or rehab status, prefer football.player_current_injury_status over raw football.injuries.",
            "Use football.injuries only for historical or trend questions.",
        ],
        "preferred_objects": [
            "football.player_current_injury_status",
            "football.injuries",
            "football.players",
        ],
        "example_sql": (
            "SELECT player_id, name, injury_type, injury_part, severity_level, injury_status, expected_return_date "
            "FROM football.player_current_injury_status "
            "WHERE injury_id IS NOT NULL "
            "ORDER BY expected_return_date NULLS LAST, injury_date DESC "
            "LIMIT 10"
        ),
    },
    {
        "name": "training_load",
        "keywords": ["훈련", "training", "부하", "load", "훈련량"],
        "guidance": [
            "For training load questions, use football.training_gps_stats joined to football.trainings.",
            "Do not mix match and training workload unless the user explicitly asks for combined workload.",
        ],
        "preferred_objects": [
            "football.training_gps_stats",
            "football.trainings",
            "football.players",
        ],
        "example_sql": (
            "SELECT t.training_date, p.player_id, p.name, tgs.total_distance, tgs.sprint_count, tgs.accel_count "
            "FROM football.training_gps_stats AS tgs "
            "JOIN football.trainings AS t ON t.training_id = tgs.training_id "
            "JOIN football.players AS p ON p.player_id = tgs.player_id "
            "WHERE t.training_date >= CURRENT_DATE - INTERVAL '14 days' "
            "ORDER BY t.training_date DESC, tgs.total_distance DESC NULLS LAST "
            "LIMIT 20"
        ),
    },
    {
        "name": "combined_workload_summary",
        "keywords": [
            "경기훈련",
            "경기 훈련",
            "경기와훈련",
            "경기와 훈련",
            "경기랑훈련",
            "경기랑 훈련",
            "통합부하",
            "통합 부하",
            "합산부하",
            "합산 부하",
            "combined workload",
            "overall load",
            "acute chronic",
            "acwr",
        ],
        "guidance": [
            "For combined workload questions, unify football.training_gps_stats + football.trainings with football.match_gps_stats + football.matches into one session timeline per player.",
            "When the user asks about spikes, overload, or workload risk, compare the recent 7-day acute load against a prior 21-day baseline.",
            "Do not answer from only training or only match data when the question explicitly asks for combined workload.",
        ],
        "preferred_objects": [
            "football.training_gps_stats",
            "football.trainings",
            "football.match_gps_stats",
            "football.matches",
            "football.players",
        ],
        "example_sql": (
            "WITH sessions AS ("
            " SELECT tgs.player_id, t.training_date AS session_date, 'training' AS session_source, tgs.total_distance, tgs.sprint_count"
            " FROM football.training_gps_stats AS tgs"
            " JOIN football.trainings AS t ON t.training_id = tgs.training_id"
            " UNION ALL "
            " SELECT mgs.player_id, m.match_date AS session_date, 'match' AS session_source, mgs.total_distance, mgs.sprint_count"
            " FROM football.match_gps_stats AS mgs"
            " JOIN football.matches AS m ON m.match_id = mgs.match_id"
            ") "
            "SELECT player_id, COUNT(*) AS sessions_7d, SUM(total_distance) AS total_distance_7d "
            "FROM sessions "
            "WHERE session_date >= CURRENT_DATE - INTERVAL '7 days' "
            "GROUP BY player_id "
            "LIMIT 10"
        ),
    },
    {
        "name": "position_availability_summary",
        "keywords": [
            "포지션가용",
            "포지션 가용",
            "가용인원",
            "가용 인원",
            "포지션별부상",
            "포지션별 부상",
            "결장",
            "출전가능",
            "출전 가능",
            "라인업",
            "availability risk",
            "position availability",
        ],
        "guidance": [
            "For position availability questions, start from football.players and overlay football.player_current_injury_status.",
            "Treat players with injury_id IS NOT NULL and actual_return_date IS NULL as currently unavailable.",
            "If a specific position is named, filter primary_position or secondary_position and summarize unavailable players plus expected return dates.",
        ],
        "preferred_objects": [
            "football.players",
            "football.player_current_injury_status",
        ],
        "example_sql": (
            "SELECT p.primary_position, COUNT(*) AS roster_count, "
            "COUNT(*) FILTER (WHERE pcis.injury_id IS NOT NULL AND pcis.actual_return_date IS NULL) AS unavailable_count "
            "FROM football.players AS p "
            "LEFT JOIN football.player_current_injury_status AS pcis ON pcis.player_id = p.player_id "
            "GROUP BY p.primary_position "
            "ORDER BY unavailable_count DESC, roster_count ASC"
        ),
    },
    {
        "name": "player_profile_summary",
        "keywords": ["프로필", "선수정보", "선수 정보", "기본정보", "기본 정보", "등번호", "포지션", "국적", "주발", "profile"],
        "guidance": [
            "For player profile summaries, resolve the player first and then combine football.players with football.player_latest_physical_profile and football.player_current_injury_status.",
            "Use latest football.evaluations and football.counseling_notes only as concise supporting context.",
            "Do not speculate beyond the stored roster, injury, physical, evaluation, and counseling records.",
        ],
        "preferred_objects": [
            "football.players",
            "football.player_latest_physical_profile",
            "football.player_current_injury_status",
            "football.evaluations",
            "football.counseling_notes",
        ],
        "example_sql": (
            "SELECT p.name, p.jersey_number, p.primary_position, p.secondary_position, p.foot, p.nationality, p.status, "
            "plpp.height_cm, plpp.weight_kg, plpp.body_fat_percentage, plpp.muscle_mass_kg, pcis.injury_status "
            "FROM football.players AS p "
            "LEFT JOIN football.player_latest_physical_profile AS plpp ON plpp.player_id = p.player_id "
            "LEFT JOIN football.player_current_injury_status AS pcis ON pcis.player_id = p.player_id "
            "WHERE p.name = 'TARGET_PLAYER_NAME' "
            "LIMIT 1"
        ),
    },
    {
        "name": "physical_change_analysis",
        "keywords": ["피지컬", "체성분", "체중", "체지방", "근육량", "bmi", "physical", "체력테스트", "체력 테스트"],
        "guidance": [
            "For physical change analysis, compare the latest football.physical_profiles row with the previous row for the same player.",
            "If the user asks about speed, jump, or agility, also compare the latest football.physical_tests row with the previous test row.",
            "Use exact stored measurements and deltas rather than vague judgments.",
        ],
        "preferred_objects": [
            "football.physical_profiles",
            "football.player_latest_physical_profile",
            "football.physical_tests",
            "football.players",
        ],
        "example_sql": (
            "WITH ranked_profiles AS ("
            " SELECT player_id, created_at, weight_kg, body_fat_percentage, muscle_mass_kg, bmi, "
            "ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY created_at DESC) AS rn "
            "FROM football.physical_profiles"
            ") "
            "SELECT * FROM ranked_profiles WHERE player_id = 'TARGET_PLAYER_ID' AND rn <= 2"
        ),
    },
    {
        "name": "evaluation_summary",
        "keywords": ["평가", "평가점수", "코치평가", "코치 평가", "coach comment", "technical", "tactical", "mental", "evaluation"],
        "guidance": [
            "For player evaluation summaries, use football.evaluations ordered by evaluation_date DESC.",
            "Summarize the latest technical, tactical, physical, and mental scores and compare to the previous evaluation when available.",
            "Treat coach_comment as supporting evidence, not as a substitute for the recorded scores.",
        ],
        "preferred_objects": [
            "football.evaluations",
            "football.players",
        ],
        "example_sql": (
            "SELECT p.name, e.evaluation_date, e.technical, e.tactical, e.physical, e.mental, e.coach_comment "
            "FROM football.evaluations AS e "
            "JOIN football.players AS p ON p.player_id = e.player_id "
            "WHERE p.name = 'TARGET_PLAYER_NAME' "
            "ORDER BY e.evaluation_date DESC "
            "LIMIT 2"
        ),
    },
    {
        "name": "counseling_summary",
        "keywords": ["상담", "상담노트", "상담 노트", "멘탈", "counseling", "상담기록", "상담 기록"],
        "guidance": [
            "For counseling summaries, use football.counseling_notes ordered by counseling_date DESC.",
            "Summarize the latest note first, then mention repeated recent topics or themes from the last few notes.",
            "Do not infer clinical meaning beyond the stored topic and summary text.",
        ],
        "preferred_objects": [
            "football.counseling_notes",
            "football.players",
        ],
        "example_sql": (
            "SELECT p.name, c.counseling_date, c.topic, c.summary "
            "FROM football.counseling_notes AS c "
            "JOIN football.players AS p ON p.player_id = c.player_id "
            "WHERE p.name = 'TARGET_PLAYER_NAME' "
            "ORDER BY c.counseling_date DESC "
            "LIMIT 3"
        ),
    },
    {
        "name": "player_recent_match_summary",
        "keywords": ["최근 경기", "직전 경기", "마지막 경기", "경기 요약", "경기 기록", "match summary", "stats"],
        "guidance": [
            "For player recent-match summaries, resolve the player first and use football.player_match_facts ordered by match_date DESC.",
            "If the question specifies official matches, filter match_type = '공식'.",
            "Summarize the latest one to three matches using stored technical and workload fields.",
        ],
        "preferred_objects": [
            "football.player_match_facts",
            "football.players",
            "football.matches",
        ],
        "example_sql": (
            "SELECT player_name, match_date, match_type, opponent_team, minutes_played, goals, assists, shots, "
            "pass_accuracy, total_distance, sprint_count "
            "FROM football.player_match_facts "
            "WHERE player_name = 'TARGET_PLAYER_NAME' "
            "ORDER BY match_date DESC "
            "LIMIT 3"
        ),
    },
    {
        "name": "player_recent_training_summary",
        "keywords": ["최근 훈련", "직전 훈련", "마지막 훈련", "훈련 요약", "훈련 기록", "training summary", "세션 기록"],
        "guidance": [
            "For player recent-training summaries, resolve the player first and use football.training_gps_stats joined to football.trainings.",
            "Order by training_date DESC and summarize the latest one to three sessions.",
            "Use session_name, training_focus, intensity_level, total_distance, sprint_count, accel_count, and decel_count when available.",
        ],
        "preferred_objects": [
            "football.training_gps_stats",
            "football.trainings",
            "football.players",
        ],
        "example_sql": (
            "SELECT p.name, t.training_date, t.session_name, t.training_focus, t.intensity_level, "
            "tgs.total_distance, tgs.sprint_count, tgs.accel_count, tgs.decel_count "
            "FROM football.training_gps_stats AS tgs "
            "JOIN football.trainings AS t ON t.training_id = tgs.training_id "
            "JOIN football.players AS p ON p.player_id = tgs.player_id "
            "WHERE p.name = 'TARGET_PLAYER_NAME' "
            "ORDER BY t.training_date DESC "
            "LIMIT 3"
        ),
    },
    {
        "name": "return_to_play_timeline",
        "keywords": ["복귀예정", "복귀 예정", "언제복귀", "언제 복귀", "expected return", "return timeline", "돌아와"],
        "guidance": [
            "For return-to-play timeline questions, prefer football.player_current_injury_status.",
            "If the player is named, show the current injury status and expected_return_date for that player.",
            "If the question is team-wide, list the currently unavailable players ordered by expected_return_date ASC NULLS LAST.",
        ],
        "preferred_objects": [
            "football.player_current_injury_status",
            "football.players",
        ],
        "example_sql": (
            "SELECT name, injury_date, injury_type, injury_status, expected_return_date "
            "FROM football.player_current_injury_status "
            "WHERE injury_id IS NOT NULL AND actual_return_date IS NULL "
            "ORDER BY expected_return_date ASC NULLS LAST "
            "LIMIT 10"
        ),
    },
    {
        "name": "physical_leaderboard",
        "keywords": ["체중", "체지방", "근육량", "bmi", "피지컬 순위", "physical leaderboard", "ranking"],
        "guidance": [
            "For current body-composition leaderboards, use football.player_latest_physical_profile.",
            "Pick the ordering metric from the question: weight_kg, body_fat_percentage, muscle_mass_kg, or bmi.",
            "Use DESC or ASC according to whether the user asks for the highest or lowest values.",
        ],
        "preferred_objects": [
            "football.player_latest_physical_profile",
            "football.players",
        ],
        "example_sql": (
            "SELECT name, weight_kg, body_fat_percentage, bmi, muscle_mass_kg "
            "FROM football.player_latest_physical_profile "
            "ORDER BY muscle_mass_kg DESC NULLS LAST "
            "LIMIT 5"
        ),
    },
    {
        "name": "physical_test_leaderboard",
        "keywords": ["10m", "30m", "점프", "민첩", "agility", "physical test", "스프린트 테스트"],
        "guidance": [
            "For physical-test leaderboards, use football.physical_tests from the latest test_date.",
            "Pick the ordering metric from the question, such as sprint_10m, sprint_30m, vertical_jump_cm, or agility_t_test_sec.",
            "Lower is better for sprint and agility times; higher is better for jump height unless the user asks for the opposite.",
        ],
        "preferred_objects": [
            "football.physical_tests",
            "football.players",
        ],
        "example_sql": (
            "SELECT p.name, pt.test_date, pt.sprint_10m, pt.sprint_30m, pt.vertical_jump_cm, pt.agility_t_test_sec "
            "FROM football.physical_tests AS pt "
            "JOIN football.players AS p ON p.player_id = pt.player_id "
            "WHERE pt.test_date = (SELECT MAX(test_date) FROM football.physical_tests) "
            "ORDER BY pt.sprint_10m ASC NULLS LAST "
            "LIMIT 5"
        ),
    },
    {
        "name": "evaluation_leaderboard",
        "keywords": ["평가 순위", "technical", "tactical", "physical 점수", "mental 점수", "evaluation ranking", "코치 평가 순위"],
        "guidance": [
            "For evaluation leaderboards, use football.evaluations from the latest evaluation_date.",
            "Pick the ordering metric from the question: technical, tactical, physical, or mental.",
            "Use ASC or DESC depending on whether the user asks for the highest or lowest scores.",
        ],
        "preferred_objects": [
            "football.evaluations",
            "football.players",
        ],
        "example_sql": (
            "SELECT p.name, e.evaluation_date, e.technical, e.tactical, e.physical, e.mental "
            "FROM football.evaluations AS e "
            "JOIN football.players AS p ON p.player_id = e.player_id "
            "WHERE e.evaluation_date = (SELECT MAX(evaluation_date) FROM football.evaluations) "
            "ORDER BY e.physical DESC NULLS LAST "
            "LIMIT 5"
        ),
    },
    {
        "name": "counseling_topic_summary",
        "keywords": ["상담 주제", "상담 이슈", "topic ranking", "팀 전체 상담", "counseling theme", "멘탈 이슈"],
        "guidance": [
            "For team-wide counseling theme summaries, aggregate football.counseling_notes over a recent window anchored to the latest counseling_date.",
            "Group by topic and report counts plus the latest counseling_date per topic.",
            "Use summary text only as supporting context; do not infer beyond recorded topics and summaries.",
        ],
        "preferred_objects": [
            "football.counseling_notes",
            "football.players",
        ],
        "example_sql": (
            "SELECT topic, COUNT(*) AS note_count, MAX(counseling_date) AS latest_date "
            "FROM football.counseling_notes "
            "WHERE counseling_date >= (SELECT MAX(counseling_date) FROM football.counseling_notes) - INTERVAL '60 days' "
            "GROUP BY topic "
            "ORDER BY note_count DESC, latest_date DESC "
            "LIMIT 5"
        ),
    },
    {
        "name": "roster_lookup",
        "keywords": ["로스터", "명단", "목록", "포지션", "센터백", "골키퍼", "왼발", "오른발", "active 선수"],
        "guidance": [
            "For roster lookup questions, use football.players and filter by primary_position, secondary_position, foot, or status when the question specifies them.",
            "When the user asks for a position group, include players whose primary_position or secondary_position matches.",
            "Return a short list with name, jersey_number, and position context.",
        ],
        "preferred_objects": [
            "football.players",
        ],
        "example_sql": (
            "SELECT name, jersey_number, primary_position, secondary_position, foot, status "
            "FROM football.players "
            "WHERE primary_position = 'CB' OR secondary_position = 'CB' "
            "ORDER BY jersey_number ASC "
            "LIMIT 10"
        ),
    },
    {
        "name": "team_recent_match_summary",
        "keywords": ["팀 최근경기", "팀 최근 경기", "최근 경기 결과", "경기력", "팀 요약", "공식전 결과", "match summary"],
        "guidance": [
            "For team recent-match summaries, use football.matches joined to football.match_team_stats and football.opponent_teams.",
            "If the user asks about official matches, filter football.matches.match_type = '공식'.",
            "Summarize scoreline, possession, shots, shots_on_target, pass_accuracy, and duel_win_rate for the latest one to three matches.",
        ],
        "preferred_objects": [
            "football.matches",
            "football.match_team_stats",
            "football.opponent_teams",
        ],
        "example_sql": (
            "SELECT m.match_date, m.match_type, ot.opponent_team_name, m.goals_for, m.goals_against, m.possession_for, "
            "mts.shots, mts.shots_on_target, mts.pass_accuracy, mts.duel_win_rate "
            "FROM football.matches AS m "
            "LEFT JOIN football.opponent_teams AS ot ON ot.opponent_team_id = m.opponent_team_id "
            "LEFT JOIN football.match_team_stats AS mts ON mts.match_id = m.match_id "
            "ORDER BY m.match_date DESC "
            "LIMIT 3"
        ),
    },
    {
        "name": "position_recent_form",
        "keywords": ["포지션별 폼", "센터백", "풀백", "윙어", "스트라이커", "미드필더", "position form"],
        "guidance": [
            "For position recent-form questions, join football.player_match_facts to football.players and aggregate over a recent 21-day window anchored to the latest match_date.",
            "Filter by primary_position or secondary_position according to the position group in the question.",
            "Order by the requested metric such as avg_total_distance, avg_sprint_count, or avg_minutes.",
        ],
        "preferred_objects": [
            "football.player_match_facts",
            "football.players",
            "football.matches",
        ],
        "example_sql": (
            "WITH anchor AS (SELECT MAX(match_date) AS max_match_date FROM football.matches) "
            "SELECT pmf.player_name, COUNT(*) AS recent_matches, AVG(pmf.total_distance) AS avg_total_distance, AVG(pmf.sprint_count) AS avg_sprint_count "
            "FROM football.player_match_facts AS pmf "
            "JOIN football.players AS p ON p.player_id = pmf.player_id "
            "CROSS JOIN anchor AS a "
            "WHERE pmf.match_date > a.max_match_date - INTERVAL '21 days' AND (p.primary_position = 'CB' OR p.secondary_position = 'CB') "
            "GROUP BY pmf.player_id, pmf.player_name "
            "ORDER BY avg_total_distance DESC NULLS LAST "
            "LIMIT 5"
        ),
    },
    {
        "name": "player_comparison",
        "keywords": ["비교", "vs", "누가더", "누가 더", "비교해줘"],
        "guidance": [
            "For player comparison questions, resolve the two player names from the question first.",
            "Compare recent 21-day match workload and the latest evaluation scores for the two players.",
            "Do not compare unnamed players; if fewer than two names are present, ask for both player names explicitly.",
        ],
        "preferred_objects": [
            "football.players",
            "football.player_match_facts",
            "football.evaluations",
        ],
        "example_sql": (
            "WITH recent_matches AS ("
            " SELECT player_id, player_name, COUNT(*) AS recent_matches, AVG(total_distance) AS avg_total_distance, AVG(sprint_count) AS avg_sprint_count "
            " FROM football.player_match_facts "
            " WHERE player_name IN ('PLAYER_A', 'PLAYER_B') "
            " GROUP BY player_id, player_name"
            ") "
            "SELECT * FROM recent_matches"
        ),
    },
    {
        "name": "opponent_match_lookup",
        "keywords": ["상대팀", "상대로", "전적", "현대고전", "상대 경기", "상대 결과"],
        "guidance": [
            "For opponent-specific match lookups, resolve the opponent team name from the question using football.opponent_teams.",
            "Then query football.matches joined to football.match_team_stats and football.opponent_teams ordered by match_date DESC.",
            "Summarize the latest one to three matches against that opponent.",
        ],
        "preferred_objects": [
            "football.matches",
            "football.match_team_stats",
            "football.opponent_teams",
        ],
        "example_sql": (
            "SELECT m.match_date, m.match_type, ot.opponent_team_name, m.goals_for, m.goals_against, mts.shots, mts.shots_on_target "
            "FROM football.matches AS m "
            "JOIN football.opponent_teams AS ot ON ot.opponent_team_id = m.opponent_team_id "
            "LEFT JOIN football.match_team_stats AS mts ON mts.match_id = m.match_id "
            "WHERE ot.opponent_team_name = 'TARGET_OPPONENT_TEAM' "
            "ORDER BY m.match_date DESC "
            "LIMIT 3"
        ),
    },
]

COMMON_OBJECTS = (
    "football.player_match_facts",
    "football.player_current_injury_status",
    "football.player_latest_physical_profile",
    "football.players",
    "football.matches",
)


def select_relevant_schema_context(
    question: str,
    schema_catalog: dict[str, dict[str, Any]],
    *,
    object_limit: int = 6,
    playbook_limit: int = 3,
) -> dict[str, Any]:
    normalized_question = _normalize_search_text(question)
    matched_playbooks = _select_playbooks(question, normalized_question, limit=playbook_limit)
    preferred_objects = {
        object_name
        for playbook in matched_playbooks
        for object_name in playbook["preferred_objects"]
    }

    scored: list[tuple[int, str]] = []
    for object_name, details in schema_catalog.items():
        score = 0
        normalized_name = _normalize_search_text(object_name)
        if normalized_name in normalized_question or normalized_question in normalized_name:
            score += 2

        search_terms = list(details.get("keywords", []))
        search_terms.extend(details.get("preferred_for", []))
        search_terms.extend(details.get("column_names", []))

        for term in search_terms:
            normalized_term = _normalize_search_text(str(term))
            if normalized_term and normalized_term in normalized_question:
                score += 3

        if object_name in preferred_objects:
            score += 8
        if object_name in COMMON_OBJECTS:
            score += 1

        if score > 0:
            scored.append((score, object_name))

    selected_names = {name for _, name in sorted(scored, reverse=True)[:object_limit]}
    selected_names.update(name for name in COMMON_OBJECTS if name in schema_catalog)

    relevant_objects = []
    for object_name in sorted(selected_names):
        details = schema_catalog[object_name]
        relevant_objects.append(
            {
                "name": object_name,
                "type": details["table_type"],
                "description": details.get("description"),
                "preferred_for": details.get("preferred_for", []),
                "join_keys": details.get("join_keys", []),
                "warnings": details.get("warnings", []),
                "columns": details.get("column_names", []),
            }
        )

    return {
        "global_rules": [
            "Treat the schema catalog below as authoritative. Never invent a column that is not listed for that object.",
            "Prefer curated views such as football.player_match_facts, football.player_current_injury_status, and football.player_latest_physical_profile before raw tables when they fit the question.",
            "If you need match_date, opponent_team, or stadium context, use football.matches or football.player_match_facts instead of assuming those columns exist on football.player_match_stats.",
            "When a query playbook is present, stay close to its exact column names and example SQL shape instead of inventing a new query pattern.",
            "For injury cause analysis, use football.injuries because injury_mechanism and notes are stored there rather than on football.player_current_injury_status.",
            "For body-composition change questions, use football.physical_profiles or football.player_latest_physical_profile; for physical testing, use football.physical_tests.",
            "For coach evaluation questions, use football.evaluations. For counseling or mental-support notes, use football.counseling_notes.",
            "For roster lookup questions, use football.players. For player recent-match summaries, prefer football.player_match_facts. For player recent-training summaries, use football.training_gps_stats joined to football.trainings.",
            "For team recent-match summaries and opponent-specific match lookups, use football.matches plus football.match_team_stats and football.opponent_teams.",
        ],
        "relevant_objects": relevant_objects,
        "query_playbooks": matched_playbooks,
    }


def merge_schema_hints(
    object_name: str,
    *,
    table_type: str,
    column_names: list[str],
) -> dict[str, Any]:
    hint = SCHEMA_OBJECT_HINTS.get(object_name, {})
    return {
        "table_type": table_type,
        "description": hint.get("description", ""),
        "keywords": hint.get("keywords", []),
        "preferred_for": hint.get("preferred_for", []),
        "join_keys": hint.get("join_keys", []),
        "warnings": hint.get("warnings", []),
        "column_names": column_names,
    }


def _select_playbooks(
    question: str,
    normalized_question: str,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    scored: list[tuple[int, dict[str, Any], list[str]]] = []
    for playbook in QUERY_PLAYBOOKS:
        score = 0
        for keyword in playbook["keywords"]:
            normalized_keyword = _normalize_search_text(keyword)
            if normalized_keyword and normalized_keyword in normalized_question:
                score += 4
        example_score, matched_examples = _match_example_questions(question, normalized_question, playbook["name"])
        score += example_score
        if score > 0:
            scored.append((score, playbook, matched_examples))

    if not scored:
        return []

    ordered = sorted(scored, key=lambda item: item[0], reverse=True)
    top_score = ordered[0][0]
    cutoff = max(6, top_score - 6)
    selected = [item for item in ordered if item[0] >= cutoff][:limit]
    return [
        {
            "name": playbook["name"],
            "guidance": playbook["guidance"],
            "preferred_objects": playbook["preferred_objects"],
            "example_sql": playbook["example_sql"],
            "matched_examples": matched_examples,
        }
        for _, playbook, matched_examples in selected
    ]


def _match_example_questions(
    question: str,
    normalized_question: str,
    playbook_name: str,
    *,
    limit: int = 3,
) -> tuple[int, list[str]]:
    question_terms = _extract_informative_terms(question)
    scored_examples: list[tuple[int, str]] = []

    for example_question in PLAYBOOK_EXAMPLE_QUESTIONS.get(playbook_name, []):
        normalized_example = _normalize_search_text(example_question)
        score = 0
        if normalized_question == normalized_example:
            score += 20
        elif normalized_question in normalized_example or normalized_example in normalized_question:
            score += 10

        example_terms = _extract_informative_terms(example_question)
        overlap_terms = question_terms & example_terms
        if len(overlap_terms) >= 2:
            score += len(overlap_terms) * 4
        elif len(overlap_terms) == 1:
            overlap_term = next(iter(overlap_terms))
            if len(overlap_term) >= 4:
                score += 2

        if score >= 4:
            scored_examples.append((score, example_question))

    top_ranked = sorted(scored_examples, key=lambda item: item[0], reverse=True)[:limit]
    top_examples = [example for _, example in top_ranked]
    total_score = sum(score for score, _ in top_ranked)
    return total_score, top_examples
