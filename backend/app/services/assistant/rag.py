from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import psycopg

from ...config import settings
from ...db import get_connection
from .provider import AssistantProviderError, embed_texts, get_embedding_config, vector_literal


@dataclass(frozen=True)
class RagSearchResult:
    chunk_id: str
    title: str
    source_type: str
    source_uri: str
    chunk_text: str
    similarity: float | None
    metadata: dict[str, Any]


def get_rag_index_counts() -> tuple[bool, int, int]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_regtype('vector') IS NOT NULL AS available")
                pgvector_available = bool(cursor.fetchone()["available"])
                cursor.execute("SELECT to_regclass('football.assistant_documents') IS NOT NULL AS exists")
                if not bool(cursor.fetchone()["exists"]):
                    return pgvector_available, 0, 0
                cursor.execute("SELECT COUNT(*) AS count FROM football.assistant_documents")
                document_count = int(cursor.fetchone()["count"])
                cursor.execute("SELECT COUNT(*) AS count FROM football.assistant_chunks")
                chunk_count = int(cursor.fetchone()["count"])
                return pgvector_available, document_count, chunk_count
    except psycopg.Error:
        return False, 0, 0


def search_rag_documents(question: str, *, top_k: int | None = None) -> list[RagSearchResult]:
    embedding_batch = embed_texts([question])
    if not embedding_batch.embeddings:
        return []

    query_embedding = embedding_batch.embeddings[0]
    dimension = len(query_embedding)
    provider, model = get_embedding_config()
    limit = top_k or settings.assistant_rag_top_k

    query = """
        SELECT
            c.chunk_id,
            d.title,
            d.source_type,
            d.source_uri,
            c.chunk_text,
            c.metadata,
            (1 - (c.embedding <=> %s::vector))::double precision AS similarity
        FROM football.assistant_chunks AS c
        JOIN football.assistant_documents AS d
            ON d.document_id = c.document_id
        WHERE c.embedding IS NOT NULL
          AND c.embedding_provider = %s
          AND c.embedding_model = %s
          AND c.embedding_dimension = %s
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
    """

    vector_value = vector_literal(query_embedding)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, [vector_value, provider, model, dimension, vector_value, limit])
            rows = cursor.fetchall()

    return [
        RagSearchResult(
            chunk_id=str(row["chunk_id"]),
            title=str(row["title"]),
            source_type=str(row["source_type"]),
            source_uri=str(row["source_uri"]),
            chunk_text=str(row["chunk_text"]),
            similarity=float(row["similarity"]) if row["similarity"] is not None else None,
            metadata=dict(row["metadata"] or {}),
        )
        for row in rows
    ]


def search_rag_documents_safely(question: str, *, top_k: int | None = None) -> tuple[list[RagSearchResult], str | None]:
    try:
        return search_rag_documents(question, top_k=top_k), None
    except AssistantProviderError as exc:
        return [], str(exc)
    except psycopg.Error as exc:
        return [], str(exc)
