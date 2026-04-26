from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.app.config import settings  # noqa: E402
from backend.app.services.assistant.provider import embed_texts, vector_literal  # noqa: E402
from db.scripts.load_virtual_players_workbook_db import initialize_schema, wait_for_connection  # noqa: E402
from db.scripts.load_virtual_players_workbook_shared import DEFAULT_DATABASE_URL  # noqa: E402


@dataclass(frozen=True)
class SourceDocument:
    source_type: str
    source_uri: str
    title: str
    text: str
    metadata: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index assistant RAG documents into pgvector.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--reset", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--chunk-overlap", type=int, default=160)
    parser.add_argument("--retries", type=int, default=20)
    parser.add_argument("--retry-delay", type=float, default=1.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with wait_for_connection(args.database_url, args.retries, args.retry_delay) as conn:
        with conn.cursor() as cursor:
            initialize_schema(cursor)
            if args.reset:
                cursor.execute("TRUNCATE TABLE football.assistant_documents CASCADE")

            documents = collect_source_documents(conn)
            indexed_chunks = index_documents(
                cursor,
                documents,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
            )

        conn.commit()

    print(f"Indexed documents: {len(documents)}")
    print(f"Indexed chunks: {indexed_chunks}")
    print(f"Embedding provider: {settings.assistant_embedding_provider}")
    print(f"Embedding model: {settings.assistant_embedding_model}")


def collect_source_documents(conn: psycopg.Connection[Any]) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    documents.extend(collect_markdown_documents())
    documents.extend(collect_pdf_documents())
    documents.extend(collect_database_text_documents(conn))
    return [document for document in documents if document.text.strip()]


def collect_markdown_documents() -> list[SourceDocument]:
    paths = [
        ROOT_DIR / "README.md",
        ROOT_DIR / "backend" / "README.md",
        ROOT_DIR / "db" / "README.md",
        ROOT_DIR / "db" / "ERD.md",
        *sorted((ROOT_DIR / "frontend").glob("*.md")),
    ]
    documents = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        documents.append(
            SourceDocument(
                source_type="markdown",
                source_uri=str(path.relative_to(ROOT_DIR)),
                title=path.name,
                text=text,
                metadata={"path": str(path.relative_to(ROOT_DIR))},
            )
        )
    return documents


def collect_pdf_documents() -> list[SourceDocument]:
    pdf_path = ROOT_DIR / "references" / "Bepro11 datas.pdf"
    if not pdf_path.exists():
        return []

    try:
        from pypdf import PdfReader
    except ImportError:
        print("Skipped PDF indexing: install pypdf to extract references/Bepro11 datas.pdf", file=sys.stderr)
        return []

    reader = PdfReader(str(pdf_path))
    page_texts = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            page_texts.append(f"\n\n[page {index}]\n{text}")
    return [
        SourceDocument(
            source_type="pdf",
            source_uri=str(pdf_path.relative_to(ROOT_DIR)),
            title=pdf_path.name,
            text="".join(page_texts),
            metadata={"path": str(pdf_path.relative_to(ROOT_DIR)), "page_count": len(reader.pages)},
        )
    ]


def collect_database_text_documents(conn: psycopg.Connection[Any]) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT i.injury_id, i.player_id, p.name, i.injury_date, i.injury_type, i.injury_part,
                   i.injury_mechanism, i.notes
            FROM football.injuries AS i
            JOIN football.players AS p ON p.player_id = i.player_id
            WHERE COALESCE(i.injury_mechanism, '') <> '' OR COALESCE(i.notes, '') <> ''
            """
        )
        for row in cursor.fetchall():
            text = "\n".join(
                part
                for part in (
                    f"선수: {row['name']}",
                    f"부상일: {row['injury_date']}",
                    f"부상: {row['injury_part']} {row['injury_type']}",
                    f"발생 메커니즘: {row['injury_mechanism']}",
                    f"메모: {row['notes']}",
                )
                if part and not part.endswith("None")
            )
            documents.append(
                SourceDocument(
                    source_type="db_injury",
                    source_uri=f"football.injuries:{row['injury_id']}",
                    title=f"{row['name']} 부상 기록",
                    text=text,
                    metadata={"player_id": row["player_id"], "injury_id": row["injury_id"]},
                )
            )

        cursor.execute(
            """
            SELECT e.evaluation_id, e.player_id, p.name, e.evaluation_date, e.technical,
                   e.tactical, e.physical, e.mental, e.coach_comment
            FROM football.evaluations AS e
            JOIN football.players AS p ON p.player_id = e.player_id
            WHERE COALESCE(e.coach_comment, '') <> ''
            """
        )
        for row in cursor.fetchall():
            text = (
                f"선수: {row['name']}\n평가일: {row['evaluation_date']}\n"
                f"점수: technical {row['technical']}, tactical {row['tactical']}, "
                f"physical {row['physical']}, mental {row['mental']}\n"
                f"코치 코멘트: {row['coach_comment']}"
            )
            documents.append(
                SourceDocument(
                    source_type="db_evaluation",
                    source_uri=f"football.evaluations:{row['evaluation_id']}",
                    title=f"{row['name']} 평가 코멘트",
                    text=text,
                    metadata={"player_id": row["player_id"], "evaluation_id": row["evaluation_id"]},
                )
            )

        cursor.execute(
            """
            SELECT c.counseling_id, c.player_id, p.name, c.counseling_date, c.topic::text AS topic, c.summary
            FROM football.counseling_notes AS c
            JOIN football.players AS p ON p.player_id = c.player_id
            WHERE COALESCE(c.summary, '') <> ''
            """
        )
        for row in cursor.fetchall():
            text = (
                f"선수: {row['name']}\n상담일: {row['counseling_date']}\n"
                f"주제: {row['topic']}\n상담 요약: {row['summary']}"
            )
            documents.append(
                SourceDocument(
                    source_type="db_counseling",
                    source_uri=f"football.counseling_notes:{row['counseling_id']}",
                    title=f"{row['name']} 상담 기록",
                    text=text,
                    metadata={"player_id": row["player_id"], "counseling_id": row["counseling_id"]},
                )
            )

        cursor.execute(
            """
            SELECT t.training_id, t.training_date, t.session_name::text AS session_name,
                   t.training_focus::text AS training_focus, t.training_detail, t.notes
            FROM football.trainings AS t
            WHERE COALESCE(t.training_detail, '') <> '' OR COALESCE(t.notes, '') <> ''
            """
        )
        for row in cursor.fetchall():
            text = "\n".join(
                part
                for part in (
                    f"훈련일: {row['training_date']}",
                    f"세션: {row['session_name']}",
                    f"포커스: {row['training_focus']}",
                    f"상세: {row['training_detail']}",
                    f"메모: {row['notes']}",
                )
                if part and not part.endswith("None")
            )
            documents.append(
                SourceDocument(
                    source_type="db_training",
                    source_uri=f"football.trainings:{row['training_id']}",
                    title=f"{row['training_date']} 훈련 기록",
                    text=text,
                    metadata={"training_id": row["training_id"]},
                )
            )

    return documents


def index_documents(
    cursor: psycopg.Cursor[Any],
    documents: list[SourceDocument],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    total_chunks = 0
    for document in documents:
        document_id = build_id(f"{document.source_type}:{document.source_uri}")
        content_hash = hashlib.sha256(document.text.encode("utf-8")).hexdigest()
        cursor.execute(
            "DELETE FROM football.assistant_documents WHERE source_type = %s AND source_uri = %s",
            [document.source_type, document.source_uri],
        )
        cursor.execute(
            """
            INSERT INTO football.assistant_documents (
                document_id, source_type, source_uri, title, content_hash, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                document_id,
                document.source_type,
                document.source_uri,
                document.title,
                content_hash,
                Jsonb(document.metadata),
            ],
        )

        chunks = chunk_text(document.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for start in range(0, len(chunks), settings.assistant_embedding_batch_size):
            batch = chunks[start : start + settings.assistant_embedding_batch_size]
            embeddings = embed_texts(batch)
            for offset, (chunk, embedding) in enumerate(zip(batch, embeddings.embeddings, strict=True)):
                chunk_index = start + offset
                cursor.execute(
                    """
                    INSERT INTO football.assistant_chunks (
                        chunk_id,
                        document_id,
                        chunk_index,
                        chunk_text,
                        token_estimate,
                        embedding,
                        embedding_provider,
                        embedding_model,
                        embedding_dimension,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s)
                    """,
                    [
                        f"{document_id}:{chunk_index:04d}",
                        document_id,
                        chunk_index,
                        chunk,
                        estimate_tokens(chunk),
                        vector_literal(embedding),
                        embeddings.provider,
                        embeddings.model,
                        len(embedding),
                        Jsonb({"chunk_index": chunk_index, **document.metadata}),
                    ],
                )
                total_chunks += 1
    return total_chunks


def chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    paragraphs = [paragraph.strip() for paragraph in normalized.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if not current:
            current = paragraph
            continue
        if len(current) + len(paragraph) + 2 <= chunk_size:
            current = f"{current}\n\n{paragraph}"
            continue
        chunks.extend(split_long_chunk(current, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
        current = paragraph
    if current:
        chunks.extend(split_long_chunk(current, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
    return chunks


def split_long_chunk(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    step = max(1, chunk_size - chunk_overlap)
    for start in range(0, len(text), step):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def build_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
