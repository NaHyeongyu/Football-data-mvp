from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers.assistant import router as assistant_router
from .routers.frontend import router as frontend_router
from .routers.players import router as players_router
from .routers.team import router as team_router


app = FastAPI(
    title="Football Data System API",
    version="0.1.0",
    description="Current roster and player data API backed by PostgreSQL.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(players_router)
app.include_router(team_router)
app.include_router(assistant_router)
app.include_router(frontend_router)
