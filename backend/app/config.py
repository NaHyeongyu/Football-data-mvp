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
    assistant_provider: str = os.getenv("ASSISTANT_PROVIDER", "ollama")
    assistant_model: str = os.getenv("ASSISTANT_MODEL", os.getenv("LLAMA_MODEL", "llama3.1:8b"))
    assistant_base_url: str = os.getenv(
        "ASSISTANT_BASE_URL",
        os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
    )
    assistant_timeout_seconds: float = float(os.getenv("ASSISTANT_TIMEOUT_SECONDS", "90"))
    assistant_rag_top_k: int = int(os.getenv("ASSISTANT_RAG_TOP_K", "5"))
    assistant_embedding_provider: str = os.getenv("ASSISTANT_EMBEDDING_PROVIDER", os.getenv("ASSISTANT_PROVIDER", "ollama"))
    assistant_embedding_model: str = os.getenv("ASSISTANT_EMBEDDING_MODEL", "nomic-embed-text")
    assistant_embedding_base_url: str = os.getenv(
        "ASSISTANT_EMBEDDING_BASE_URL",
        os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
    )
    assistant_embedding_batch_size: int = int(os.getenv("ASSISTANT_EMBEDDING_BATCH_SIZE", "24"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    )


settings = Settings()
