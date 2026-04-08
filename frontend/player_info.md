# Player Information Schema

| Column | Type | 설명 |
|------|------|------|
| player_id | string | 플랫폼 내부 선수 고유 ID |
| name | string | 선수 전체 이름 |
| date_of_birth | date | 생년월일 |
| jersey_number | integer | 등번호 |
| primary_position | enum | 주 포지션 |
| secondary_position | enum | 부 포지션 |
| foot | enum | 주발 (right / left / both) |
| nationality | string | 국적 |
| status | enum | 선수 상태 (active / injured / 방출) |
| profile_image_url | string | 프로필 이미지 |
| joined_at | datetime | 선수 입단일 |
| previous_team | string | 이전소속팀 |
| updated_at | datetime | 수정일 |