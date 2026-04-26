# Football Data System

Football Data System 작업용 저장소입니다.

현재는 `frontend` 단독 실행이 가능하고, 별도로 `virtual_players_2008_complete_with_all_staff_data.xlsx`를 PostgreSQL로 적재하는 `db` 구성도 포함합니다.

## 디렉터리 구조

- `frontend/`: Next.js 기반 프론트엔드
- `backend/`: FastAPI 기반 API
- `db/`: PostgreSQL 스키마, 뷰, 적재 스크립트
- `data/excel/`: 향후 재구성을 위해 남겨둔 원본 샘플 Excel
- `data/csv/`: 향후 재구성을 위해 남겨둔 원본 샘플 CSV
- `references/`: 워크북 정규화 / enum / 감사 스크립트

## 빠른 시작

```bash
cd frontend
npm install
npm run dev
```

기본 라우트:

- `/`: 운영 홈
- `/players`: 선수 로스터
- `/players/[playerId]`: 선수 상세
- `/dashboard`: 팀 분석
- `/matches`: 경기 로그
- `/physical`: 피지컬 / GPS
- `/injury`: 메디컬 / AT
- `/assistant`: DB + pgvector RAG 질의 에이전트
- `/reports`: 리포트

## 현재 데이터 구조

데이터 접근 레이어:

- `frontend/lib/team-api.ts`
- `frontend/lib/data-store.ts`

프론트 데이터 소스:

- FastAPI 백엔드 DB 연동 API
- `GET /api/frontend/players-directory`
- `GET /api/frontend/players/{player_id}`
- `GET /api/frontend/physical-overview`
- `GET /api/team/*`

## DB 적재

```bash
cd db
docker compose up -d
cd ..
./.venv/bin/python db/scripts/load_virtual_players_workbook.py
```

상세 설명은 `db/README.md`를 보면 됩니다.

## Assistant RAG 인덱싱

기본값은 Ollama 기반입니다.

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
./.venv/bin/python db/scripts/index_assistant_rag.py
```

OpenAI를 쓰려면 환경변수를 바꿉니다.

```bash
ASSISTANT_PROVIDER=openai \
ASSISTANT_MODEL=gpt-4o-mini \
ASSISTANT_EMBEDDING_PROVIDER=openai \
ASSISTANT_EMBEDDING_MODEL=text-embedding-3-small \
OPENAI_API_KEY=... \
./.venv/bin/python db/scripts/index_assistant_rag.py
```

## API 실행

```bash
./.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

현재 구현된 엔드포인트:

- `GET /healthz`
- `GET /api/players`
- `GET /api/players/injury-risk`
- `GET /api/players/{player_id}`
- `GET /api/assistant/status`
- `POST /api/assistant/query`
