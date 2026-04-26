from __future__ import annotations

import json
from typing import Any

import psycopg
from fastapi import HTTPException

from ...config import settings
from ...schemas import (
    AssistantCitation,
    AssistantQueryResponse,
    AssistantQueryStep,
    AssistantStatusResponse,
)
from .provider import AssistantProviderError, chat_complete, get_chat_provider, get_embedding_config
from .rag import RagSearchResult, get_rag_index_counts, search_rag_documents_safely
from .structured_tools import StructuredEvidence, collect_structured_evidence


SYSTEM_PROMPT = """
당신은 축구 데이터 시스템의 분석 에이전트입니다.
답변은 한국어로 작성합니다.
정형 DB 근거와 RAG 문서 근거만 사용하고, 근거에 없는 내용은 추측하지 않습니다.
수치가 있으면 날짜, 선수명, 지표명을 함께 언급합니다.
문서 근거와 DB 근거가 서로 다르면 충돌 가능성을 짧게 표시합니다.
답변은 실무자가 바로 읽을 수 있게 간결하게 정리합니다.
""".strip()


def get_assistant_status() -> AssistantStatusResponse:
    pgvector_available, document_count, chunk_count = get_rag_index_counts()
    embedding_provider, embedding_model = get_embedding_config()
    detail = "ready" if pgvector_available else "pgvector extension or database is not available"
    if chunk_count == 0:
        detail = f"{detail}; RAG index is empty"

    return AssistantStatusResponse(
        chat_provider=get_chat_provider(),
        chat_model=settings.assistant_model,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        pgvector_available=pgvector_available,
        indexed_documents=document_count,
        indexed_chunks=chunk_count,
        detail=detail,
    )


def run_assistant_query(question: str) -> AssistantQueryResponse:
    normalized_question = question.strip()
    if not normalized_question:
        raise HTTPException(status_code=400, detail="Question is required.")

    steps: list[AssistantQueryStep] = []
    try:
        structured_evidence = collect_structured_evidence(normalized_question)
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Database is not reachable for assistant queries.") from exc

    for item in structured_evidence:
        steps.append(
            AssistantQueryStep(
                step=len(steps) + 1,
                action="tool",
                tool=item.tool,
                reason=item.reason,
                row_count=len(item.rows),
                preview=item.rows[:5],
            )
        )

    rag_results, rag_error = search_rag_documents_safely(normalized_question)
    steps.append(
        AssistantQueryStep(
            step=len(steps) + 1,
            action="tool",
            tool="search_rag_documents",
            reason="질문과 관련된 문서/노트 chunk를 pgvector 유사도 검색으로 조회합니다.",
            row_count=len(rag_results) if rag_error is None else None,
            preview=[_rag_preview(row) for row in rag_results[:5]],
            error=rag_error,
        )
    )

    try:
        answer = _generate_final_answer(
            question=normalized_question,
            structured_evidence=structured_evidence,
            rag_results=rag_results,
        )
    except AssistantProviderError as exc:
        answer = _build_fallback_answer(
            question=normalized_question,
            structured_evidence=structured_evidence,
            rag_results=rag_results,
            model_error=str(exc),
        )
        steps.append(
            AssistantQueryStep(
                step=len(steps) + 1,
                action="fallback",
                tool="local_answer_formatter",
                reason="LLM provider 호출이 실패해 조회 근거를 기반으로 기본 답변을 생성했습니다.",
                error=str(exc),
            )
        )

    return AssistantQueryResponse(
        question=normalized_question,
        provider=get_chat_provider(),
        model=settings.assistant_model,
        answer=answer,
        steps=steps,
        citations=[
            AssistantCitation(
                title=row.title,
                source_type=row.source_type,
                source_uri=row.source_uri,
                chunk_id=row.chunk_id,
                similarity=row.similarity,
            )
            for row in rag_results
        ],
    )


def _generate_final_answer(
    *,
    question: str,
    structured_evidence: list[StructuredEvidence],
    rag_results: list[RagSearchResult],
) -> str:
    payload = {
        "question": question,
        "structured_evidence": [
            {
                "tool": item.tool,
                "title": item.title,
                "rows": item.rows[:8],
            }
            for item in structured_evidence
        ],
        "rag_evidence": [
            {
                "title": item.title,
                "source_type": item.source_type,
                "source_uri": item.source_uri,
                "similarity": item.similarity,
                "text": item.chunk_text[:1200],
                "metadata": item.metadata,
            }
            for item in rag_results[: settings.assistant_rag_top_k]
        ],
    }
    user_prompt = (
        "아래 JSON 근거만 사용해 사용자의 질문에 답하세요. "
        "마지막에 '근거:' 문장을 짧게 붙여 어떤 DB 도구/문서가 쓰였는지 요약하세요.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}"
    )
    return chat_complete(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )


def _build_fallback_answer(
    *,
    question: str,
    structured_evidence: list[StructuredEvidence],
    rag_results: list[RagSearchResult],
    model_error: str,
) -> str:
    lines = [
        "LLM 응답 생성은 실패했지만, 조회된 근거 기준으로 요약합니다.",
        f"질문: {question}",
    ]
    for item in structured_evidence[:4]:
        if not item.rows:
            continue
        lines.append(f"{item.title}: {_format_rows(item.rows[:3])}")
    if rag_results:
        sources = ", ".join(f"{item.title}({item.source_type})" for item in rag_results[:3])
        lines.append(f"문서 근거: {sources}")
    lines.append(f"모델 오류: {model_error}")
    return "\n".join(lines)


def _format_rows(rows: list[dict[str, object | None]]) -> str:
    formatted_rows = []
    for row in rows:
        parts = []
        for key, value in list(row.items())[:6]:
            if value is not None:
                parts.append(f"{key}={value}")
        formatted_rows.append("(" + ", ".join(parts) + ")")
    return " ".join(formatted_rows)


def _rag_preview(row: RagSearchResult) -> dict[str, object | None]:
    return {
        "title": row.title,
        "source_type": row.source_type,
        "source_uri": row.source_uri,
        "similarity": row.similarity,
        "text": row.chunk_text[:220],
    }
