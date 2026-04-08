from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PhysicalProfileSummary(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_percentage: float | None = None
    bmi: float | None = None
    muscle_mass_kg: float | None = None
    measured_at: datetime | None = None


class CurrentInjurySummary(BaseModel):
    injury_id: str | None = None
    injury_date: date | None = None
    injury_type: str | None = None
    injury_part: str | None = None
    severity_level: str | None = None
    injury_status: str | None = None
    expected_return_date: date | None = None
    actual_return_date: date | None = None
    occurred_during: str | None = None


class MatchSummary(BaseModel):
    appearances: int = 0
    total_minutes: int = 0
    total_goals: int = 0
    total_assists: int = 0
    recent_form_score: float | None = None
    previous_form_score: float | None = None
    form_delta: float | None = None
    form_trend: str | None = None
    evaluated_match_count: int = 0
    latest_match_score: float | None = None
    position_average_form_score: float | None = None
    team_average_form_score: float | None = None
    form_vs_position_average: float | None = None
    form_vs_team_average: float | None = None
    latest_match_date: date | None = None


class PlayerSummary(BaseModel):
    player_id: str
    name: str
    jersey_number: int
    date_of_birth: date
    age: int
    primary_position: str
    secondary_position: str | None = None
    foot: str
    nationality: str
    status: str
    profile_image_url: str | None = None
    joined_at: datetime
    previous_team: str | None = None
    updated_at: datetime
    physical_profile: PhysicalProfileSummary
    current_injury: CurrentInjurySummary | None = None
    match_summary: MatchSummary


class PlayerListResponse(BaseModel):
    total: int
    items: list[PlayerSummary]


class RecentMatchItem(BaseModel):
    match_player_id: str
    match_id: str
    match_date: date
    match_type: str
    opponent_team: str
    stadium: str
    minutes_played: int
    goals: int
    assists: int
    shots: int
    pass_accuracy: float | None = None
    total_distance: float | None = None
    max_speed: float | None = None
    sprint_count: int | None = None
    match_score: float | None = None
    match_score_band: str | None = None


class MatchHighlightItem(RecentMatchItem):
    pass


class PlayerDetailResponse(PlayerSummary):
    latest_season_year: int | None = None
    season_best_match: MatchHighlightItem | None = None
    season_worst_match: MatchHighlightItem | None = None
    recent_matches: list[RecentMatchItem]


class RecentInjuryHistoryItem(BaseModel):
    injury_id: str
    player_id: str
    name: str
    primary_position: str
    status: str
    injury_date: date
    injury_type: str | None = None
    injury_part: str | None = None
    severity_level: str | None = None
    injury_status: str | None = None
    expected_return_date: date | None = None
    actual_return_date: date | None = None
    notes: str | None = None


class InjuryRiskFactors(BaseModel):
    load_score: float
    physical_change_score: float
    injury_history_score: float
    return_to_play_score: float
    symptom_score: float
    acute_load_7d: float
    acute_load_percentile: float | None = None
    chronic_load_baseline: float | None = None
    acute_chronic_ratio: float | None = None
    acute_distance_7d: float | None = None
    chronic_distance_baseline: float | None = None
    distance_ratio: float | None = None
    high_intensity_sessions_7d: int
    match_minutes_7d: int
    sprint_count_7d: int
    sprint_count_baseline: float | None = None
    sprint_ratio: float | None = None
    body_fat_delta: float | None = None
    muscle_mass_delta: float | None = None
    weight_delta: float | None = None
    injuries_last_180d: int
    injuries_last_365d: int
    reinjury_flag: bool
    days_since_return: int | None = None
    open_rehab_flag: bool
    recent_symptom_count_120d: int
    recent_symptom_flag: bool
    latest_symptom_days_ago: int | None = None
    recent_medical_consultation_count_14d: int


class PlayerInjuryRiskItem(BaseModel):
    snapshot_date: date
    player_id: str
    name: str
    primary_position: str
    status: str
    overall_risk_score: float
    risk_band: str
    reasons: list[str]
    factors: InjuryRiskFactors


class PlayerInjuryRiskResponse(BaseModel):
    snapshot_date: date
    total: int
    items: list[PlayerInjuryRiskItem]
    recent_history: list[RecentInjuryHistoryItem] = Field(default_factory=list)


class PerformanceReadinessFactors(BaseModel):
    match_form_score: float
    evaluation_score: float
    mental_readiness_score: float
    availability_penalty: float
    recent_form_index: float | None = None
    previous_form_index: float | None = None
    form_delta: float | None = None
    recent_match_count: int
    recent_match_minutes_avg: float | None = None
    latest_match_date: date | None = None
    latest_evaluation_average: float | None = None
    previous_evaluation_average: float | None = None
    evaluation_delta: float | None = None
    latest_evaluation_date: date | None = None
    recent_counseling_count_90d: int
    caution_note_count_90d: int


class PlayerPerformanceReadinessItem(BaseModel):
    snapshot_date: date
    player_id: str
    name: str
    primary_position: str
    status: str
    readiness_score: float
    readiness_band: str
    reasons: list[str]
    factors: PerformanceReadinessFactors


class PlayerPerformanceReadinessResponse(BaseModel):
    snapshot_date: date
    total: int
    items: list[PlayerPerformanceReadinessItem]


class DevelopmentReportFactors(BaseModel):
    physical_growth_score: float
    performance_growth_score: float
    gps_growth_score: float
    evaluation_growth_score: float
    comparison_window_days: int | None = None
    muscle_mass_delta: float | None = None
    body_fat_delta: float | None = None
    weight_delta: float | None = None
    recent_form_index: float | None = None
    previous_form_index: float | None = None
    form_delta: float | None = None
    recent_distance_avg: float | None = None
    previous_distance_avg: float | None = None
    recent_sprint_avg: float | None = None
    previous_sprint_avg: float | None = None
    recent_max_speed_avg: float | None = None
    previous_max_speed_avg: float | None = None
    latest_evaluation_average: float | None = None
    previous_evaluation_average: float | None = None
    evaluation_delta: float | None = None
    latest_profile_date: date | None = None


class PlayerDevelopmentReportItem(BaseModel):
    snapshot_date: date
    player_id: str
    name: str
    primary_position: str
    status: str
    growth_score: float
    growth_band: str
    reasons: list[str]
    factors: DevelopmentReportFactors


class PlayerDevelopmentReportResponse(BaseModel):
    snapshot_date: date
    total: int
    items: list[PlayerDevelopmentReportItem]


class PositionAvailabilityItem(BaseModel):
    position: str
    roster_count: int
    available_count: int
    managed_count: int
    injured_count: int


class TeamAvailabilityBoard(BaseModel):
    available_count: int
    managed_count: int
    injured_count: int
    scheduled_return_count: int
    positions: list[PositionAvailabilityItem]


class TeamLoadTrendPoint(BaseModel):
    session_date: date
    session_source: str
    total_load: float
    sprint_count: int
    total_distance: float


class TeamLoadTrend(BaseModel):
    load_7d: float
    load_14d: float
    load_28d: float
    match_load_share_28d: float
    training_load_share_28d: float
    average_sprint_exposure_7d: float
    average_total_distance_7d: float
    load_spike_player_count: int
    load_drop_player_count: int
    trend_points: list[TeamLoadTrendPoint]


class TeamMatchFormItem(BaseModel):
    match_id: str
    match_date: date
    match_type: str
    opponent_team: str
    goals_for: int
    goals_against: int
    team_average_match_score: float
    average_minutes: float
    efficiency_score: float | None = None


class TeamMatchFormBoard(BaseModel):
    recent_5_match_score: float
    previous_5_match_score: float | None = None
    form_delta: float | None = None
    latest_match_score: float | None = None
    best_match: TeamMatchFormItem | None = None
    worst_match: TeamMatchFormItem | None = None
    recent_matches: list[TeamMatchFormItem]


class PositionBalanceItem(BaseModel):
    position: str
    recent_form_score: float | None = None
    previous_form_score: float | None = None
    form_delta: float | None = None
    average_minutes: float | None = None
    average_sprint_count: float | None = None
    average_total_distance: float | None = None
    available_count: int
    managed_count: int
    injured_count: int
    insight_label: str


class InjuryPartDistributionItem(BaseModel):
    injury_part: str
    count: int


class TeamMedicalOverview(BaseModel):
    injuries_last_180d: int
    reinjury_count_365d: int
    returns_last_14d_count: int
    current_rehab_count: int
    injury_parts: list[InjuryPartDistributionItem]


class PositionDevelopmentItem(BaseModel):
    position: str
    roster_count: int
    average_body_fat_delta: float | None = None
    average_muscle_mass_delta: float | None = None
    average_form_delta: float | None = None
    growth_label: str


class TeamDevelopmentTrend(BaseModel):
    average_body_fat_delta: float | None = None
    average_muscle_mass_delta: float | None = None
    season_start_body_fat_delta: float | None = None
    season_start_muscle_mass_delta: float | None = None
    rising_players_count: int
    falling_players_count: int
    positions: list[PositionDevelopmentItem]


class TeamOverviewResponse(BaseModel):
    snapshot_date: date
    availability: TeamAvailabilityBoard
    load: TeamLoadTrend
    match_form: TeamMatchFormBoard
    position_balance: list[PositionBalanceItem]
    medical: TeamMedicalOverview
    development: TeamDevelopmentTrend


class TeamCalendarMonthOption(BaseModel):
    year: int
    month: int
    label: str


class TeamCalendarSummary(BaseModel):
    total_event_count: int
    match_count: int
    official_match_count: int
    practice_match_count: int
    training_count: int
    high_intensity_training_count: int


class TeamCalendarEvent(BaseModel):
    event_id: str
    event_type: str
    event_date: date
    start_at: datetime | None = None
    end_at: datetime | None = None
    title: str
    category: str
    detail: str | None = None
    location: str | None = None
    opponent_team: str | None = None
    intensity_level: str | None = None
    coach_name: str | None = None
    score_for: int | None = None
    score_against: int | None = None


class TeamCalendarResponse(BaseModel):
    reference_date: date
    selected_year: int
    selected_month: int
    selected_label: str
    available_months: list[TeamCalendarMonthOption]
    summary: TeamCalendarSummary
    events: list[TeamCalendarEvent]


class TeamTrainingDetailMeta(BaseModel):
    training_id: str
    training_date: date
    session_name: str
    training_type: str
    training_focus: str | None = None
    training_detail: str | None = None
    notes: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    intensity_level: str | None = None
    coach_name: str | None = None
    location: str | None = None


class TeamTrainingDetailSummary(BaseModel):
    participant_count: int
    session_duration_min: int | None = None
    average_play_time_min: float | None = None
    total_distance: float | None = None
    average_distance: float | None = None
    total_sprint_count: int
    average_avg_speed: float | None = None
    average_max_speed: float | None = None
    total_accel_count: int
    total_decel_count: int
    total_hi_accel_count: int
    total_hi_decel_count: int
    total_cod_count: int


class TeamTrainingDetailLeader(BaseModel):
    metric_key: str
    label: str
    player_id: str
    name: str
    jersey_number: int
    position: str
    value: float
    unit: str | None = None


class TeamTrainingDetailPlayerStat(BaseModel):
    training_gps_id: str
    player_id: str
    name: str
    jersey_number: int
    position: str
    play_time_min: float | None = None
    total_distance: float | None = None
    avg_speed: float | None = None
    distance_0_15_min: float | None = None
    distance_15_30_min: float | None = None
    distance_30_45_min: float | None = None
    distance_45_60_min: float | None = None
    distance_60_75_min: float | None = None
    distance_75_90_min: float | None = None
    max_speed: float | None = None
    sprint_count: int | None = None
    sprint_distance: float | None = None
    distance_speed_0_5: float | None = None
    distance_speed_5_10: float | None = None
    distance_speed_10_15: float | None = None
    distance_speed_15_20: float | None = None
    distance_speed_20_25: float | None = None
    distance_speed_25_plus: float | None = None
    accel_count: int | None = None
    decel_count: int | None = None
    hi_accel_count: int | None = None
    hi_decel_count: int | None = None
    cod_count: int | None = None


class TeamTrainingDetailResponse(BaseModel):
    reference_date: date
    training: TeamTrainingDetailMeta
    summary: TeamTrainingDetailSummary
    leaders: list[TeamTrainingDetailLeader]
    players: list[TeamTrainingDetailPlayerStat]


class TeamTrainingYearOption(BaseModel):
    year: int
    label: str


class TeamTrainingsSummary(BaseModel):
    training_count: int
    high_intensity_count: int
    medium_intensity_count: int
    low_intensity_count: int
    average_duration_min: float | None = None
    average_participant_count: float | None = None
    average_total_distance: float | None = None


class TeamTrainingListItem(BaseModel):
    training_id: str
    training_date: date
    session_name: str
    training_type: str
    training_focus: str | None = None
    intensity_level: str | None = None
    coach_name: str | None = None
    location: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    session_duration_min: int | None = None
    participant_count: int | None = None
    total_distance: float | None = None


class TeamTrainingListResponse(BaseModel):
    reference_date: date
    selected_year: int
    available_years: list[TeamTrainingYearOption]
    summary: TeamTrainingsSummary
    trainings: list[TeamTrainingListItem]


class TeamMatchYearOption(BaseModel):
    year: int
    label: str


class TeamMatchesSummary(BaseModel):
    match_count: int
    official_match_count: int
    practice_match_count: int
    win_count: int
    draw_count: int
    loss_count: int
    average_match_score: float | None = None


class TeamMatchListItem(BaseModel):
    match_id: str
    match_date: date
    match_type: str
    opponent_team: str
    stadium_name: str
    goals_for: int
    goals_against: int
    result: str
    possession_for: float | None = None
    possession_against: float | None = None
    team_average_match_score: float
    average_minutes: float
    player_count: int


class TeamMatchListResponse(BaseModel):
    reference_date: date
    selected_year: int
    available_years: list[TeamMatchYearOption]
    summary: TeamMatchesSummary
    matches: list[TeamMatchListItem]


class TeamMatchDetailMeta(BaseModel):
    match_id: str
    match_date: date
    match_type: str
    opponent_team: str
    stadium_name: str
    goals_for: int
    goals_against: int
    result: str
    possession_for: float | None = None
    possession_against: float | None = None


class TeamMatchDetailSummary(BaseModel):
    team_average_match_score: float | None = None
    efficiency_score: float | None = None
    player_count: int
    starter_count: int
    substitute_used_count: int
    average_minutes: float | None = None
    total_distance: float | None = None
    average_distance: float | None = None
    total_sprint_count: int
    average_max_speed: float | None = None


class TeamMatchDetailTeamStats(BaseModel):
    assists: int
    shots: int
    shots_on_target: int
    key_passes: int
    pass_accuracy: float | None = None
    crosses_attempted: int
    crosses_succeeded: int
    cross_accuracy: float | None = None
    duels_won: int
    duels_total: int
    duel_win_rate: float | None = None
    interceptions: int
    recoveries: int
    mistakes: int


class TeamMatchDetailLeader(BaseModel):
    metric_key: str
    label: str
    player_id: str
    name: str
    jersey_number: int
    position: str
    value: float
    unit: str | None = None


class TeamMatchDetailPlayerStat(BaseModel):
    match_player_id: str
    player_id: str
    name: str
    jersey_number: int
    position: str
    start_position: str | None = None
    substitute_in: int | None = None
    substitute_out: int | None = None
    minutes_played: int
    goals: int
    assists: int
    shots: int
    shots_on_target: int
    key_passes: int
    pass_accuracy: float | None = None
    duel_win_rate: float | None = None
    recoveries: int
    interceptions: int
    mistakes: int
    yellow_cards: int
    red_cards: int
    total_distance: float | None = None
    play_time_min: int | None = None
    avg_speed: float | None = None
    distance_0_15_min: float | None = None
    distance_15_30_min: float | None = None
    distance_30_45_min: float | None = None
    distance_45_60_min: float | None = None
    distance_60_75_min: float | None = None
    distance_75_90_min: float | None = None
    sprint_count: int | None = None
    sprint_distance: float | None = None
    distance_speed_0_5: float | None = None
    distance_speed_5_10: float | None = None
    distance_speed_10_15: float | None = None
    distance_speed_15_20: float | None = None
    distance_speed_20_25: float | None = None
    distance_speed_25_plus: float | None = None
    cod_count: int | None = None
    max_speed: float | None = None
    accel_count: int | None = None
    decel_count: int | None = None
    hi_accel_count: int | None = None
    hi_decel_count: int | None = None
    match_score: float | None = None
    match_score_band: str | None = None


class TeamMatchDetailResponse(BaseModel):
    reference_date: date
    match: TeamMatchDetailMeta
    summary: TeamMatchDetailSummary
    team_stats: TeamMatchDetailTeamStats
    leaders: list[TeamMatchDetailLeader]
    players: list[TeamMatchDetailPlayerStat]


class AssistantStatusResponse(BaseModel):
    provider: str
    base_url: str
    model: str
    reachable: bool
    model_available: bool
    available_models: list[str]
    detail: str


class AssistantQueryRequest(BaseModel):
    question: str


class AssistantQueryStep(BaseModel):
    step: int
    action: str
    reason: str | None = None
    sql: str | None = None
    row_count: int | None = None
    error: str | None = None
    preview: list[dict[str, object | None]] = Field(default_factory=list)


class AssistantQueryResponse(BaseModel):
    question: str
    provider: str
    model: str
    answer: str
    steps: list[AssistantQueryStep]
