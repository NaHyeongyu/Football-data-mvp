# Database Setup

`virtual_players_2008_complete_with_all_staff_data.xlsx` 워크북을 기준으로 한 PostgreSQL 적재 구성입니다.

## 구성

- `docker-compose.yml`: pgvector 확장이 포함된 Postgres 실행
- `init/001_schema.sql`: enum, lookup, fact 테이블
- `init/002_views.sql`: 자주 쓸 뷰
- `ERD.md`: Mermaid ERD
- `scripts/load_virtual_players_workbook.py`: 워크북 적재 스크립트

## 기본 스키마

- schema: `football`
- enum type: 포지션, 풋, 부상 상태, 경기 타입, 트레이닝 타입 등
- lookup table:
  - `stadiums`
  - `opponent_teams`
  - `coaches`
  - `training_locations`
- core table:
  - `players`
  - `physical_tests`
  - `physical_profiles`
  - `injuries`
  - `matches`
  - `match_team_stats`
  - `player_match_stats`
  - `trainings`
  - `match_gps_stats`
  - `training_gps_stats`
  - `evaluations`
  - `counseling_notes`
  - `assistant_documents`
  - `assistant_chunks`

## 실행

```bash
cd db
docker compose up -d
cd ..
./.venv/bin/python db/scripts/load_virtual_players_workbook.py
```

RAG 인덱스는 워크북 적재 후 별도로 생성합니다.

```bash
./.venv/bin/python db/scripts/index_assistant_rag.py
```

기본 접속 정보:

- host: `127.0.0.1`
- port: `5432`
- db: `football_data`
- user: `postgres`
- password: `postgres`

`DATABASE_URL`을 넘기면 다른 접속 정보로도 적재할 수 있습니다.

```bash
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/football_data \
./.venv/bin/python db/scripts/load_virtual_players_workbook.py
```

## 기본 뷰

- `football.player_latest_physical_profile`
- `football.player_current_injury_status`
- `football.player_match_facts`
