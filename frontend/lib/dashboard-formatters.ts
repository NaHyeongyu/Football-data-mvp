const positionGroupLabels: Record<string, string> = {
  Attacker: "공격",
  Defender: "수비",
  Goalkeeper: "골키퍼",
  Midfielder: "미드필더",
};

const scoutPriorityLabels: Record<string, string> = {
  priority_shortlist: "우선 추적",
  strong_follow: "집중 관찰",
  monitor: "모니터링",
};

const riskBandLabels: Record<string, string> = {
  stable: "안정",
  managed: "집중 관리",
  red_flag: "긴급 점검",
};

const developmentFocusLabels: Record<string, string> = {
  availability_management: "가용성 관리",
  build_up_passing: "빌드업 패스",
  chance_creation: "찬스 메이킹",
  defensive_volume: "수비 볼륨",
  duel_security: "경합 안정성",
  final_third_output: "파이널 서드 생산성",
  match_exposure: "실전 노출",
  speed_power_development: "스피드·파워 강화",
};

const agentStorylineLabels: Record<string, string> = {
  "development trajectory is strong enough for early portfolio promotion":
    "성장 곡선이 안정적이라 조기 포트폴리오 노출 대상으로 검토할 수 있습니다.",
  "high-upside profile ready for proactive showcase conversations":
    "잠재치가 높아 선제적 쇼케이스 미팅에 올리기 적합한 프로필입니다.",
  "medical narrative needs tighter management before external push":
    "외부 노출 전 의료·가용성 관리 스토리를 먼저 정리할 필요가 있습니다.",
  "productive attacking profile with clear highlight-package value":
    "공격 생산성이 뚜렷해 하이라이트 패키지 가치가 분명한 유형입니다.",
  "stable development profile with selective exposure upside":
    "육성 흐름이 안정적이어서 선별적 외부 노출 시 반응을 기대할 수 있습니다.",
};

const scoutNoteLabels: Record<string, string> = {
  "depth or rotation profile worth periodic tracking":
    "로테이션 자원 관점에서 정기적으로 체크할 가치가 있습니다.",
  "priority follow-up profile with data-backed starter potential":
    "데이터상 선발 잠재력이 확인돼 우선 후속 관찰이 필요한 프로필입니다.",
  "quality is useful but medical validation is required":
    "기량은 충분하지만 메디컬 검증을 선행해야 합니다.",
  "trend line is positive and warrants continued live monitoring":
    "상승 추세가 뚜렷해 현장 관찰을 계속 이어갈 필요가 있습니다.",
};

const coachActionLabels: Record<string, string> = {
  "coordinate return-to-play load with role-specific technical work":
    "복귀 부하를 조절하면서 포지션 특화 기술 훈련을 병행해야 합니다.",
  "maintain role and sharpen top two development priorities":
    "현재 역할은 유지하되 핵심 개발 과제 두 개에 집중하는 편이 좋습니다.",
  "reduce complexity and reinforce core role actions":
    "플레이 과제를 단순화하고 역할 핵심 행동을 다시 강화할 필요가 있습니다.",
};

const managementActionLabels: Record<string, string> = {
  "expand competitive minutes to validate pathway decisions":
    "향후 경로 판단을 위해 경쟁 경기 출전 시간을 더 늘려볼 필요가 있습니다.",
  "keep in stable squad planning cycle":
    "현 스쿼드 운영 계획 안에서 안정적으로 관리하면 됩니다.",
  "place on medical or availability watchlist":
    "의무·가용성 워치리스트에 올려 우선 관리해야 합니다.",
};

const dominantFootLabels: Record<string, string> = {
  L: "왼발",
  R: "오른발",
  B: "양발",
};

const growthBandLabels: Record<string, string> = {
  accelerating: "가속 성장",
  positive: "상승 유지",
  monitor: "관찰 필요",
};

const fieldLabels: Record<string, string> = {
  season_id: "시즌 ID",
  season_year: "시즌 연도",
  matches: "경기 수",
  wins: "승",
  draws: "무",
  losses: "패",
  goals_for: "득점",
  goals_against: "실점",
  points: "승점",
  avg_goal_difference: "평균 득실차",
  win_rate_pct: "승률",
  points_per_match: "경기당 승점",
  goals_for_per_match: "경기당 득점",
  goals_against_per_match: "경기당 실점",
  registered_position: "등록 포지션",
  position_group: "포지션 그룹",
  players: "선수 수",
  average_age: "평균 연령",
  average_height_cm: "평균 신장(cm)",
  total_minutes: "총 출전 시간",
  average_scout_fit_score: "평균 스카우트 적합도",
  average_management_risk_score: "평균 운영 리스크",
  available_now: "즉시 가용 인원",
  availability_pct: "가용 비율",
  player_id: "선수 ID",
  player_name: "선수명",
  age_today: "현재 연령",
  grade: "학년",
  primary_role: "주 역할",
  dominant_foot: "주발",
  height_cm: "키(cm)",
  weight_kg: "체중(kg)",
  minutes: "출전 시간",
  minutes_share_pct: "출전 점유율",
  start_rate_pct: "선발 비율",
  goal_contrib_p90: "90분당 공격 관여",
  key_passes_p90: "90분당 키패스",
  pass_completion_pct: "패스 성공률",
  duel_win_pct: "경합 승률",
  max_speed_kmh: "최고 속도(km/h)",
  sprint_30m_sec_latest: "30m 스프린트(최근)",
  vertical_jump_cm_latest: "수직 점프(최근)",
  endurance_m_latest: "지구력(최근)",
  athletic_gain_score: "피지컬 상승 지수",
  growth_score: "성장 점수",
  latest_match_availability: "최신 경기 가용성",
  total_days_missed: "누적 결장일",
  mental_sessions: "멘탈 세션",
  market_value_score: "시장가치 지수",
  availability_risk_score: "가용성 리스크",
  agent_storyline: "에이전트 메모",
  performance_score: "퍼포먼스 점수",
  athletic_profile_score: "피지컬 프로필 점수",
  scout_fit_score: "스카우트 적합도",
  scout_priority: "스카우트 우선순위",
  scout_note: "스카우트 메모",
  role_count: "역할 수",
  role_alignment_pct: "역할 정합률",
  recent_form_score: "최근 폼 점수",
  player_load_p90: "90분당 부하",
  distance_total_p90: "90분당 총 거리",
  high_speed_m_p90: "90분당 고속 거리",
  coach_readiness_score: "코칭 준비도",
  development_focus_1: "개발 포인트 1",
  development_focus_2: "개발 포인트 2",
  coach_action: "코치 액션",
  at_events: "AT 이벤트",
  support_load_score: "지원 부하 점수",
  management_value_score: "운영 가치 점수",
  management_risk_score: "운영 리스크 점수",
  risk_band: "리스크 밴드",
  management_action: "운영 액션",
  latest_record_date: "최신 기록일",
  latest_status_type: "상태 유형",
  latest_injury_name: "최신 부상명",
  latest_injury_type: "부상 유형",
  latest_injury_grade: "부상 등급",
  latest_rehab_stage: "재활 단계",
  unavailable_events: "불가 이벤트",
  conditional_events: "조건부 이벤트",
  latest_return_to_play_date: "복귀 예정일",
  latest_training_participation: "훈련 참여 상태",
  match_id: "경기 ID",
  match_no: "라운드",
  match_date: "경기일",
  team_name: "팀명",
  opponent: "상대",
  venue: "장소",
  result: "결과",
  result_badge: "결과 배지",
  score: "스코어",
  match_label: "경기 라벨",
  key_player: "핵심 선수",
  key_player_role: "핵심 선수 역할",
  key_player_goals: "핵심 선수 득점",
  key_player_assists: "핵심 선수 도움",
  key_player_impact_score: "핵심 선수 영향 점수",
  season_match_count: "시즌 경기 수",
  appearances: "출전 경기 수",
  starts: "선발 경기 수",
  appearance_rate_pct: "출전율",
  goals: "득점",
  assists: "도움",
  goal_contrib: "공격 관여",
  saves_p90: "90분당 세이브",
  shots_on_target_p90: "90분당 유효 슈팅",
  duels_won_p90: "90분당 경합 승리",
  dribble_efficiency_pct: "드리블 효율",
  def_actions_p90: "90분당 수비 액션",
  sprint_count_p90: "90분당 스프린트 수",
  recent_minutes: "최근 출전 시간",
  recent_goal_contrib: "최근 공격 관여",
  discipline_risk: "징계 리스크",
  first_season_id: "첫 시즌 ID",
  latest_season_id: "최신 시즌 ID",
  minutes_first: "첫 시즌 출전 시간",
  minutes_latest: "최신 시즌 출전 시간",
  minutes_delta: "출전 시간 변화",
  goal_contrib_p90_first: "첫 시즌 90분당 공격 관여",
  goal_contrib_p90_latest: "최신 시즌 90분당 공격 관여",
  goal_contrib_p90_delta: "공격 관여 변화",
  pass_completion_pct_delta: "패스 성공률 변화",
  duel_win_pct_delta: "경합 승률 변화",
  recent_form_delta: "최근 폼 변화",
  growth_band: "성장 밴드",
  latest_test_date: "최신 테스트일",
  latest_test_count: "테스트 횟수",
  height_cm_latest: "최신 신장(cm)",
  weight_kg_latest: "최신 체중(kg)",
  skeletal_muscle_kg_latest: "최신 골격근량(kg)",
  body_fat_pct_latest: "최신 체지방률",
  sprint_10m_sec_latest: "10m 스프린트(최근)",
  sprint_50m_sec_latest: "50m 스프린트(최근)",
  sprint_100m_sec_latest: "100m 스프린트(최근)",
  shuttle_run_count_latest: "셔틀런 횟수(최근)",
  agility_t_sec_latest: "T-Agility(최근)",
  shuttle_run_sec_latest: "셔틀런(최근)",
  flexibility_cm_latest: "유연성(최근)",
  height_delta: "신장 변화",
  weight_delta: "체중 변화",
  skeletal_muscle_delta: "골격근량 변화",
  body_fat_delta: "체지방률 변화",
  sprint_10m_delta: "10m 스프린트 변화",
  sprint_30m_delta: "30m 스프린트 변화",
  sprint_50m_delta: "50m 스프린트 변화",
  sprint_100m_delta: "100m 스프린트 변화",
  vertical_jump_delta: "수직 점프 변화",
  agility_delta: "민첩성 변화",
  shuttle_run_count_delta: "셔틀런 횟수 변화",
  shuttle_run_delta: "셔틀런 변화",
  endurance_delta: "지구력 변화",
  flexibility_delta: "유연성 변화",
  best_shuttle_run_count: "최고 셔틀런 횟수",
  best_sprint_50m_sec: "최고 50m 스프린트",
  best_sprint_100m_sec: "최고 100m 스프린트",
  best_shuttle_run_sec: "최고 셔틀런",
  best_sprint_30m_sec: "최고 30m 스프린트",
  best_vertical_jump_cm: "최고 수직 점프(cm)",
  best_endurance_m: "최고 지구력(m)",
};

export function formatPositionGroup(value: string) {
  return positionGroupLabels[value] ?? value;
}

export function formatScoutPriority(value: string) {
  return scoutPriorityLabels[value] ?? toStartCase(value);
}

export function formatRiskBand(value: string) {
  return riskBandLabels[value] ?? toStartCase(value);
}

export function formatDevelopmentFocus(value: string) {
  return developmentFocusLabels[value] ?? toStartCase(value);
}

export function formatAgentStoryline(value: string) {
  return agentStorylineLabels[value] ?? value;
}

export function formatScoutNote(value: string) {
  return scoutNoteLabels[value] ?? value;
}

export function formatCoachAction(value: string) {
  return coachActionLabels[value] ?? value;
}

export function formatManagementAction(value: string) {
  return managementActionLabels[value] ?? value;
}

export function formatDominantFoot(value: string) {
  return dominantFootLabels[value] ?? value;
}

export function formatGrowthBand(value: string) {
  return growthBandLabels[value] ?? toStartCase(value);
}

export function formatFieldLabel(value: string) {
  return fieldLabels[value] ?? toStartCase(value);
}

export function formatMetricValue(key: string, value: number) {
  if (Number.isNaN(value)) {
    return "-";
  }

  if (key.endsWith("_pct")) {
    return `${value.toFixed(1)}%`;
  }

  if (key.endsWith("_delta")) {
    const precision = Math.abs(value) < 10 ? 2 : 1;
    const sign = value > 0 ? "+" : "";
    return `${sign}${value.toFixed(precision)}`;
  }

  if (Number.isInteger(value)) {
    return value.toLocaleString("ko-KR");
  }

  return value.toLocaleString("ko-KR", {
    maximumFractionDigits: 2,
    minimumFractionDigits: Math.abs(value) < 10 ? 1 : 0,
  });
}

export function formatCompactDate(value: string) {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(parsed);
}

export function toStartCase(value: string) {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}
