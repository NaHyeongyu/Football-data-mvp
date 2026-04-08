Match Data Schema

# 1. Match Metadata

| Column | 설명 |
|------|------|
| match_id | 경기 ID |
| match_date | 경기 날짜 |
| match_type | 경기 종류(친선, 공식)|
| stadium | 경기장 |
| home_team | 홈팀 |
| away_team | 원정팀 |
| score_home | 홈팀 득점 |
| score_away | 원정팀 득점 |
| possession_home | 홈팀 점유율 |
| possession_away | 원정팀 점유율 |

---

# 2. Team Match Stats

## 2-1. 공격

| Column | 설명 |
|------|------|
| goals | 득점 |
| assists | 도움 |
| shots | 전체 슈팅 |
| shots_on_target | 유효슈팅 |
| shots_off_target | 빗나간 슈팅 |
| blocked_shots | 상대 수비에 막힌 슈팅 |
| shots_inside_penalty_area | 박스 안 슈팅 |
| shots_outside_penalty_area | 박스 밖 슈팅 |
| offsides | 오프사이드 |
| take_ons_attempted | 돌파 시도 |
| take_ons_succeeded | 돌파 성공 |
| take_ons_failed | 돌파 실패 |

## 2-2. 패스

| Column | 설명 |
|------|------|
| passes_attempted | 패스 시도 |
| passes_succeeded | 패스 성공 |
| passes_failed | 패스 실패 |
| pass_accuracy | 패스 성공률 |
| key_passes | 키패스 |
| crosses_attempted | 크로스 시도 |
| crosses_succeeded | 크로스 성공 |
| crosses_failed | 크로스 실패 |
| cross_accuracy | 크로스 성공률 |
| control_under_pressure | 압박 하 컨트롤 성공 |

## 2-3. 패스 방향/거리/구역

| Column | 설명 |
|------|------|
| forward_passes_attempted | 전진 패스 시도 |
| forward_passes_succeeded | 전진 패스 성공 |
| forward_passes_failed | 전진 패스 실패 |
| sideways_passes_attempted | 횡패스 시도 |
| sideways_passes_succeeded | 횡패스 성공 |
| sideways_passes_failed | 횡패스 실패 |
| backward_passes_attempted | 후방 패스 시도 |
| backward_passes_succeeded | 후방 패스 성공 |
| backward_passes_failed | 후방 패스 실패 |
| short_passes_attempted | 단거리 패스 시도 |
| short_passes_succeeded | 단거리 패스 성공 |
| short_passes_failed | 단거리 패스 실패 |
| medium_passes_attempted | 중거리 패스 시도 |
| medium_passes_succeeded | 중거리 패스 성공 |
| medium_passes_failed | 중거리 패스 실패 |
| long_passes_attempted | 장거리 패스 시도 |
| long_passes_succeeded | 장거리 패스 성공 |
| long_passes_failed | 장거리 패스 실패 |
| passes_in_defensive_third_attempted | 수비 구역 패스 시도 |
| passes_in_defensive_third_succeeded | 수비 구역 패스 성공 |
| passes_in_defensive_third_failed | 수비 구역 패스 실패 |
| passes_in_middle_third_attempted | 중원 구역 패스 시도 |
| passes_in_middle_third_succeeded | 중원 구역 패스 성공 |
| passes_in_middle_third_failed | 중원 구역 패스 실패 |
| passes_in_final_third_attempted | 공격 구역 패스 시도 |
| passes_in_final_third_succeeded | 공격 구역 패스 성공 |
| passes_in_final_third_failed | 공격 구역 패스 실패 |

## 2-4. 수비

| Column | 설명 |
|------|------|
| tackles_attempted | 태클 시도 |
| tackles_succeeded | 태클 성공 |
| tackles_failed | 태클 실패 |
| interceptions | 인터셉트 |
| recoveries | 리커버리 |
| clearances | 클리어런스 |
| interventions | 인터벤션 |
| blocks | 블록 |
| mistakes | 실수 |

## 2-5. 경합

| Column | 설명 |
|------|------|
| aerial_duels_total | 공중볼 경합 수 |
| aerial_duels_won | 공중볼 승리 |
| aerial_duels_lost | 공중볼 패배 |
| aerial_duel_win_rate | 공중볼 승률 |
| ground_duels_total | 지상 경합 수 |
| ground_duels_won | 지상 경합 승리 |
| ground_duels_lost | 지상 경합 패배 |
| ground_duel_win_rate | 지상 경합 승률 |
| duels_total | 전체 경합 수 |
| duels_won | 전체 경합 승리 |
| duels_lost | 전체 경합 패배 |
| duel_win_rate | 전체 경합 승률 |

## 2-6. 세트피스

| Column | 설명 |
|------|------|
| freekicks_shots | 프리킥 직접 슈팅 |
| freekicks_shots_on_target | 프리킥 유효슈팅 |
| freekicks_crosses_attempted | 프리킥 크로스 시도 |
| freekicks_crosses_succeeded | 프리킥 크로스 성공 |
| freekicks_crosses_failed | 프리킥 크로스 실패 |
| corners | 코너킥 |
| throw_ins | 스로인 |
| goal_kicks_attempted | 골킥 시도 |
| goal_kicks_succeeded | 골킥 성공 |
| goal_kicks_failed | 골킥 실패 |

## 2-7. 징계 / 파울

| Column | 설명 |
|------|------|
| fouls_committed | 범한 파울 |
| fouls_won | 얻어낸 파울 |
| yellow_cards | 경고 |
| red_cards | 퇴장 |

---

# 3. Player Offensive Stats

| Column | 설명 |
|------|------|
| player_name | 선수명 |
| player_birth_day | 생년월일 |
| position | 포지션 |
| minutes_played | 출전 시간 |
| start_position | 선발 포지션 |
| substitute_in | 교체 투입 |
| substitute_out | 교체 아웃 |
| goals | 득점 |
| goals_type | 득점 방법 |
| assists | 도움 |
| shots | 슈팅 |
| shots_on_target | 유효슈팅 |
| shots_off_target | 빗나간 슈팅 |
| blocked_shots | 막힌 슈팅 |
| shots_inside_pa | 박스 안 슈팅 |
| shots_outside_pa | 박스 밖 슈팅 |
| offsides | 오프사이드 |
| freekicks | 프리킥 관여 |
| corners | 코너킥 관여 |
| throw_ins | 스로인 관여 |
| take_ons_attempted | 돌파 시도 |
| take_ons_succeeded | 돌파 성공 |
| take_ons_failed | 돌파 실패 |
| shooting_accuracy | 슈팅 정확도 |
| take_on_success_rate | 돌파 성공률 |

---

# 4. Player Passing / Distribution Stats

| Column | 설명 |
|------|------|
| passes_attempted | 패스 시도 |
| passes_completed | 패스 성공 |
| passes_failed | 패스 실패 |
| pass_accuracy | 패스 성공률 |
| key_passes | 키패스 |
| crosses_attempted | 크로스 시도 |
| crosses_success | 크로스 성공 |
| crosses_failed | 크로스 실패 |
| cross_accuracy | 크로스 성공률 |
| forward_passes_attempted | 전진 패스 시도 |
| forward_passes_succeeded | 전진 패스 성공 |
| forward_passes_failed | 전진 패스 실패 |
| sideways_passes_attempted | 횡패스 시도 |
| sideways_passes_succeeded | 횡패스 성공 |
| sideways_passes_failed | 횡패스 실패 |
| backward_passes_attempted | 후방 패스 시도 |
| backward_passes_succeeded | 후방 패스 성공 |
| backward_passes_failed | 후방 패스 실패 |
| short_passes_attempted | 단거리 패스 시도 |
| short_passes_succeeded | 단거리 패스 성공 |
| short_passes_failed | 단거리 패스 실패 |
| medium_passes_attempted | 중거리 패스 시도 |
| medium_passes_succeeded | 중거리 패스 성공 |
| medium_passes_failed | 중거리 패스 실패 |
| long_passes_attempted | 장거리 패스 시도 |
| long_passes_succeeded | 장거리 패스 성공 |
| long_passes_failed | 장거리 패스 실패 |
| passes_in_defensive_third_attempted | 수비 3분할 시작 패스 시도 |
| passes_in_defensive_third_succeeded | 수비 3분할 시작 패스 성공 |
| passes_in_defensive_third_failed | 수비 3분할 시작 패스 실패 |
| passes_in_middle_third_attempted | 중원 3분할 시작 패스 시도 |
| passes_in_middle_third_succeeded | 중원 3분할 시작 패스 성공 |
| passes_in_middle_third_failed | 중원 3분할 시작 패스 실패 |
| passes_in_final_third_attempted | 공격 3분할 시작 패스 시도 |
| passes_in_final_third_succeeded | 공격 3분할 시작 패스 성공 |
| passes_in_final_third_failed | 공격 3분할 시작 패스 실패 |
| control_under_pressure | 압박 하 컨트롤 성공 |

---

# 5. Player Defensive Stats

| Column | 설명 |
|------|------|
| tackles_attempted | 태클 시도 |
| tackles_success | 태클 성공 |
| tackles_failed | 태클 실패 |
| interceptions | 인터셉트 |
| recoveries | 리커버리 |
| clearances | 클리어런스 |
| interventions | 인터벤션 |
| blocks | 블록 |
| mistakes | 실수 |
| fouls_committed | 범한 파울 |
| fouls_won | 얻어낸 파울 |
| yellow_cards | 경고 |
| red_cards | 퇴장 |
| aerial_duels_total | 공중볼 경합 수 |
| aerial_duels_won | 공중볼 승리 |
| aerial_duels_lost | 공중볼 패배 |
| ground_duels_total | 지상 경합 수 |
| ground_duels_won | 지상 경합 승리 |
| ground_duels_lost | 지상 경합 패배 |
| duel_total | 전체 경합 수 |
| duel_won | 전체 경합 승리 |
| duel_lost | 전체 경합 패배 |

---

# 6. Goalkeeper Stats

| Column | 설명 |
|------|------|
| goalkeeper_id | 골키퍼 ID |
| minutes_played | 출전 시간 |
| goals_conceded | 실점 |
| shots_on_target_faced | 상대 유효슈팅 허용 |
| saves | 세이브 |
| save_rate | 세이브율 |
| catches | 캐치 |
| punches | 펀칭 |
| goal_kicks_attempted | 골킥 시도 |
| goal_kicks_succeeded | 골킥 성공 |
| goal_kicks_failed | 골킥 실패 |
| aerial_clearances_attempted | 공중 클리어 시도 |
| aerial_clearances_succeeded | 공중 클리어 성공 |
| aerial_clearances_failed | 공중 클리어 실패 |

---

# 7. Event Summary Stats

| Column | 설명 |
|------|------|
| total_shots | 전체 슈팅 |
| shots_on_target | 유효슈팅 |
| shots_off_target | 빗나간 슈팅 |
| blocked_shots | 막힌 슈팅 |
| total_passes_attempted | 전체 패스 시도 |
| total_passes_succeeded | 전체 패스 성공 |
| total_passes_failed | 전체 패스 실패 |
| total_crosses_attempted | 전체 크로스 시도 |
| total_crosses_succeeded | 전체 크로스 성공 |
| total_crosses_failed | 전체 크로스 실패 |
| total_take_ons_attempted | 전체 돌파 시도 |
| total_take_ons_succeeded | 전체 돌파 성공 |
| total_take_ons_failed | 전체 돌파 실패 |
| total_tackles_attempted | 전체 태클 시도 |
| total_tackles_succeeded | 전체 태클 성공 |
| total_tackles_failed | 전체 태클 실패 |
| total_interceptions | 전체 인터셉트 |
| total_recoveries | 전체 리커버리 |
| total_clearances | 전체 클리어런스 |
| total_aerial_duels | 전체 공중볼 경합 |
| total_aerial_duels_won | 전체 공중볼 승리 |
| total_aerial_duels_lost | 전체 공중볼 패배 |
| total_ground_duels | 전체 지상 경합 |
| total_ground_duels_won | 전체 지상 경합 승리 |
| total_ground_duels_lost | 전체 지상 경합 패배 |

---
