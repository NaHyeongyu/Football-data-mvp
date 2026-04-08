# Player Injury History Schema

| Column | Type | 설명 |
|------|------|------|
| injury_id | string | 부상 이력 ID |
| player_id | string | 선수 ID |
| injury_date | date | 부상 발생일 |
| injury_type | string | 부상 유형 |
| injury_part | string | 부상 부위 |
| severity_level | string | 부상 정도 |
| status | string | 현재 상태 |
| expected_return_date | date | 예상 복귀일 |
| actual_return_date | date | 실제 복귀일 |
| surgery_required | boolean | 수술 여부 |
| injury_mechanism | string | 부상 발생 방식 |
| occurred_during | string | 발생 상황 (match / training / outside) |
| notes | string | 특이사항 |
| created_at | datetime | 생성일 |
| updated_at | datetime | 수정일 |