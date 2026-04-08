# Player physical data Schema

| Column | Type | 설명 |
|------|------|------|
| gps_id | string | gps 기록 ID |
| match_id | string | 경기 ID |
| training_id | string | 훈련 ID |
| player_id | string | 선수 ID |
| distance | float | 총 이동 거리 |
| play_time_min | float | 플레이 시간 |
| avg_speed | float | 평균 속도 |
| max_speed | float | 최고 속도 |
| distance | float | 총 이동 거리 |
| 0~15min_distance | float | 0~15분 이동 거리 |
| 15~30min_distance | float | 15~30분 이동 거리 |
| 30~45min_distance | float | 30~45분 이동 거리 |
| 45~60min_distance | float | 45~60분 이동 거리 |
| 60~75min_distance | float | 60~75분 이동 거리 |
| 75~90min_distance | float | 75~90분 이동 거리 |
| sprint_count | integer | 스프린트 횟수 |
| sprint_distance | float | 스프린트 거리 |
| distance_speed_0_5km | float | 시속 0km~5km 이동 거리 |
| distance_speed_5_10km | float | 시속 5km~10km 이동 거리 |
| distance_speed_10_15km | float | 시속 10km~15km 이동 거리 |
| distance_speed_15_20km | float | 시속 15km~20km 이동 거리 |
| distance_speed_20_25km | float | 시속 20km~25km 이동 거리 |
| distance_speed_25< | float | 시속 25km~ 이동 거리 |
| cod_count | integer | 방향 전환 횟수 |
| accel_count | integer | 가속 횟수 |
| decel_count | integer | 감속 횟수 |
| hi_accel_count | integer | 고강도 가속 횟수 |
| hi_decel_count | integer | 고강도 감속 횟수 |
