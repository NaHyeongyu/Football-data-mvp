export type PositionAvailabilityItem = {
  position: string;
  roster_count: number;
  available_count: number;
  managed_count: number;
  injured_count: number;
};

export type TeamAvailabilityBoard = {
  available_count: number;
  managed_count: number;
  injured_count: number;
  scheduled_return_count: number;
  positions: PositionAvailabilityItem[];
};

export type TeamLoadTrendPoint = {
  session_date: string;
  session_source: string;
  total_load: number;
  sprint_count: number;
  total_distance: number;
};

export type TeamLoadTrend = {
  load_7d: number;
  load_14d: number;
  load_28d: number;
  match_load_share_28d: number;
  training_load_share_28d: number;
  average_sprint_exposure_7d: number;
  average_total_distance_7d: number;
  load_spike_player_count: number;
  load_drop_player_count: number;
  trend_points: TeamLoadTrendPoint[];
};

export type TeamMatchFormItem = {
  match_id: string;
  match_date: string;
  match_type: string;
  opponent_team: string;
  goals_for: number;
  goals_against: number;
  team_average_match_score: number;
  average_minutes: number;
  efficiency_score: number | null;
};

export type TeamMatchFormBoard = {
  recent_5_match_score: number;
  previous_5_match_score: number | null;
  form_delta: number | null;
  latest_match_score: number | null;
  best_match: TeamMatchFormItem | null;
  worst_match: TeamMatchFormItem | null;
  recent_matches: TeamMatchFormItem[];
};

export type PositionBalanceItem = {
  position: string;
  recent_form_score: number | null;
  previous_form_score: number | null;
  form_delta: number | null;
  average_minutes: number | null;
  average_sprint_count: number | null;
  average_total_distance: number | null;
  available_count: number;
  managed_count: number;
  injured_count: number;
  insight_label: string;
};

export type InjuryPartDistributionItem = {
  injury_part: string;
  count: number;
};

export type TeamMedicalOverview = {
  injuries_last_180d: number;
  reinjury_count_365d: number;
  returns_last_14d_count: number;
  current_rehab_count: number;
  injury_parts: InjuryPartDistributionItem[];
};

export type PositionDevelopmentItem = {
  position: string;
  roster_count: number;
  average_body_fat_delta: number | null;
  average_muscle_mass_delta: number | null;
  average_form_delta: number | null;
  growth_label: string;
};

export type TeamDevelopmentTrend = {
  average_body_fat_delta: number | null;
  average_muscle_mass_delta: number | null;
  season_start_body_fat_delta: number | null;
  season_start_muscle_mass_delta: number | null;
  rising_players_count: number;
  falling_players_count: number;
  positions: PositionDevelopmentItem[];
};

export type TeamOverviewResponse = {
  snapshot_date: string;
  availability: TeamAvailabilityBoard;
  load: TeamLoadTrend;
  match_form: TeamMatchFormBoard;
  position_balance: PositionBalanceItem[];
  medical: TeamMedicalOverview;
  development: TeamDevelopmentTrend;
};

export type TeamCalendarMonthOption = {
  year: number;
  month: number;
  label: string;
};

export type TeamCalendarSummary = {
  total_event_count: number;
  match_count: number;
  official_match_count: number;
  practice_match_count: number;
  training_count: number;
  high_intensity_training_count: number;
};

export type TeamCalendarEvent = {
  event_id: string;
  event_type: string;
  event_date: string;
  start_at: string | null;
  end_at: string | null;
  title: string;
  category: string;
  detail: string | null;
  location: string | null;
  opponent_team: string | null;
  intensity_level: string | null;
  coach_name: string | null;
  score_for: number | null;
  score_against: number | null;
};

export type TeamCalendarResponse = {
  reference_date: string;
  selected_year: number;
  selected_month: number;
  selected_label: string;
  available_months: TeamCalendarMonthOption[];
  summary: TeamCalendarSummary;
  events: TeamCalendarEvent[];
};

export type TeamTrainingDetailMeta = {
  training_id: string;
  training_date: string;
  session_name: string;
  training_type: string;
  training_focus: string | null;
  training_detail: string | null;
  notes: string | null;
  start_at: string | null;
  end_at: string | null;
  intensity_level: string | null;
  coach_name: string | null;
  location: string | null;
};

export type TeamTrainingDetailSummary = {
  participant_count: number;
  session_duration_min: number | null;
  average_play_time_min: number | null;
  total_distance: number | null;
  average_distance: number | null;
  total_sprint_count: number;
  average_avg_speed: number | null;
  average_max_speed: number | null;
  total_accel_count: number;
  total_decel_count: number;
  total_hi_accel_count: number;
  total_hi_decel_count: number;
  total_cod_count: number;
};

export type TeamTrainingDetailLeader = {
  metric_key: string;
  label: string;
  player_id: string;
  name: string;
  jersey_number: number;
  position: string;
  value: number;
  unit: string | null;
};

export type TeamTrainingDetailPlayerStat = {
  training_gps_id: string;
  player_id: string;
  name: string;
  jersey_number: number;
  position: string;
  play_time_min: number | null;
  total_distance: number | null;
  avg_speed: number | null;
  distance_0_15_min: number | null;
  distance_15_30_min: number | null;
  distance_30_45_min: number | null;
  distance_45_60_min: number | null;
  distance_60_75_min: number | null;
  distance_75_90_min: number | null;
  max_speed: number | null;
  sprint_count: number | null;
  sprint_distance: number | null;
  distance_speed_0_5: number | null;
  distance_speed_5_10: number | null;
  distance_speed_10_15: number | null;
  distance_speed_15_20: number | null;
  distance_speed_20_25: number | null;
  distance_speed_25_plus: number | null;
  accel_count: number | null;
  decel_count: number | null;
  hi_accel_count: number | null;
  hi_decel_count: number | null;
  cod_count: number | null;
};

export type TeamTrainingDetailResponse = {
  reference_date: string;
  training: TeamTrainingDetailMeta;
  summary: TeamTrainingDetailSummary;
  leaders: TeamTrainingDetailLeader[];
  players: TeamTrainingDetailPlayerStat[];
};

export type TeamTrainingYearOption = {
  year: number;
  label: string;
};

export type TeamTrainingsSummary = {
  training_count: number;
  high_intensity_count: number;
  medium_intensity_count: number;
  low_intensity_count: number;
  average_duration_min: number | null;
  average_participant_count: number | null;
  average_total_distance: number | null;
};

export type TeamTrainingListItem = {
  training_id: string;
  training_date: string;
  session_name: string;
  training_type: string;
  training_focus: string | null;
  intensity_level: string | null;
  coach_name: string | null;
  location: string | null;
  start_at: string | null;
  end_at: string | null;
  session_duration_min: number | null;
  participant_count: number | null;
  total_distance: number | null;
};

export type TeamTrainingListResponse = {
  reference_date: string;
  selected_year: number;
  available_years: TeamTrainingYearOption[];
  summary: TeamTrainingsSummary;
  trainings: TeamTrainingListItem[];
};

export type TeamMatchYearOption = {
  year: number;
  label: string;
};

export type TeamMatchesSummary = {
  match_count: number;
  official_match_count: number;
  practice_match_count: number;
  win_count: number;
  draw_count: number;
  loss_count: number;
  average_match_score: number | null;
};

export type TeamMatchListItem = {
  match_id: string;
  match_date: string;
  match_type: string;
  opponent_team: string;
  stadium_name: string;
  goals_for: number;
  goals_against: number;
  result: string;
  possession_for: number | null;
  possession_against: number | null;
  team_average_match_score: number;
  average_minutes: number;
  player_count: number;
};

export type TeamMatchListResponse = {
  reference_date: string;
  selected_year: number;
  available_years: TeamMatchYearOption[];
  summary: TeamMatchesSummary;
  matches: TeamMatchListItem[];
};

export type TeamMatchDetailMeta = {
  match_id: string;
  match_date: string;
  match_type: string;
  opponent_team: string;
  stadium_name: string;
  goals_for: number;
  goals_against: number;
  result: string;
  possession_for: number | null;
  possession_against: number | null;
};

export type TeamMatchDetailSummary = {
  team_average_match_score: number | null;
  efficiency_score: number | null;
  player_count: number;
  starter_count: number;
  substitute_used_count: number;
  average_minutes: number | null;
  total_distance: number | null;
  average_distance: number | null;
  total_sprint_count: number;
  average_max_speed: number | null;
};

export type TeamMatchDetailTeamStats = {
  assists: number;
  shots: number;
  shots_on_target: number;
  key_passes: number;
  pass_accuracy: number | null;
  crosses_attempted: number;
  crosses_succeeded: number;
  cross_accuracy: number | null;
  duels_won: number;
  duels_total: number;
  duel_win_rate: number | null;
  interceptions: number;
  recoveries: number;
  mistakes: number;
};

export type TeamMatchDetailLeader = {
  metric_key: string;
  label: string;
  player_id: string;
  name: string;
  jersey_number: number;
  position: string;
  value: number;
  unit: string | null;
};

export type TeamMatchDetailPlayerStat = {
  match_player_id: string;
  player_id: string;
  name: string;
  jersey_number: number;
  position: string;
  start_position: string | null;
  substitute_in: number | null;
  substitute_out: number | null;
  minutes_played: number;
  goals: number;
  assists: number;
  shots: number;
  shots_on_target: number;
  key_passes: number;
  pass_accuracy: number | null;
  duel_win_rate: number | null;
  recoveries: number;
  interceptions: number;
  mistakes: number;
  yellow_cards: number;
  red_cards: number;
  total_distance: number | null;
  play_time_min: number | null;
  avg_speed: number | null;
  distance_0_15_min: number | null;
  distance_15_30_min: number | null;
  distance_30_45_min: number | null;
  distance_45_60_min: number | null;
  distance_60_75_min: number | null;
  distance_75_90_min: number | null;
  sprint_count: number | null;
  sprint_distance: number | null;
  distance_speed_0_5: number | null;
  distance_speed_5_10: number | null;
  distance_speed_10_15: number | null;
  distance_speed_15_20: number | null;
  distance_speed_20_25: number | null;
  distance_speed_25_plus: number | null;
  cod_count: number | null;
  max_speed: number | null;
  accel_count: number | null;
  decel_count: number | null;
  hi_accel_count: number | null;
  hi_decel_count: number | null;
  match_score: number | null;
  match_score_band: string | null;
};

export type TeamMatchDetailResponse = {
  reference_date: string;
  match: TeamMatchDetailMeta;
  summary: TeamMatchDetailSummary;
  team_stats: TeamMatchDetailTeamStats;
  leaders: TeamMatchDetailLeader[];
  players: TeamMatchDetailPlayerStat[];
};

export type AssistantStatusResponse = {
  provider: string;
  base_url: string;
  model: string;
  reachable: boolean;
  model_available: boolean;
  available_models: string[];
  detail: string;
};

export type AssistantQueryRequest = {
  question: string;
};

export type AssistantQueryStep = {
  step: number;
  action: string;
  reason: string | null;
  sql: string | null;
  row_count: number | null;
  error: string | null;
  preview: Array<Record<string, unknown>>;
};

export type AssistantQueryResponse = {
  question: string;
  provider: string;
  model: string;
  answer: string;
  steps: AssistantQueryStep[];
};

export type PlayerRecentInjuryHistoryItem = {
  injury_id: string;
  player_id: string;
  name: string;
  primary_position: string;
  status: string;
  injury_date: string;
  injury_type: string | null;
  injury_part: string | null;
  severity_level: string | null;
  injury_status: string | null;
  expected_return_date: string | null;
  actual_return_date: string | null;
  notes: string | null;
};

export type PlayerInjuryRiskFactors = {
  load_score: number;
  physical_change_score: number;
  injury_history_score: number;
  return_to_play_score: number;
  symptom_score: number;
  acute_load_7d: number;
  acute_load_percentile: number | null;
  chronic_load_baseline: number | null;
  acute_chronic_ratio: number | null;
  acute_distance_7d: number | null;
  chronic_distance_baseline: number | null;
  distance_ratio: number | null;
  high_intensity_sessions_7d: number;
  match_minutes_7d: number;
  sprint_count_7d: number;
  sprint_count_baseline: number | null;
  sprint_ratio: number | null;
  body_fat_delta: number | null;
  muscle_mass_delta: number | null;
  weight_delta: number | null;
  injuries_last_180d: number;
  injuries_last_365d: number;
  reinjury_flag: boolean;
  days_since_return: number | null;
  open_rehab_flag: boolean;
  recent_symptom_count_120d: number;
  recent_symptom_flag: boolean;
  latest_symptom_days_ago: number | null;
  recent_medical_consultation_count_14d: number;
};

export type PlayerInjuryRiskItem = {
  snapshot_date: string;
  player_id: string;
  name: string;
  primary_position: string;
  status: string;
  overall_risk_score: number;
  risk_band: string;
  reasons: string[];
  factors: PlayerInjuryRiskFactors;
};

export type PlayerInjuryRiskResponse = {
  snapshot_date: string;
  total: number;
  items: PlayerInjuryRiskItem[];
  recent_history: PlayerRecentInjuryHistoryItem[];
};

export type PerformanceReadinessFactors = {
  match_form_score: number;
  evaluation_score: number;
  mental_readiness_score: number;
  availability_penalty: number;
  recent_form_index: number | null;
  previous_form_index: number | null;
  form_delta: number | null;
  recent_match_count: number;
  recent_match_minutes_avg: number | null;
  latest_match_date: string | null;
  latest_evaluation_average: number | null;
  previous_evaluation_average: number | null;
  evaluation_delta: number | null;
  latest_evaluation_date: string | null;
  recent_counseling_count_90d: number;
  caution_note_count_90d: number;
};

export type PlayerPerformanceReadinessItem = {
  snapshot_date: string;
  player_id: string;
  name: string;
  primary_position: string;
  status: string;
  readiness_score: number;
  readiness_band: string;
  reasons: string[];
  factors: PerformanceReadinessFactors;
};

export type PlayerPerformanceReadinessResponse = {
  snapshot_date: string;
  total: number;
  items: PlayerPerformanceReadinessItem[];
};

export type DevelopmentReportFactors = {
  physical_growth_score: number;
  performance_growth_score: number;
  gps_growth_score: number;
  evaluation_growth_score: number;
  comparison_window_days: number | null;
  muscle_mass_delta: number | null;
  body_fat_delta: number | null;
  weight_delta: number | null;
  recent_form_index: number | null;
  previous_form_index: number | null;
  form_delta: number | null;
  recent_distance_avg: number | null;
  previous_distance_avg: number | null;
  recent_sprint_avg: number | null;
  previous_sprint_avg: number | null;
  recent_max_speed_avg: number | null;
  previous_max_speed_avg: number | null;
  latest_evaluation_average: number | null;
  previous_evaluation_average: number | null;
  evaluation_delta: number | null;
  latest_profile_date: string | null;
};

export type PlayerDevelopmentReportItem = {
  snapshot_date: string;
  player_id: string;
  name: string;
  primary_position: string;
  status: string;
  growth_score: number;
  growth_band: string;
  reasons: string[];
  factors: DevelopmentReportFactors;
};

export type PlayerDevelopmentReportResponse = {
  snapshot_date: string;
  total: number;
  items: PlayerDevelopmentReportItem[];
};
