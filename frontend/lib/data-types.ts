export type DashboardSummary = {
  latestSeasonId: string;
  latestSeasonYear: number;
  playerCount: number;
  seasonCount: number;
  matchCount: number;
  latestSeasonPoints: number;
  latestSeasonWinRatePct: number;
  latestSeasonGoalsFor: number;
  latestSeasonGoalsAgainst: number;
  latestSeasonGoalsForPerMatch: number;
  latestSeasonGoalsAgainstPerMatch: number;
  priorityShortlistCount: number;
  managedRiskCount: number;
  availableNowCount: number;
};

export type SeasonTrendItem = {
  season_id: string;
  matches: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  points: number;
  avg_goal_difference: number;
  season_year: number;
  win_rate_pct: number;
  points_per_match: number;
  goals_for_per_match: number;
  goals_against_per_match: number;
};

export type MarketLeader = {
  player_id: string;
  player_name: string;
  age_today: number;
  grade: number;
  registered_position: string;
  primary_role: string;
  position_group: string;
  dominant_foot: string;
  height_cm: number;
  weight_kg: number;
  minutes: number;
  minutes_share_pct: number;
  start_rate_pct: number;
  goal_contrib_p90: number;
  key_passes_p90: number;
  pass_completion_pct: number;
  duel_win_pct: number;
  max_speed_kmh: number;
  sprint_30m_sec_latest: number;
  vertical_jump_cm_latest: number;
  endurance_m_latest: number;
  athletic_gain_score: number;
  growth_score: number;
  latest_match_availability: string;
  total_days_missed: number;
  mental_sessions: number;
  market_value_score: number;
  availability_risk_score: number;
  agent_storyline: string;
};

export type ScoutShortlistItem = {
  player_id: string;
  player_name: string;
  age_today: number;
  grade: number;
  registered_position: string;
  primary_role: string;
  position_group: string;
  latest_match_availability: string;
  performance_score: number;
  athletic_profile_score: number;
  scout_fit_score: number;
  scout_priority: string;
  growth_score: number;
  scout_note: string;
};

export type CoachFocusItem = {
  player_id: string;
  player_name: string;
  registered_position: string;
  primary_role: string;
  minutes: number;
  minutes_share_pct: number;
  start_rate_pct: number;
  role_count: number;
  role_alignment_pct: number;
  recent_form_score: number;
  player_load_p90: number;
  distance_total_p90: number;
  high_speed_m_p90: number;
  latest_match_availability: string;
  total_days_missed: number;
  coach_readiness_score: number;
  development_focus_1: string;
  development_focus_2: string;
  coach_action: string;
};

export type ManagementBoardItem = {
  player_id: string;
  player_name: string;
  age_today: number;
  grade: number;
  registered_position: string;
  minutes_share_pct: number;
  performance_score: number;
  growth_score: number;
  latest_match_availability: string;
  availability_risk_score: number;
  total_days_missed: number;
  at_events: number;
  mental_sessions: number;
  support_load_score: number;
  management_value_score: number;
  management_risk_score: number;
  risk_band: string;
  management_action: string;
};

export type MedicalRiskItem = {
  player_id: string;
  player_name: string;
  registered_position: string;
  latest_record_date: string | null;
  latest_status_type: string;
  latest_injury_name: string | null;
  latest_injury_type: string | null;
  latest_injury_grade: string | null;
  latest_rehab_stage: string | null;
  latest_match_availability: string;
  total_days_missed: number;
  unavailable_events: number;
  conditional_events: number;
  availability_risk_score: number;
  latest_return_to_play_date: string | null;
  latest_training_participation: string | null;
};

export type PositionDepthItem = {
  registered_position: string;
  position_group: string;
  players: number;
  average_age: number;
  average_height_cm: number;
  total_minutes: number;
  average_scout_fit_score: number;
  average_management_risk_score: number;
  available_now: number;
  availability_pct: number;
};

export type RecentMatchItem = {
  match_id: string;
  season_id: string;
  match_no: number;
  match_date: string;
  team_name: string;
  opponent: string;
  venue: string;
  result: string;
  result_badge: string;
  score: string;
  match_label: string;
  key_player: string;
  key_player_role: string;
  key_player_goals: number;
  key_player_assists: number;
  key_player_impact_score: number;
};

export type PlayerSeasonSummaryItem = {
  player_id: string;
  player_name: string;
  season_id: string;
  season_year: number;
  registered_position: string;
  primary_role: string;
  position_group: string;
  grade: number;
  age_today: number;
  season_match_count: number;
  appearances: number;
  starts: number;
  minutes: number;
  appearance_rate_pct: number;
  start_rate_pct: number;
  minutes_share_pct: number;
  goals: number;
  assists: number;
  goal_contrib: number;
  goal_contrib_p90: number;
  saves_p90: number;
  shots_on_target_p90: number;
  key_passes_p90: number;
  duels_won_p90: number;
  pass_completion_pct: number;
  dribble_efficiency_pct: number;
  duel_win_pct: number;
  def_actions_p90: number;
  distance_total_p90: number;
  high_speed_m_p90: number;
  max_speed_kmh: number;
  sprint_count_p90: number;
  player_load_p90: number;
  role_count: number;
  role_alignment_pct: number;
  recent_form_score: number;
  recent_minutes: number;
  recent_goal_contrib: number;
  discipline_risk: number;
};

export type PlayerGrowthTrendItem = {
  player_id: string;
  player_name: string;
  registered_position: string;
  position_group: string;
  first_season_id: string;
  latest_season_id: string;
  minutes_first: number;
  minutes_latest: number;
  minutes_delta: number;
  goal_contrib_p90_first: number;
  goal_contrib_p90_latest: number;
  goal_contrib_p90_delta: number;
  pass_completion_pct_delta: number;
  duel_win_pct_delta: number;
  recent_form_delta: number;
  growth_score: number;
  growth_band: string;
};

export type PhysicalProgressItem = {
  player_id: string;
  player_name: string;
  registered_position: string;
  position_group: string;
  latest_test_date: string;
  latest_test_count: number;
  height_cm_latest: number;
  weight_kg_latest: number;
  skeletal_muscle_kg_latest: number;
  body_fat_pct_latest: number;
  sprint_10m_sec_latest: number;
  sprint_30m_sec_latest: number;
  sprint_50m_sec_latest: number;
  sprint_100m_sec_latest: number;
  vertical_jump_cm_latest: number;
  agility_t_sec_latest: number;
  shuttle_run_count_latest: number;
  shuttle_run_sec_latest: number;
  endurance_m_latest: number;
  flexibility_cm_latest: number;
  height_delta: number;
  weight_delta: number;
  skeletal_muscle_delta: number;
  body_fat_delta: number;
  sprint_10m_delta: number;
  sprint_30m_delta: number;
  sprint_50m_delta: number;
  sprint_100m_delta: number;
  vertical_jump_delta: number;
  agility_delta: number;
  shuttle_run_count_delta: number;
  shuttle_run_delta: number;
  endurance_delta: number;
  flexibility_delta: number;
  best_shuttle_run_count: number;
  best_sprint_50m_sec: number;
  best_sprint_100m_sec: number;
  best_shuttle_run_sec: number;
  best_sprint_30m_sec: number;
  best_vertical_jump_cm: number;
  best_endurance_m: number;
  athletic_gain_score: number;
};

export type ChartValuePoint = {
  label: string;
  value: number;
};

export type TeamMatchTrendItem = {
  match_id: string;
  season_id: string;
  match_no: number;
  match_date: string;
  match_label: string;
  opponent: string;
  venue: string;
  result: string;
  active_players: number;
  total_distance_km: number;
  total_high_speed_m: number;
  peak_max_speed_kmh: number;
  total_sprint_count: number;
  total_acceleration_count: number;
  total_deceleration_count: number;
  total_player_load: number;
  distance_total_p90: number;
  high_speed_m_p90: number;
  sprint_count_p90: number;
  acceleration_count_p90: number;
  deceleration_count_p90: number;
  player_load_p90: number;
  avg_max_speed_kmh: number;
};

export type PhysicalTestMetricKey =
  | "heightCm"
  | "weightKg"
  | "skeletalMuscleKg"
  | "bodyFatPct"
  | "sprint10mSec"
  | "sprint30mSec"
  | "sprint50mSec"
  | "sprint100mSec"
  | "verticalJumpCm"
  | "agilityTSec"
  | "shuttleRunCount";

export type PhysicalTestMetricValue = {
  current: number | null;
  previous: number | null;
  delta: number | null;
};

export type PhysicalTestSessionRow = {
  playerId: string;
  playerName: string;
  registeredPosition: string;
  metrics: Record<PhysicalTestMetricKey, PhysicalTestMetricValue>;
};

export type PhysicalTestSessionView = {
  key: string;
  testDate: string;
  testRound: number;
  seasonYear: number;
  playerCount: number;
  rows: PhysicalTestSessionRow[];
};

export type PositionSnapshotItem = {
  registered_position: string;
  position_group: string;
  players: number;
  avg_minutes_share_pct: number;
  avg_player_load_p90: number;
  avg_sprint_count_p90: number;
  avg_recent_form_score: number;
  avg_growth_score: number;
  avg_availability_risk_score: number;
};

export type DashboardVisualizations = {
  kpiSeries: {
    playerCountBySeason: ChartValuePoint[];
    matchesBySeason: ChartValuePoint[];
    averageMinutesShareBySeason: ChartValuePoint[];
    averageSprintCountBySeason: ChartValuePoint[];
    riskDistribution: ChartValuePoint[];
    positionAvailability: ChartValuePoint[];
  };
  teamMatchTrend: TeamMatchTrendItem[];
  positionSnapshot: PositionSnapshotItem[];
};

export type DashboardDatasets = {
  teamSeasonSummary: SeasonTrendItem[];
  positionDepth: PositionDepthItem[];
  agentBoard: MarketLeader[];
  scoutBoard: ScoutShortlistItem[];
  coachBoard: CoachFocusItem[];
  managementBoard: ManagementBoardItem[];
  medicalAvailability: MedicalRiskItem[];
  playerSeasonSummary: PlayerSeasonSummaryItem[];
  playerGrowthTrend: PlayerGrowthTrendItem[];
  physicalProgress: PhysicalProgressItem[];
  matchGpsSummary: TeamMatchTrendItem[];
  matchLog: RecentMatchItem[];
};

export type DashboardPayload = {
  generatedOn: string;
  summary: DashboardSummary;
  seasonTrend: SeasonTrendItem[];
  marketLeaders: MarketLeader[];
  scoutShortlist: ScoutShortlistItem[];
  coachFocus: CoachFocusItem[];
  managementBoard: ManagementBoardItem[];
  riskWatchlist: MedicalRiskItem[];
  positionDepth: PositionDepthItem[];
  recentMatches: RecentMatchItem[];
  visualizations: DashboardVisualizations;
  datasets: DashboardDatasets;
};

export type PlayersDirectoryPayload = {
  latestSeasonYear: number;
  medicalAvailability: MedicalRiskItem[];
  playerSeasonSummary: PlayerSeasonSummaryItem[];
};

export type PhysicalOverviewPayload = {
  latestSeasonYear: number;
  matchGpsSummary: TeamMatchTrendItem[];
  physicalSessions: PhysicalTestSessionView[];
};

export type PlayerDetailProfile = {
  player_id: string;
  name: string;
  birth_date: string;
  grade: number | null;
  registered_position: string | null;
  primary_role: string | null;
  position_group: string | null;
  age_today: number | null;
  dominant_foot: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  team_name: string | null;
  status: string | null;
  latest_season_id: string | null;
  latest_season_year: number | null;
  latest_match_availability: string | null;
  latest_injury_name: string | null;
  latest_injury_grade: string | null;
  latest_return_to_play_date: string | null;
  growth_score: number | null;
  growth_band: string | null;
};

export type PlayerMatchPerformanceItem = {
  analysis_id: string;
  player_id?: string;
  match_id: string;
  match_type?: string | null;
  season_id: string;
  season_year: number;
  match_no: number;
  match_date: string;
  team_name: string;
  opponent: string;
  venue: string;
  result: string;
  score: string;
  match_label: string;
  name: string;
  position: string;
  position_played: string;
  appearance_type: string;
  started: string;
  minutes_played: number;
  first_half_minutes: number;
  second_half_minutes: number;
  sub_in_minute: number | null;
  sub_out_minute: number | null;
  goals: number;
  assists: number;
  goal_contrib: number;
  shots: number;
  shots_on_target: number;
  key_passes: number;
  pass_attempts: number;
  pass_success: number;
  pass_success_pct: number | null;
  dribble_attempts: number;
  dribble_success: number;
  dribble_success_pct: number | null;
  tackles_won: number;
  interceptions: number;
  clearings: number;
  saves: number;
  duels_won: number;
  duels_lost: number;
  yellow_cards: number;
  red_cards: number;
  play_time_min?: number | null;
  total_distance?: number | null;
  avg_speed?: number | null;
  max_speed?: number | null;
  sprint_distance?: number | null;
  accel_count?: number | null;
  decel_count?: number | null;
  hi_accel_count?: number | null;
  hi_decel_count?: number | null;
  cod_count?: number | null;
  distance_0_15_min?: number | null;
  distance_15_30_min?: number | null;
  distance_30_45_min?: number | null;
  distance_45_60_min?: number | null;
  distance_60_75_min?: number | null;
  distance_75_90_min?: number | null;
  distance_speed_0_5?: number | null;
  distance_speed_5_10?: number | null;
  distance_speed_10_15?: number | null;
  distance_speed_15_20?: number | null;
  distance_speed_20_25?: number | null;
  distance_speed_25_plus?: number | null;
  distance_total_km: number | null;
  distance_high_speed_m: number | null;
  max_speed_kmh: number | null;
  sprint_count: number | null;
  acceleration_count: number | null;
  deceleration_count: number | null;
  player_load: number | null;
  impact_score: number;
};

export type PlayerPhysicalTestItem = {
  physical_id: string;
  season_id: string;
  season_year: number;
  player_id: string;
  test_round: number;
  test_date: string;
  height_cm: number | null;
  weight_kg: number | null;
  skeletal_muscle_kg: number | null;
  body_fat_pct: number | null;
  sprint_10m_sec: number | null;
  sprint_30m_sec: number | null;
  sprint_50m_sec: number | null;
  sprint_100m_sec: number | null;
  vertical_jump_cm: number | null;
  agility_t_sec: number | null;
  shuttle_run_count: number | null;
  shuttle_run_sec: number | null;
  endurance_m: number | null;
  flexibility_cm: number | null;
};

export type PlayerInjuryRecordItem = {
  at_id: string;
  season_id: string;
  season_year: number;
  player_id: string;
  record_date: string;
  status_type: string;
  body_part: string | null;
  injury_name: string | null;
  injury_type: string | null;
  injury_grade: string | null;
  injury_start_date: string | null;
  injury_end_date: string | null;
  days_missed: number;
  return_to_play_date: string | null;
  training_participation: string | null;
  match_availability: string;
  rehab_stage: string | null;
};

export type PlayerMentalNoteItem = {
  mental_id: string;
  season_id: string;
  season_year: number;
  player_id: string;
  session_round: number;
  session_date: string;
  counseling_type: string;
  player_quote: string;
};

export type PlayerDetailReports = {
  agent: MarketLeader | null;
  scout: ScoutShortlistItem | null;
  coach: CoachFocusItem | null;
  management: ManagementBoardItem | null;
  medical: MedicalRiskItem | null;
  growth: PlayerGrowthTrendItem | null;
  physical: PhysicalProgressItem | null;
};

export type PlayerDetailPayload = {
  generatedOn: string;
  profile: PlayerDetailProfile;
  latestSeasonSummary: PlayerSeasonSummaryItem | null;
  seasonSummaries: PlayerSeasonSummaryItem[];
  matchPerformance: PlayerMatchPerformanceItem[];
  physicalTests: PlayerPhysicalTestItem[];
  injuryHistory: PlayerInjuryRecordItem[];
  mentalNotes: PlayerMentalNoteItem[];
  reports: PlayerDetailReports;
};
