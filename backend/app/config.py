from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@127.0.0.1:5432/football_data",
    )
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    llama_base_url: str = os.getenv("LLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    llama_model: str = os.getenv("LLAMA_MODEL", "llama3.1:8b")
    llama_timeout_seconds: float = float(os.getenv("LLAMA_TIMEOUT_SECONDS", "90"))
    assistant_max_steps: int = int(os.getenv("ASSISTANT_MAX_STEPS", "3"))
    assistant_sql_max_rows: int = int(os.getenv("ASSISTANT_SQL_MAX_ROWS", "100"))
    assistant_sql_preview_rows: int = int(os.getenv("ASSISTANT_SQL_PREVIEW_ROWS", "8"))
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    )


settings = Settings()
