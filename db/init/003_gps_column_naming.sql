DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'football'
          AND table_name = 'match_gps_stats'
          AND column_name = 'total_distance_m'
    ) THEN
        ALTER TABLE football.match_gps_stats RENAME COLUMN total_distance_m TO total_distance;
        ALTER TABLE football.match_gps_stats RENAME COLUMN avg_speed_kmh TO avg_speed;
        ALTER TABLE football.match_gps_stats RENAME COLUMN max_speed_kmh TO max_speed;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_0_15_min_m TO distance_0_15_min;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_15_30_min_m TO distance_15_30_min;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_30_45_min_m TO distance_30_45_min;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_45_60_min_m TO distance_45_60_min;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_60_75_min_m TO distance_60_75_min;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_75_90_min_m TO distance_75_90_min;
        ALTER TABLE football.match_gps_stats RENAME COLUMN sprint_distance_m TO sprint_distance;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_speed_0_5_km_m TO distance_speed_0_5;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_speed_5_10_km_m TO distance_speed_5_10;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_speed_10_15_km_m TO distance_speed_10_15;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_speed_15_20_km_m TO distance_speed_15_20;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_speed_20_25_km_m TO distance_speed_20_25;
        ALTER TABLE football.match_gps_stats RENAME COLUMN distance_speed_25_plus_km_m TO distance_speed_25_plus;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'football'
          AND table_name = 'training_gps_stats'
          AND column_name = 'total_distance_m'
    ) THEN
        ALTER TABLE football.training_gps_stats RENAME COLUMN total_distance_m TO total_distance;
        ALTER TABLE football.training_gps_stats RENAME COLUMN avg_speed_kmh TO avg_speed;
        ALTER TABLE football.training_gps_stats RENAME COLUMN max_speed_kmh TO max_speed;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_0_15_min_m TO distance_0_15_min;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_15_30_min_m TO distance_15_30_min;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_30_45_min_m TO distance_30_45_min;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_45_60_min_m TO distance_45_60_min;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_60_75_min_m TO distance_60_75_min;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_75_90_min_m TO distance_75_90_min;
        ALTER TABLE football.training_gps_stats RENAME COLUMN sprint_distance_m TO sprint_distance;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_speed_0_5_km_m TO distance_speed_0_5;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_speed_5_10_km_m TO distance_speed_5_10;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_speed_10_15_km_m TO distance_speed_10_15;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_speed_15_20_km_m TO distance_speed_15_20;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_speed_20_25_km_m TO distance_speed_20_25;
        ALTER TABLE football.training_gps_stats RENAME COLUMN distance_speed_25_plus_km_m TO distance_speed_25_plus;
    END IF;
END
$$;
