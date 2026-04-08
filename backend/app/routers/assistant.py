from __future__ import annotations

from fastapi import APIRouter

from ..schemas import AssistantQueryRequest, AssistantQueryResponse, AssistantStatusResponse
from ..services.assistant import get_assistant_status, run_assistant_query


router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.get("/status", response_model=AssistantStatusResponse)
def get_status() -> AssistantStatusResponse:
    return get_assistant_status()


@router.post("/query", response_model=AssistantQueryResponse)
def query_assistant(payload: AssistantQueryRequest) -> AssistantQueryResponse:
    return run_assistant_query(question=payload.question)
