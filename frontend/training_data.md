# Training Session Schema

| Column | Type | 설명 |
|------|------|------|
| training_id | string | 훈련 ID |
| training_date | date | 훈련 날짜 |
| training_type | string | 훈련 유형 |
| training_detail | string | 훈련 내용 |
| training_focus | string | 훈련 목적 |
| session_name | string | 훈련명 |
| start_time | datetime | 시작 시간 |
| end_time | datetime | 종료 시간 |
| intensity_level | enum | 훈련 강도 (low / medium / high / very_high) |
| coach_name | string | 담당 코치 |
| location | string | 훈련 장소 |
| notes | string | 특이사항 |
| created_at | datetime | 생성일 |
| updated_at | datetime | 수정일 |