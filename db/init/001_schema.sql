CREATE SCHEMA IF NOT EXISTS football;

DO $$
BEGIN
    CREATE TYPE football.position_enum AS ENUM ('GK', 'CB', 'LB', 'RB', 'DM', 'CM', 'AM', 'LW', 'RW', 'CF', 'ST', 'LM', 'RM');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.dominant_foot_enum AS ENUM ('right', 'left', 'both');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.player_status_enum AS ENUM ('active', 'injured');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.injury_severity_enum AS ENUM ('minor', 'moderate', 'severe');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.injury_status_enum AS ENUM ('rehab', 'recovered');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.injury_context_enum AS ENUM ('match', 'training', 'outside');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.match_type_enum AS ENUM ('공식', '연습');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.goal_type_enum AS ENUM ('header', 'inside_box', 'penalty');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.training_type_enum AS ENUM (
        'conditioning',
        'pre_match',
        'recovery',
        'tactical',
        'tactical_physical',
        'technical'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.training_focus_enum AS ENUM (
        '고강도 전술 + 체력',
        '기술 완성도',
        '전술 정리 및 세트피스',
        '조직 전술',
        '체력·파워 향상',
        '회복 및 재생'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.session_name_enum AS ENUM (
        '경기 전날 프리매치 세션',
        '경기 후 회복훈련',
        '기술 완성 훈련',
        '동계 고강도 피지컬 세션',
        '전술 조직훈련',
        '주중 고강도 전술훈련'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.intensity_level_enum AS ENUM ('low', 'medium', 'high');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE football.counseling_topic_enum AS ENUM (
        '경기 피드백',
        '멘탈 관리',
        '부상 관리',
        '진로 상담',
        '훈련 태도'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE TABLE IF NOT EXISTS football.stadiums (
    stadium_id TEXT PRIMARY KEY,
    stadium_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS football.opponent_teams (
    opponent_team_id TEXT PRIMARY KEY,
    opponent_team_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS football.coaches (
    coach_id TEXT PRIMARY KEY,
    coach_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS football.training_locations (
    training_location_id TEXT PRIMARY KEY,
    location_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS football.players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    jersey_number INTEGER NOT NULL CHECK (jersey_number > 0),
    primary_position football.position_enum NOT NULL,
    secondary_position football.position_enum,
    foot football.dominant_foot_enum NOT NULL,
    nationality TEXT NOT NULL,
    status football.player_status_enum NOT NULL,
    profile_image_url TEXT,
    joined_at TIMESTAMP NOT NULL,
    previous_team TEXT,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS football.physical_tests (
    physical_test_id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES football.players(player_id) ON DELETE CASCADE,
    test_date DATE NOT NULL,
    sprint_10m DOUBLE PRECISION,
    sprint_30m DOUBLE PRECISION,
    sprint_50m DOUBLE PRECISION,
    sprint_100m DOUBLE PRECISION,
    vertical_jump_cm DOUBLE PRECISION,
    agility_t_test_sec DOUBLE PRECISION,
    agility_505_sec DOUBLE PRECISION,
    agility_shuttle_run_sec DOUBLE PRECISION,
    UNIQUE (player_id, test_date)
);

CREATE TABLE IF NOT EXISTS football.physical_profiles (
    physical_data_id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES football.players(player_id) ON DELETE CASCADE,
    height_cm DOUBLE PRECISION NOT NULL CHECK (height_cm > 0),
    weight_kg DOUBLE PRECISION NOT NULL CHECK (weight_kg > 0),
    body_fat_percentage DOUBLE PRECISION CHECK (body_fat_percentage BETWEEN 0 AND 100),
    bmi DOUBLE PRECISION CHECK (bmi > 0),
    muscle_mass_kg DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL,
    UNIQUE (player_id, created_at)
);

CREATE TABLE IF NOT EXISTS football.injuries (
    injury_id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES football.players(player_id) ON DELETE CASCADE,
    injury_date DATE NOT NULL,
    injury_type TEXT NOT NULL,
    injury_part TEXT NOT NULL,
    severity_level football.injury_severity_enum NOT NULL,
    status football.injury_status_enum NOT NULL,
    expected_return_date DATE,
    actual_return_date DATE,
    surgery_required BOOLEAN NOT NULL,
    injury_mechanism TEXT NOT NULL,
    occurred_during football.injury_context_enum NOT NULL,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT injuries_expected_after_injury CHECK (
        expected_return_date IS NULL OR expected_return_date >= injury_date
    ),
    CONSTRAINT injuries_actual_after_injury CHECK (
        actual_return_date IS NULL OR actual_return_date >= injury_date
    )
);

CREATE TABLE IF NOT EXISTS football.matches (
    match_id TEXT PRIMARY KEY,
    match_date DATE NOT NULL,
    match_type football.match_type_enum NOT NULL,
    stadium_id TEXT NOT NULL REFERENCES football.stadiums(stadium_id),
    opponent_team_id TEXT NOT NULL REFERENCES football.opponent_teams(opponent_team_id),
    goals_for INTEGER NOT NULL DEFAULT 0 CHECK (goals_for >= 0),
    goals_against INTEGER NOT NULL DEFAULT 0 CHECK (goals_against >= 0),
    possession_for DOUBLE PRECISION CHECK (possession_for BETWEEN 0 AND 100),
    possession_against DOUBLE PRECISION CHECK (possession_against BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS football.match_team_stats (
    match_id TEXT PRIMARY KEY REFERENCES football.matches(match_id) ON DELETE CASCADE,
    assists INTEGER NOT NULL DEFAULT 0,
    shots INTEGER NOT NULL DEFAULT 0,
    shots_on_target INTEGER NOT NULL DEFAULT 0,
    shots_off_target INTEGER NOT NULL DEFAULT 0,
    blocked_shots INTEGER NOT NULL DEFAULT 0,
    shots_inside_penalty_area INTEGER NOT NULL DEFAULT 0,
    shots_outside_penalty_area INTEGER NOT NULL DEFAULT 0,
    offsides INTEGER NOT NULL DEFAULT 0,
    take_ons_attempted INTEGER NOT NULL DEFAULT 0,
    take_ons_succeeded INTEGER NOT NULL DEFAULT 0,
    take_ons_failed INTEGER NOT NULL DEFAULT 0,
    passes_attempted INTEGER NOT NULL DEFAULT 0,
    passes_succeeded INTEGER NOT NULL DEFAULT 0,
    passes_failed INTEGER NOT NULL DEFAULT 0,
    pass_accuracy DOUBLE PRECISION CHECK (pass_accuracy BETWEEN 0 AND 1),
    key_passes INTEGER NOT NULL DEFAULT 0,
    crosses_attempted INTEGER NOT NULL DEFAULT 0,
    crosses_succeeded INTEGER NOT NULL DEFAULT 0,
    crosses_failed INTEGER NOT NULL DEFAULT 0,
    cross_accuracy DOUBLE PRECISION CHECK (cross_accuracy BETWEEN 0 AND 1),
    control_under_pressure INTEGER NOT NULL DEFAULT 0,
    forward_passes_attempted INTEGER NOT NULL DEFAULT 0,
    forward_passes_succeeded INTEGER NOT NULL DEFAULT 0,
    forward_passes_failed INTEGER NOT NULL DEFAULT 0,
    sideways_passes_attempted INTEGER NOT NULL DEFAULT 0,
    sideways_passes_succeeded INTEGER NOT NULL DEFAULT 0,
    sideways_passes_failed INTEGER NOT NULL DEFAULT 0,
    backward_passes_attempted INTEGER NOT NULL DEFAULT 0,
    backward_passes_succeeded INTEGER NOT NULL DEFAULT 0,
    backward_passes_failed INTEGER NOT NULL DEFAULT 0,
    short_passes_attempted INTEGER NOT NULL DEFAULT 0,
    short_passes_succeeded INTEGER NOT NULL DEFAULT 0,
    short_passes_failed INTEGER NOT NULL DEFAULT 0,
    medium_passes_attempted INTEGER NOT NULL DEFAULT 0,
    medium_passes_succeeded INTEGER NOT NULL DEFAULT 0,
    medium_passes_failed INTEGER NOT NULL DEFAULT 0,
    long_passes_attempted INTEGER NOT NULL DEFAULT 0,
    long_passes_succeeded INTEGER NOT NULL DEFAULT 0,
    long_passes_failed INTEGER NOT NULL DEFAULT 0,
    passes_in_defensive_third_attempted INTEGER NOT NULL DEFAULT 0,
    passes_in_defensive_third_succeeded INTEGER NOT NULL DEFAULT 0,
    passes_in_defensive_third_failed INTEGER NOT NULL DEFAULT 0,
    passes_in_middle_third_attempted INTEGER NOT NULL DEFAULT 0,
    passes_in_middle_third_succeeded INTEGER NOT NULL DEFAULT 0,
    passes_in_middle_third_failed INTEGER NOT NULL DEFAULT 0,
    passes_in_final_third_attempted INTEGER NOT NULL DEFAULT 0,
    passes_in_final_third_succeeded INTEGER NOT NULL DEFAULT 0,
    passes_in_final_third_failed INTEGER NOT NULL DEFAULT 0,
    tackles_attempted INTEGER NOT NULL DEFAULT 0,
    tackles_succeeded INTEGER NOT NULL DEFAULT 0,
    tackles_failed INTEGER NOT NULL DEFAULT 0,
    interceptions INTEGER NOT NULL DEFAULT 0,
    recoveries INTEGER NOT NULL DEFAULT 0,
    clearances INTEGER NOT NULL DEFAULT 0,
    interventions INTEGER NOT NULL DEFAULT 0,
    blocks INTEGER NOT NULL DEFAULT 0,
    mistakes INTEGER NOT NULL DEFAULT 0,
    aerial_duels_total INTEGER NOT NULL DEFAULT 0,
    aerial_duels_won INTEGER NOT NULL DEFAULT 0,
    aerial_duels_lost INTEGER NOT NULL DEFAULT 0,
    aerial_duel_win_rate DOUBLE PRECISION CHECK (aerial_duel_win_rate BETWEEN 0 AND 1),
    ground_duels_total INTEGER NOT NULL DEFAULT 0,
    ground_duels_won INTEGER NOT NULL DEFAULT 0,
    ground_duels_lost INTEGER NOT NULL DEFAULT 0,
    ground_duel_win_rate DOUBLE PRECISION CHECK (ground_duel_win_rate BETWEEN 0 AND 1),
    duels_total INTEGER NOT NULL DEFAULT 0,
    duels_won INTEGER NOT NULL DEFAULT 0,
    duels_lost INTEGER NOT NULL DEFAULT 0,
    duel_win_rate DOUBLE PRECISION CHECK (duel_win_rate BETWEEN 0 AND 1),
    freekicks_shots INTEGER NOT NULL DEFAULT 0,
    freekicks_shots_on_target INTEGER NOT NULL DEFAULT 0,
    freekicks_crosses_attempted INTEGER NOT NULL DEFAULT 0,
    freekicks_crosses_succeeded INTEGER NOT NULL DEFAULT 0,
    freekicks_crosses_failed INTEGER NOT NULL DEFAULT 0,
    corners INTEGER NOT NULL DEFAULT 0,
    throw_ins INTEGER NOT NULL DEFAULT 0,
    goal_kicks_attempted INTEGER NOT NULL DEFAULT 0,
    goal_kicks_succeeded INTEGER NOT NULL DEFAULT 0,
    goal_kicks_failed INTEGER NOT NULL DEFAULT 0,
    fouls_committed INTEGER NOT NULL DEFAULT 0,
    fouls_won INTEGER NOT NULL DEFAULT 0,
    yellow_cards INTEGER NOT NULL DEFAULT 0,
    red_cards INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS football.player_match_stats (
    match_player_id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL REFERENCES football.matches(match_id) ON DELETE CASCADE,
    player_id TEXT NOT NULL REFERENCES football.players(player_id) ON DELETE CASCADE,
    position football.position_enum NOT NULL,
    minutes_played INTEGER NOT NULL CHECK (minutes_played >= 0),
    start_position football.position_enum,
    substitute_in INTEGER CHECK (substitute_in >= 0),
    substitute_out INTEGER CHECK (substitute_out >= 0),
    goals INTEGER NOT NULL DEFAULT 0,
    goals_type football.goal_type_enum,
    assists INTEGER NOT NULL DEFAULT 0,
    shots INTEGER NOT NULL DEFAULT 0,
    shots_on_target INTEGER NOT NULL DEFAULT 0,
    shots_off_target INTEGER NOT NULL DEFAULT 0,
    blocked_shots INTEGER NOT NULL DEFAULT 0,
    shots_inside_pa INTEGER NOT NULL DEFAULT 0,
    shots_outside_pa INTEGER NOT NULL DEFAULT 0,
    offsides INTEGER NOT NULL DEFAULT 0,
    freekicks INTEGER NOT NULL DEFAULT 0,
    corners INTEGER NOT NULL DEFAULT 0,
    throw_ins INTEGER NOT NULL DEFAULT 0,
    take_ons_attempted INTEGER NOT NULL DEFAULT 0,
    take_ons_succeeded INTEGER NOT NULL DEFAULT 0,
    take_ons_failed INTEGER NOT NULL DEFAULT 0,
    shooting_accuracy DOUBLE PRECISION CHECK (shooting_accuracy BETWEEN 0 AND 1),
    take_on_success_rate DOUBLE PRECISION CHECK (take_on_success_rate BETWEEN 0 AND 1),
    passes_attempted INTEGER NOT NULL DEFAULT 0,
    passes_completed INTEGER NOT NULL DEFAULT 0,
    passes_failed INTEGER NOT NULL DEFAULT 0,
    pass_accuracy DOUBLE PRECISION CHECK (pass_accuracy BETWEEN 0 AND 1),
    key_passes INTEGER NOT NULL DEFAULT 0,
    crosses_attempted INTEGER NOT NULL DEFAULT 0,
    crosses_succeeded INTEGER NOT NULL DEFAULT 0,
    crosses_failed INTEGER NOT NULL DEFAULT 0,
    cross_accuracy DOUBLE PRECISION CHECK (cross_accuracy BETWEEN 0 AND 1),
    forward_passes_attempted INTEGER NOT NULL DEFAULT 0,
    forward_passes_succeeded DOUBLE PRECISION,
    forward_passes_failed DOUBLE PRECISION,
    sideways_passes_attempted INTEGER NOT NULL DEFAULT 0,
    sideways_passes_succeeded DOUBLE PRECISION,
    sideways_passes_failed DOUBLE PRECISION,
    backward_passes_attempted INTEGER NOT NULL DEFAULT 0,
    backward_passes_succeeded DOUBLE PRECISION,
    backward_passes_failed DOUBLE PRECISION,
    short_passes_attempted INTEGER NOT NULL DEFAULT 0,
    short_passes_succeeded DOUBLE PRECISION,
    short_passes_failed DOUBLE PRECISION,
    medium_passes_attempted INTEGER NOT NULL DEFAULT 0,
    medium_passes_succeeded DOUBLE PRECISION,
    medium_passes_failed DOUBLE PRECISION,
    long_passes_attempted INTEGER NOT NULL DEFAULT 0,
    long_passes_succeeded DOUBLE PRECISION,
    long_passes_failed DOUBLE PRECISION,
    passes_in_defensive_third_attempted INTEGER NOT NULL DEFAULT 0,
    passes_in_defensive_third_succeeded DOUBLE PRECISION,
    passes_in_defensive_third_failed DOUBLE PRECISION,
    passes_in_middle_third_attempted INTEGER NOT NULL DEFAULT 0,
    passes_in_middle_third_succeeded DOUBLE PRECISION,
    passes_in_middle_third_failed DOUBLE PRECISION,
    passes_in_final_third_attempted INTEGER NOT NULL DEFAULT 0,
    passes_in_final_third_succeeded DOUBLE PRECISION,
    passes_in_final_third_failed DOUBLE PRECISION,
    control_under_pressure INTEGER NOT NULL DEFAULT 0,
    tackles_attempted INTEGER NOT NULL DEFAULT 0,
    tackles_succeeded INTEGER NOT NULL DEFAULT 0,
    tackles_failed INTEGER NOT NULL DEFAULT 0,
    interceptions INTEGER NOT NULL DEFAULT 0,
    recoveries INTEGER NOT NULL DEFAULT 0,
    clearances INTEGER NOT NULL DEFAULT 0,
    interventions INTEGER NOT NULL DEFAULT 0,
    blocks INTEGER NOT NULL DEFAULT 0,
    mistakes INTEGER NOT NULL DEFAULT 0,
    fouls_committed INTEGER NOT NULL DEFAULT 0,
    fouls_won INTEGER NOT NULL DEFAULT 0,
    yellow_cards INTEGER NOT NULL DEFAULT 0,
    red_cards INTEGER NOT NULL DEFAULT 0,
    aerial_duels_total INTEGER NOT NULL DEFAULT 0,
    aerial_duels_won INTEGER NOT NULL DEFAULT 0,
    aerial_duels_lost INTEGER NOT NULL DEFAULT 0,
    ground_duels_total INTEGER NOT NULL DEFAULT 0,
    ground_duels_won INTEGER NOT NULL DEFAULT 0,
    ground_duels_lost INTEGER NOT NULL DEFAULT 0,
    goalkeeper_player_id TEXT REFERENCES football.players(player_id),
    goals_conceded DOUBLE PRECISION,
    shots_on_target_faced DOUBLE PRECISION,
    saves DOUBLE PRECISION,
    save_rate DOUBLE PRECISION CHECK (save_rate IS NULL OR save_rate BETWEEN 0 AND 1),
    catches DOUBLE PRECISION,
    punches DOUBLE PRECISION,
    goal_kicks_attempted DOUBLE PRECISION,
    goal_kicks_succeeded DOUBLE PRECISION,
    goal_kicks_failed DOUBLE PRECISION,
    aerial_clearances_attempted DOUBLE PRECISION,
    aerial_clearances_succeeded DOUBLE PRECISION,
    aerial_clearances_failed DOUBLE PRECISION,
    UNIQUE (match_id, player_id)
);

CREATE TABLE IF NOT EXISTS football.trainings (
    training_id TEXT PRIMARY KEY,
    training_date DATE NOT NULL,
    training_type football.training_type_enum NOT NULL,
    training_detail TEXT NOT NULL,
    training_focus football.training_focus_enum NOT NULL,
    session_name football.session_name_enum NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    intensity_level football.intensity_level_enum NOT NULL,
    coach_id TEXT NOT NULL REFERENCES football.coaches(coach_id),
    training_location_id TEXT NOT NULL REFERENCES football.training_locations(training_location_id),
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT trainings_end_after_start CHECK (end_time > start_time)
);

CREATE TABLE IF NOT EXISTS football.match_gps_stats (
    match_gps_id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL REFERENCES football.matches(match_id) ON DELETE CASCADE,
    player_id TEXT NOT NULL REFERENCES football.players(player_id) ON DELETE CASCADE,
    total_distance DOUBLE PRECISION NOT NULL CHECK (total_distance >= 0),
    play_time_min INTEGER NOT NULL CHECK (play_time_min >= 0),
    avg_speed DOUBLE PRECISION NOT NULL CHECK (avg_speed >= 0),
    max_speed DOUBLE PRECISION NOT NULL CHECK (max_speed >= 0),
    distance_0_15_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_0_15_min >= 0),
    distance_15_30_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_15_30_min >= 0),
    distance_30_45_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_30_45_min >= 0),
    distance_45_60_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_45_60_min >= 0),
    distance_60_75_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_60_75_min >= 0),
    distance_75_90_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_75_90_min >= 0),
    sprint_count INTEGER NOT NULL DEFAULT 0 CHECK (sprint_count >= 0),
    sprint_distance DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (sprint_distance >= 0),
    distance_speed_0_5 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_0_5 >= 0),
    distance_speed_5_10 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_5_10 >= 0),
    distance_speed_10_15 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_10_15 >= 0),
    distance_speed_15_20 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_15_20 >= 0),
    distance_speed_20_25 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_20_25 >= 0),
    distance_speed_25_plus DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_25_plus >= 0),
    cod_count INTEGER NOT NULL DEFAULT 0 CHECK (cod_count >= 0),
    accel_count INTEGER NOT NULL DEFAULT 0 CHECK (accel_count >= 0),
    decel_count INTEGER NOT NULL DEFAULT 0 CHECK (decel_count >= 0),
    hi_accel_count INTEGER NOT NULL DEFAULT 0 CHECK (hi_accel_count >= 0),
    hi_decel_count INTEGER NOT NULL DEFAULT 0 CHECK (hi_decel_count >= 0),
    UNIQUE (match_id, player_id)
);

CREATE TABLE IF NOT EXISTS football.training_gps_stats (
    training_gps_id TEXT PRIMARY KEY,
    training_id TEXT NOT NULL REFERENCES football.trainings(training_id) ON DELETE CASCADE,
    player_id TEXT NOT NULL REFERENCES football.players(player_id) ON DELETE CASCADE,
    total_distance DOUBLE PRECISION NOT NULL CHECK (total_distance >= 0),
    play_time_min DOUBLE PRECISION CHECK (play_time_min IS NULL OR play_time_min >= 0),
    avg_speed DOUBLE PRECISION NOT NULL CHECK (avg_speed >= 0),
    max_speed DOUBLE PRECISION NOT NULL CHECK (max_speed >= 0),
    distance_0_15_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_0_15_min >= 0),
    distance_15_30_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_15_30_min >= 0),
    distance_30_45_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_30_45_min >= 0),
    distance_45_60_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_45_60_min >= 0),
    distance_60_75_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_60_75_min >= 0),
    distance_75_90_min DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_75_90_min >= 0),
    sprint_count INTEGER NOT NULL DEFAULT 0 CHECK (sprint_count >= 0),
    sprint_distance DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (sprint_distance >= 0),
    distance_speed_0_5 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_0_5 >= 0),
    distance_speed_5_10 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_5_10 >= 0),
    distance_speed_10_15 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_10_15 >= 0),
    distance_speed_15_20 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_15_20 >= 0),
    distance_speed_20_25 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_20_25 >= 0),
    distance_speed_25_plus DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (distance_speed_25_plus >= 0),
    cod_count INTEGER NOT NULL DEFAULT 0 CHECK (cod_count >= 0),
    accel_count INTEGER NOT NULL DEFAULT 0 CHECK (accel_count >= 0),
    decel_count INTEGER NOT NULL DEFAULT 0 CHECK (decel_count >= 0),
    hi_accel_count INTEGER NOT NULL DEFAULT 0 CHECK (hi_accel_count >= 0),
    hi_decel_count INTEGER NOT NULL DEFAULT 0 CHECK (hi_decel_count >= 0),
    UNIQUE (training_id, player_id)
);

CREATE TABLE IF NOT EXISTS football.evaluations (
    evaluation_id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES football.players(player_id) ON DELETE CASCADE,
    evaluation_date DATE NOT NULL,
    technical DOUBLE PRECISION NOT NULL CHECK (technical BETWEEN 0 AND 100),
    tactical DOUBLE PRECISION NOT NULL CHECK (tactical BETWEEN 0 AND 100),
    physical DOUBLE PRECISION NOT NULL CHECK (physical BETWEEN 0 AND 100),
    mental DOUBLE PRECISION NOT NULL CHECK (mental BETWEEN 0 AND 100),
    coach_comment TEXT NOT NULL,
    UNIQUE (player_id, evaluation_date)
);

CREATE TABLE IF NOT EXISTS football.counseling_notes (
    counseling_id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES football.players(player_id) ON DELETE CASCADE,
    counseling_date DATE NOT NULL,
    topic football.counseling_topic_enum NOT NULL,
    summary TEXT NOT NULL,
    UNIQUE (player_id, counseling_date)
);

CREATE INDEX IF NOT EXISTS idx_players_status ON football.players(status);
CREATE INDEX IF NOT EXISTS idx_physical_tests_player_date ON football.physical_tests(player_id, test_date DESC);
CREATE INDEX IF NOT EXISTS idx_physical_profiles_player_created_at ON football.physical_profiles(player_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_injuries_player_date ON football.injuries(player_id, injury_date DESC);
CREATE INDEX IF NOT EXISTS idx_matches_date ON football.matches(match_date DESC);
CREATE INDEX IF NOT EXISTS idx_player_match_stats_player ON football.player_match_stats(player_id, match_id);
CREATE INDEX IF NOT EXISTS idx_trainings_date ON football.trainings(training_date DESC);
CREATE INDEX IF NOT EXISTS idx_match_gps_player ON football.match_gps_stats(player_id, match_id);
CREATE INDEX IF NOT EXISTS idx_training_gps_player ON football.training_gps_stats(player_id, training_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_player_date ON football.evaluations(player_id, evaluation_date DESC);
CREATE INDEX IF NOT EXISTS idx_counseling_player_date ON football.counseling_notes(player_id, counseling_date DESC);
