# Backend API

FastAPI 기반 백엔드입니다. 현재는 PostgreSQL에 적재된 선수 정보를 조회하는 API부터 제공합니다.

## 실행

```bash
./.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 엔드포인트

- `GET /healthz`
- `GET /api/players`
- `GET /api/players/injury-risk`
- `GET /api/players/{player_id}`
- `GET /api/assistant/status`
- `POST /api/assistant/query`

## Assistant API

`POST /api/assistant/query`

```json
{ "question": "최근 2주 훈련 부하가 높은 선수 알려줘" }
```

Assistant는 고정 SQL 도구로 정형 데이터를 조회하고, `football.assistant_chunks`의 pgvector 임베딩을 검색해 문서/노트 근거를 함께 사용합니다.

기본 provider는 Ollama입니다.

- `ASSISTANT_PROVIDER`: `ollama` 또는 `openai`
- `ASSISTANT_MODEL`: 답변 생성 모델
- `ASSISTANT_EMBEDDING_PROVIDER`: `ollama` 또는 `openai`
- `ASSISTANT_EMBEDDING_MODEL`: 임베딩 모델

## 목록 API

`GET /api/players`

query params:

- `q`: 이름 / 선수 ID / 이전 팀 검색
- `position`: 포지션 필터
- `status`: `active`, `injured`
- `limit`
- `offset`

응답은 다음 묶음을 포함합니다.

- 기본 프로필
- 최신 피지컬 프로필
- 최신 부상 상태
- 경기 누적 요약

## 상세 API

`GET /api/players/{player_id}`

추가 query params:

- `recent_match_limit`: 최근 경기 반환 개수

## 부상 위험도 API

`GET /api/players/injury-risk`

query params:

- `as_of_date`: 스냅샷 날짜
- `risk_band`: `normal`, `watch`, `risk`
- `limit`

점수 구성:

- 최근 부하 변화
- 최근 7일 스프린트 급증
- 최근 7일 활동량 급감(GK 제외)
- 최근 피지컬 변화
- 최근 180/365일 부상 이력
- 복귀 직후 / 재활 상태
- 최근 통증 / 불편감 키워드와 메디컬 상담 신호

주의:

- `physical_tests`는 이 모델에서 사용하지 않습니다.
- 부하 계산은 최신 세션 날짜 기준으로, 전체 스냅샷은 최신 관측 데이터 기준으로 계산합니다.

## CSV 추출

```bash
./.venv/bin/python backend/scripts/export_injury_risk_scores.py --limit 10
```
