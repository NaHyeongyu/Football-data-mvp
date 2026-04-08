from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import json
import re
from time import monotonic
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException
import psycopg

from ...config import settings
from ...db import get_connection
from ...schemas import (
    AssistantQueryResponse,
    AssistantQueryStep,
    AssistantStatusResponse,
)
from .answer_formatters import (
    _format_activity_leader_answer,
    _format_combined_workload_summary_answer,
    _format_counseling_summary_answer,
    _format_counseling_topic_summary_answer,
    _format_current_injury_watch_answer,
    _format_evaluation_leaderboard_answer,
    _format_evaluation_summary_answer,
    _format_injury_cause_answer,
    _format_opponent_match_lookup_answer,
    _format_physical_change_answer,
    _format_physical_leaderboard_answer,
    _format_physical_test_leaderboard_answer,
    _format_player_comparison_answer,
    _format_player_profile_summary_answer,
    _format_player_recent_match_summary_answer,
    _format_player_recent_training_summary_answer,
    _format_position_availability_summary_answer,
    _format_position_recent_form_answer,
    _format_pre_injury_workload_answer,
    _format_recent_match_form_answer,
    _format_return_to_play_timeline_answer,
    _format_roster_lookup_answer,
    _format_team_recent_match_summary_answer,
    _format_training_load_answer,
)
from .catalog import merge_schema_hints, select_relevant_schema_context
from .llm_helpers import (
    _build_final_answer_prompt,
    _build_user_prompt,
    _extract_remote_error,
    _parse_agent_payload,
)
from .preview_helpers import (
    _build_fallback_answer_from_preview,
    _build_playbook_answer,
    _normalize_optional_text,
    _should_prefer_preview_fallback,
)
from .sql_helpers import (
    IDENTIFIER_PATTERN,
    QUALIFIED_IDENTIFIER_PATTERN,
    SQL_STRING_PATTERN,
    _extract_as_aliases,
    _extract_cte_names,
    _extract_referenced_objects,
    _format_unknown_column_error,
    _format_unknown_object_error,
    _is_function_call,
    _normalize_sql_error,
)


SYSTEM_PROMPT = """
You are a read-only football data assistant working against a PostgreSQL database.
Your job is to answer the user's question as accurately as possible using SQL queries.

You may perform multiple rounds of SQL lookup before answering.
At each turn, return JSON only with exactly one of these shapes:

{"action":"sql","reason":"why this query is needed","sql":"SELECT ..."}
{"action":"answer","reason":"why enough evidence is available","answer":"final Korean answer"}

Rules:
- Use only read-only SQL.
- Only generate a single SELECT statement or a WITH ... SELECT statement.
- Never write INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, REVOKE, COPY, or CALL.
- Prefer the football schema and the listed views.
- Treat the provided schema catalog as authoritative. Never reference a column unless it is listed for that object.
- Always use AS when defining SQL aliases.
- When a query playbook is provided, follow its preferred objects, exact column names, and example SQL shape closely.
- Avoid unnecessary subqueries or joins when a curated view already contains the needed fields.
- If the question is ambiguous, make the smallest reasonable assumption and state it in the final answer.
- If you still lack evidence, issue another SQL query instead of guessing.
- If a previous SQL step failed, correct the query using the reported error instead of repeating the same mistake.
- Never repeat a SQL query that already succeeded. If an earlier result already answers the question, return `answer`.
- Final answers must be in Korean and cite concrete evidence from the query results.
- Do not answer with only a player name or fragment. Write a complete Korean sentence or two.
- When the user asks about "recent" or "요즘", default to a recent 14- to 28-day window if the data supports it.
- When returning row-oriented data, include LIMIT in the SQL.
""".strip()

FINAL_ANSWER_SYSTEM_PROMPT = """
You are finalizing a football data answer from existing SQL evidence.
You may not ask for more SQL and you may not invent new evidence.

Return JSON only:
{"answer":"final Korean answer"}

Rules:
- Base the answer strictly on the provided SQL previews and step history.
- Cite concrete values from the latest relevant SQL result when possible.
- If the evidence is partial, say so briefly, but still give the best-supported answer.
- Final answer must be in Korean.
- Do not answer with only a name. Write one or two complete Korean sentences.
""".strip()

JOIN_HINTS = """
Useful join hints:
- football.player_match_stats.player_id -> football.players.player_id
- football.player_match_stats.match_id -> football.matches.match_id
- football.match_gps_stats.match_id + player_id -> football.player_match_stats.match_id + player_id
- football.training_gps_stats.training_id + player_id -> football.trainings.training_id + player_id
- football.injuries.player_id -> football.players.player_id
- football.physical_profiles.player_id -> football.players.player_id
- football.evaluations.player_id -> football.players.player_id
- football.counseling_notes.player_id -> football.players.player_id
- football.matches.opponent_team_id -> football.opponent_teams.opponent_team_id
- football.matches.stadium_id -> football.stadiums.stadium_id

Semantic hints:
- "활동량" usually relates to total_distance, sprint_count, accel_count, decel_count, minutes_played, load trends.
- Match data and training data are different sources. Combine them only if the question truly asks for overall workload.
- The views football.player_latest_physical_profile, football.player_current_injury_status, football.player_match_facts are useful shortcuts.
- football.player_match_facts already includes player_name, match_date, opponent, stadium, and GPS workload fields.
- football.matches.match_type uses values such as '공식' and '연습'. If the user asks for an official match, filter match_type = '공식'.
- For injury cause analysis, use football.injuries because injury_mechanism, occurred_during, and notes are stored there.
- When explaining an injury cause, cite the recorded mechanism and notes rather than speculating beyond the stored record.
- football.player_match_stats does not contain match_date. Join football.matches when filtering or ordering by match date.
""".strip()

BLOCKED_SQL_PATTERNS = (
    r"\binsert\b",
    r"\bupdate\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\balter\b",
    r"\bcreate\b",
    r"\btruncate\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\bcopy\b",
    r"\bcall\b",
    r"\bexecute\b",
    r"\bpg_sleep\b",
    r"\bpg_read_file\b",
    r"\bpg_ls_dir\b",
    r"\bdblink\b",
    r"\blo_import\b",
    r"\blo_export\b",
)

SCHEMA_QUERY = """
SELECT
    t.table_name,
    t.table_type,
    c.column_name,
    c.data_type
FROM information_schema.tables AS t
JOIN information_schema.columns AS c
    ON c.table_schema = t.table_schema
   AND c.table_name = t.table_name
WHERE t.table_schema = 'football'
  AND t.table_type IN ('BASE TABLE', 'VIEW')
ORDER BY t.table_name, c.ordinal_position
"""

SCHEMA_CACHE_TTL_SECONDS = 300.0
LOOKUP_CACHE_TTL_SECONDS = 120.0

_schema_catalog_cache: tuple[float, dict[str, dict[str, Any]]] | None = None
_player_lookup_cache: tuple[float, list[tuple[str, str]]] | None = None
_opponent_lookup_cache: tuple[float, list[tuple[str, str]]] | None = None

SQL_RESERVED_TOKENS = {
    "all",
    "and",
    "as",
    "array",
    "asc",
    "avg",
    "between",
    "by",
    "case",
    "cast",
    "coalesce",
    "count",
    "cross",
    "current_date",
    "current_timestamp",
    "date",
    "date_trunc",
    "day",
    "days",
    "desc",
    "distinct",
    "else",
    "end",
    "exists",
    "extract",
    "false",
    "filter",
    "first",
    "from",
    "full",
    "group",
    "having",
    "ilike",
    "in",
    "inner",
    "interval",
    "is",
    "join",
    "last",
    "left",
    "like",
    "limit",
    "lateral",
    "max",
    "min",
    "month",
    "not",
    "null",
    "nulls",
    "offset",
    "on",
    "or",
    "order",
    "outer",
    "over",
    "partition",
    "right",
    "round",
    "rows",
    "select",
    "sum",
    "then",
    "timestamp",
    "true",
    "union",
    "when",
    "where",
    "with",
    "year",
}


class AssistantAgentError(RuntimeError):
    pass


@dataclass(frozen=True)
class AssistantQueryContext:
    question: str
    schema_catalog: dict[str, dict[str, Any]]
    schema_context: dict[str, Any]
    active_playbooks: set[str]


@dataclass(frozen=True)
class DirectPlaybookRoute:
    name: str
    predicate: Callable[[str], bool]
    runner: Callable[[str], AssistantQueryResponse]


def _build_sql_step(
    *,
    step: int,
    reason: str | None,
    sql: str | None,
    rows: Sequence[dict[str, object | None]] | None = None,
    error: str | None = None,
) -> AssistantQueryStep:
    preview = list(rows[: settings.assistant_sql_preview_rows]) if rows is not None else None
    row_count = len(rows) if rows is not None else None
    return AssistantQueryStep(
        step=step,
        action="sql",
        reason=reason,
        sql=sql,
        row_count=row_count,
        preview=preview,
        error=error,
    )


def _build_answer_step(*, step: int, reason: str | None) -> AssistantQueryStep:
    return AssistantQueryStep(
        step=step,
        action="answer",
        reason=reason,
    )


def _build_assistant_query_response(
    *,
    question: str,
    answer: str,
    steps: Sequence[AssistantQueryStep],
) -> AssistantQueryResponse:
    return AssistantQueryResponse(
        question=question,
        provider="ollama",
        model=settings.llama_model,
        answer=answer,
        steps=list(steps),
    )


def _build_answer_only_response(
    *,
    question: str,
    answer: str,
    reason: str,
) -> AssistantQueryResponse:
    return _build_assistant_query_response(
        question=question,
        answer=answer,
        steps=[_build_answer_step(step=1, reason=reason)],
    )


def _complete_answer_response(
    *,
    question: str,
    answer: str,
    steps: list[AssistantQueryStep],
    step: int,
    reason: str,
) -> AssistantQueryResponse:
    steps.append(_build_answer_step(step=step, reason=reason))
    return _build_assistant_query_response(question=question, answer=answer, steps=steps)


def _build_direct_playbook_response(
    *,
    question: str,
    sql_query: str,
    sql_reason: str,
    rows: Sequence[dict[str, object | None]],
    answer: str,
    answer_reason: str,
    empty_answer: str | None = None,
    empty_reason: str | None = None,
) -> AssistantQueryResponse:
    steps = [
        _build_sql_step(
            step=1,
            reason=sql_reason,
            sql=sql_query,
            rows=rows,
        )
    ]
    if not rows and empty_answer is not None:
        steps.append(
            _build_answer_step(
                step=2,
                reason=empty_reason or "No rows were returned for the direct playbook query.",
            )
        )
        return _build_assistant_query_response(
            question=question,
            answer=empty_answer,
            steps=steps,
        )

    return _complete_answer_response(
        question=question,
        answer=answer,
        steps=steps,
        step=2,
        reason=answer_reason,
    )


def get_assistant_status() -> AssistantStatusResponse:
    try:
        payload = _ollama_request("/api/tags")
    except AssistantAgentError as exc:
        return AssistantStatusResponse(
            provider="ollama",
            base_url=settings.llama_base_url,
            model=settings.llama_model,
            reachable=False,
            model_available=False,
            available_models=[],
            detail=str(exc),
        )

    model_names = [str(item.get("name", "")).strip() for item in payload.get("models", []) if item.get("name")]
    model_available = settings.llama_model in model_names
    detail = (
        f"Ollama is reachable and model '{settings.llama_model}' is available."
        if model_available
        else f"Ollama is reachable, but model '{settings.llama_model}' is not pulled yet."
    )
    return AssistantStatusResponse(
        provider="ollama",
        base_url=settings.llama_base_url,
        model=settings.llama_model,
        reachable=True,
        model_available=model_available,
        available_models=model_names,
        detail=detail,
    )


def _load_assistant_query_context(question: str) -> AssistantQueryContext:
    normalized_question = question.strip()
    if not normalized_question:
        raise HTTPException(status_code=400, detail="Question is required.")

    try:
        schema_catalog = _fetch_schema_catalog()
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Database is not reachable for assistant queries.",
        ) from exc

    schema_context = select_relevant_schema_context(normalized_question, schema_catalog)
    active_playbooks = {playbook["name"] for playbook in schema_context.get("query_playbooks", [])}
    return AssistantQueryContext(
        question=normalized_question,
        schema_catalog=schema_catalog,
        schema_context=schema_context,
        active_playbooks=active_playbooks,
    )


def _request_assistant_action(
    *,
    context: AssistantQueryContext,
    previous_steps: Sequence[AssistantQueryStep],
) -> dict[str, Any]:
    try:
        assistant_response = _chat_with_llama(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(
                question=context.question,
                schema_context=context.schema_context,
                previous_steps=previous_steps,
                join_hints=JOIN_HINTS,
            ),
        )
    except AssistantAgentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _parse_agent_payload(assistant_response)


def _handle_answer_action(
    *,
    context: AssistantQueryContext,
    step_number: int,
    action_payload: dict[str, Any],
    reason: str | None,
    steps: list[AssistantQueryStep],
) -> AssistantQueryResponse:
    answer = _normalize_optional_text(action_payload.get("answer"))
    if not answer:
        raise HTTPException(status_code=502, detail="Assistant returned an empty answer.")
    return _complete_answer_response(
        question=context.question,
        answer=answer,
        steps=steps,
        step=step_number,
        reason=reason or "Returned an answer action from the assistant.",
    )


def _handle_sql_action(
    *,
    context: AssistantQueryContext,
    step_number: int,
    action_payload: dict[str, Any],
    reason: str | None,
    steps: list[AssistantQueryStep],
) -> AssistantQueryResponse | None:
    raw_sql = _normalize_optional_text(action_payload.get("sql"))
    try:
        sql_query = _validate_read_only_sql(str(action_payload.get("sql", "")))
    except HTTPException as exc:
        steps.append(
            _build_sql_step(
                step=step_number,
                reason=reason,
                sql=raw_sql,
                error=_normalize_optional_text(exc.detail),
            )
        )
        return None

    if _has_successful_sql_step(steps, sql_query):
        forced_answer = _force_answer_from_evidence(
            question=context.question,
            previous_steps=steps,
        )
        if forced_answer:
            return _complete_answer_response(
                question=context.question,
                answer=forced_answer,
                steps=steps,
                step=step_number,
                reason="Used existing SQL evidence because the model attempted to repeat a successful query.",
            )

        steps.append(
            _build_sql_step(
                step=step_number,
                reason=reason,
                sql=sql_query,
                error="This SQL was already executed successfully. Use the existing evidence and answer the user instead of repeating it.",
            )
        )
        return None

    schema_error = _validate_sql_against_catalog(sql_query, context.schema_catalog)
    if schema_error:
        steps.append(
            _build_sql_step(
                step=step_number,
                reason=reason,
                sql=sql_query,
                error=schema_error,
            )
        )
        return None

    playbook_error = _validate_sql_against_playbooks(sql_query, context.active_playbooks)
    if playbook_error:
        steps.append(
            _build_sql_step(
                step=step_number,
                reason=reason,
                sql=sql_query,
                error=playbook_error,
            )
        )
        return None

    try:
        rows = _execute_read_only_sql(sql_query)
    except psycopg.Error as exc:
        steps.append(
            _build_sql_step(
                step=step_number,
                reason=reason,
                sql=sql_query,
                error=_normalize_sql_error(exc, sql_query=sql_query),
            )
        )
        return None

    steps.append(
        _build_sql_step(
            step=step_number,
            reason=reason,
            sql=sql_query,
            rows=rows,
        )
    )
    preview = rows[: settings.assistant_sql_preview_rows]

    playbook_answer = _build_playbook_answer(
        question=context.question,
        active_playbooks=context.active_playbooks,
        sql_query=sql_query,
        row_count=len(rows),
        preview=preview,
    )
    if playbook_answer:
        return _complete_answer_response(
            question=context.question,
            answer=playbook_answer,
            steps=steps,
            step=step_number + 1,
            reason="Returned a deterministic playbook answer from the first sufficient SQL result.",
        )

    fast_answer = _force_answer_from_evidence(
        question=context.question,
        previous_steps=steps,
    )
    if fast_answer:
        return _complete_answer_response(
            question=context.question,
            answer=fast_answer,
            steps=steps,
            step=step_number + 1,
            reason="Finalized the response immediately from the current SQL evidence.",
        )
    return None


def _handle_assistant_action(
    *,
    context: AssistantQueryContext,
    step_number: int,
    action_payload: dict[str, Any],
    steps: list[AssistantQueryStep],
) -> AssistantQueryResponse | None:
    action = str(action_payload.get("action", "")).strip().lower()
    reason = _normalize_optional_text(action_payload.get("reason"))

    if action == "sql":
        return _handle_sql_action(
            context=context,
            step_number=step_number,
            action_payload=action_payload,
            reason=reason,
            steps=steps,
        )
    if action == "answer":
        return _handle_answer_action(
            context=context,
            step_number=step_number,
            action_payload=action_payload,
            reason=reason,
            steps=steps,
        )

    raise HTTPException(
        status_code=502,
        detail="Assistant returned an unsupported action. Expected 'sql' or 'answer'.",
    )


def run_assistant_query(question: str) -> AssistantQueryResponse:
    context = _load_assistant_query_context(question)

    try:
        direct_playbook_response = _run_direct_playbook_if_supported(
            question=context.question,
            active_playbooks=context.active_playbooks,
        )
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Database is not reachable for assistant queries.",
        ) from exc
    if direct_playbook_response is not None:
        return direct_playbook_response

    steps: list[AssistantQueryStep] = []

    for step_number in range(1, settings.assistant_max_steps + 1):
        action_payload = _request_assistant_action(
            context=context,
            previous_steps=steps,
        )
        response = _handle_assistant_action(
            context=context,
            step_number=step_number,
            action_payload=action_payload,
            steps=steps,
        )
        if response is not None:
            return response

    forced_answer = _force_answer_from_evidence(
        question=context.question,
        previous_steps=steps,
    )
    if forced_answer:
        return _complete_answer_response(
            question=context.question,
            answer=forced_answer,
            steps=steps,
            step=settings.assistant_max_steps + 1,
            reason="Reached the step limit, so the system finalized an answer from the existing SQL evidence.",
        )

    raise HTTPException(
        status_code=504,
        detail=f"Assistant reached the maximum of {settings.assistant_max_steps} steps without finishing.",
    )


def _fetch_schema_catalog() -> dict[str, dict[str, Any]]:
    global _schema_catalog_cache

    now = monotonic()
    if _schema_catalog_cache is not None:
        cached_at, cached_catalog = _schema_catalog_cache
        if now - cached_at <= SCHEMA_CACHE_TTL_SECONDS:
            return cached_catalog

    grouped: dict[str, dict[str, Any]] = {}
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_QUERY)
            for row in cursor.fetchall():
                object_name = f'football.{row["table_name"]}'
                group = grouped.setdefault(
                    object_name,
                    {"table_type": str(row["table_type"]), "columns": []},
                )
                group["columns"].append(
                    {
                        "name": str(row["column_name"]).lower(),
                        "data_type": str(row["data_type"]),
                    }
                )

    catalog: dict[str, dict[str, Any]] = {}
    for object_name, details in grouped.items():
        column_names = [column["name"] for column in details["columns"]]
        catalog[object_name] = {
            "object_name": object_name,
            "columns": details["columns"],
            "column_names": column_names,
            "column_names_lower": set(column_names),
            **merge_schema_hints(
                object_name,
                table_type=details["table_type"],
                column_names=column_names,
            ),
        }

    _schema_catalog_cache = (now, catalog)
    return catalog


def _fetch_player_lookup_index() -> list[tuple[str, str]]:
    global _player_lookup_cache

    now = monotonic()
    if _player_lookup_cache is not None:
        cached_at, cached_rows = _player_lookup_cache
        if now - cached_at <= LOOKUP_CACHE_TTL_SECONDS:
            return cached_rows

    sql_query = (
        "SELECT player_id, name "
        "FROM football.players "
        "ORDER BY length(name) DESC, name ASC"
    )
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            rows = [
                (str(row["player_id"]), str(row["name"]))
                for row in cursor.fetchall()
                if row.get("player_id") and row.get("name")
            ]

    _player_lookup_cache = (now, rows)
    return rows


def _fetch_opponent_lookup_index() -> list[tuple[str, str]]:
    global _opponent_lookup_cache

    now = monotonic()
    if _opponent_lookup_cache is not None:
        cached_at, cached_rows = _opponent_lookup_cache
        if now - cached_at <= LOOKUP_CACHE_TTL_SECONDS:
            return cached_rows

    sql_query = (
        "SELECT opponent_team_id, opponent_team_name "
        "FROM football.opponent_teams "
        "ORDER BY length(opponent_team_name) DESC, opponent_team_name ASC"
    )
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            rows = [
                (str(row["opponent_team_id"]), str(row["opponent_team_name"]))
                for row in cursor.fetchall()
                if row.get("opponent_team_id") and row.get("opponent_team_name")
            ]

    _opponent_lookup_cache = (now, rows)
    return rows
def _direct_playbook_routes() -> tuple[DirectPlaybookRoute, ...]:
    return (
        DirectPlaybookRoute("pre_injury_workload_analysis", _should_run_pre_injury_workload_direct, lambda question: _run_pre_injury_workload_analysis_playbook(question=question)),
        DirectPlaybookRoute("injury_cause_analysis", _should_run_injury_cause_analysis_direct, lambda question: _run_injury_cause_analysis_playbook(question=question)),
        DirectPlaybookRoute("position_availability_summary", _should_run_position_availability_summary_direct, lambda question: _run_position_availability_summary_playbook(question=question)),
        DirectPlaybookRoute("current_injury_watch", _should_run_current_injury_watch_direct, lambda question: _run_current_injury_watch_playbook(question=question)),
        DirectPlaybookRoute("counseling_summary", _should_run_counseling_summary_direct, lambda question: _run_counseling_summary_playbook(question=question)),
        DirectPlaybookRoute("evaluation_summary", _should_run_evaluation_summary_direct, lambda question: _run_evaluation_summary_playbook(question=question)),
        DirectPlaybookRoute("physical_change_analysis", _should_run_physical_change_analysis_direct, lambda question: _run_physical_change_analysis_playbook(question=question)),
        DirectPlaybookRoute("player_profile_summary", _should_run_player_profile_summary_direct, lambda question: _run_player_profile_summary_playbook(question=question)),
        DirectPlaybookRoute("player_comparison", _should_run_player_comparison_direct, lambda question: _run_player_comparison_playbook(question=question)),
        DirectPlaybookRoute("player_recent_match_summary", _should_run_player_recent_match_summary_direct, lambda question: _run_player_recent_match_summary_playbook(question=question)),
        DirectPlaybookRoute("player_recent_training_summary", _should_run_player_recent_training_summary_direct, lambda question: _run_player_recent_training_summary_playbook(question=question)),
        DirectPlaybookRoute("return_to_play_timeline", _should_run_return_to_play_timeline_direct, lambda question: _run_return_to_play_timeline_playbook(question=question)),
        DirectPlaybookRoute("opponent_match_lookup", _should_run_opponent_match_lookup_direct, lambda question: _run_opponent_match_lookup_playbook(question=question)),
        DirectPlaybookRoute("team_recent_match_summary", _should_run_team_recent_match_summary_direct, lambda question: _run_team_recent_match_summary_playbook(question=question)),
        DirectPlaybookRoute("position_recent_form", _should_run_position_recent_form_direct, lambda question: _run_position_recent_form_playbook(question=question)),
        DirectPlaybookRoute("physical_test_leaderboard", _should_run_physical_test_leaderboard_direct, lambda question: _run_physical_test_leaderboard_playbook(question=question)),
        DirectPlaybookRoute("physical_leaderboard", _should_run_physical_leaderboard_direct, lambda question: _run_physical_leaderboard_playbook(question=question)),
        DirectPlaybookRoute("evaluation_leaderboard", _should_run_evaluation_leaderboard_direct, lambda question: _run_evaluation_leaderboard_playbook(question=question)),
        DirectPlaybookRoute("counseling_topic_summary", _should_run_counseling_topic_summary_direct, lambda question: _run_counseling_topic_summary_playbook(question=question)),
        DirectPlaybookRoute("roster_lookup", _should_run_roster_lookup_direct, lambda question: _run_roster_lookup_playbook(question=question)),
        DirectPlaybookRoute(
            "latest_official_match_activity_leader",
            _should_run_latest_official_match_activity_direct,
            lambda question: _run_activity_leader_playbook(
                question=question,
                match_label="가장 최근 공식 경기",
                match_filter_sql="WHERE match_type = '공식'",
                cte_name="latest_official_match",
                reason="Answered directly from the official-match activity-leader playbook.",
            ),
        ),
        DirectPlaybookRoute("combined_workload_summary", _should_run_combined_workload_summary_direct, lambda question: _run_combined_workload_summary_playbook(question=question)),
        DirectPlaybookRoute("training_load", _should_run_training_load_direct, lambda question: _run_training_load_playbook(question=question)),
        DirectPlaybookRoute("recent_match_form", _should_run_recent_match_form_direct, lambda question: _run_recent_match_form_playbook(question=question)),
        DirectPlaybookRoute(
            "latest_match_activity_leader",
            _should_run_latest_match_activity_direct,
            lambda question: _run_activity_leader_playbook(
                question=question,
                match_label="가장 최근 경기",
                match_filter_sql="",
                cte_name="latest_match",
                reason="Answered directly from the latest-match activity-leader playbook.",
            ),
        ),
    )


def _run_direct_playbook_if_supported(
    *,
    question: str,
    active_playbooks: set[str],
) -> AssistantQueryResponse | None:
    routes = _direct_playbook_routes()
    for route in routes:
        if route.name not in active_playbooks:
            continue
        if route.predicate(question):
            return route.runner(question)

    fallback_routes = [
        route
        for route in routes
        if route.name not in active_playbooks and route.predicate(question)
    ]
    if len(fallback_routes) == 1:
        return fallback_routes[0].runner(question)
    return None


def _run_pre_injury_workload_analysis_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)

    if resolved_player is not None:
        player_id, _player_name = resolved_player
        target_injuries_sql = (
            "SELECT p.player_id, p.name, i.injury_date, i.injury_type, i.injury_part "
            "FROM football.injuries AS i "
            "JOIN football.players AS p ON p.player_id = i.player_id "
            f"WHERE p.player_id = '{player_id}' "
            "ORDER BY i.injury_date DESC, i.created_at DESC "
            "LIMIT 1"
        )
        reason = "Answered directly from the pre-injury-workload playbook for the resolved player."
    else:
        target_injuries_sql = (
            "SELECT player_id, name, injury_date, injury_type, injury_part "
            "FROM football.player_current_injury_status "
            "WHERE injury_id IS NOT NULL "
            "AND actual_return_date IS NULL "
            "ORDER BY injury_date DESC, name ASC"
        )
        reason = "Answered directly from the pre-injury-workload playbook for currently injured or rehab players."

    sql_query = (
        "WITH target_injuries AS ("
        f" {target_injuries_sql}"
        "), training_window AS ("
        " SELECT"
        "   ti.player_id,"
        "   COUNT(*) FILTER (WHERE t.training_date >= ti.injury_date - INTERVAL '7 days' AND t.training_date < ti.injury_date) AS pre7_training_sessions,"
        "   AVG(tgs.total_distance) FILTER (WHERE t.training_date >= ti.injury_date - INTERVAL '7 days' AND t.training_date < ti.injury_date) AS pre7_training_avg_distance,"
        "   AVG(tgs.sprint_count) FILTER (WHERE t.training_date >= ti.injury_date - INTERVAL '7 days' AND t.training_date < ti.injury_date) AS pre7_training_avg_sprints,"
        "   AVG(tgs.total_distance) FILTER (WHERE t.training_date >= ti.injury_date - INTERVAL '35 days' AND t.training_date < ti.injury_date - INTERVAL '7 days') AS base_training_avg_distance,"
        "   AVG(tgs.sprint_count) FILTER (WHERE t.training_date >= ti.injury_date - INTERVAL '35 days' AND t.training_date < ti.injury_date - INTERVAL '7 days') AS base_training_avg_sprints,"
        "   COUNT(*) FILTER (WHERE t.training_date >= ti.injury_date - INTERVAL '7 days' AND t.training_date < ti.injury_date AND t.intensity_level::text = 'high') AS pre7_high_training_sessions"
        " FROM target_injuries AS ti"
        " LEFT JOIN football.training_gps_stats AS tgs ON tgs.player_id = ti.player_id"
        " LEFT JOIN football.trainings AS t ON t.training_id = tgs.training_id"
        " GROUP BY ti.player_id"
        "), match_window AS ("
        " SELECT"
        "   ti.player_id,"
        "   COUNT(*) FILTER (WHERE pmf.match_date >= ti.injury_date - INTERVAL '7 days' AND pmf.match_date < ti.injury_date) AS pre7_match_events,"
        "   AVG(pmf.total_distance) FILTER (WHERE pmf.match_date >= ti.injury_date - INTERVAL '7 days' AND pmf.match_date < ti.injury_date) AS pre7_match_avg_distance,"
        "   AVG(pmf.sprint_count) FILTER (WHERE pmf.match_date >= ti.injury_date - INTERVAL '7 days' AND pmf.match_date < ti.injury_date) AS pre7_match_avg_sprints,"
        "   AVG(pmf.total_distance) FILTER (WHERE pmf.match_date >= ti.injury_date - INTERVAL '35 days' AND pmf.match_date < ti.injury_date - INTERVAL '7 days') AS base_match_avg_distance,"
        "   AVG(pmf.sprint_count) FILTER (WHERE pmf.match_date >= ti.injury_date - INTERVAL '35 days' AND pmf.match_date < ti.injury_date - INTERVAL '7 days') AS base_match_avg_sprints"
        " FROM target_injuries AS ti"
        " LEFT JOIN football.player_match_facts AS pmf ON pmf.player_id = ti.player_id"
        " GROUP BY ti.player_id"
        ") "
        "SELECT"
        " ti.player_id, ti.name, ti.injury_date, ti.injury_type, ti.injury_part,"
        " tw.pre7_training_sessions, tw.pre7_training_avg_distance, tw.pre7_training_avg_sprints,"
        " tw.base_training_avg_distance, tw.base_training_avg_sprints, tw.pre7_high_training_sessions,"
        " mw.pre7_match_events, mw.pre7_match_avg_distance, mw.pre7_match_avg_sprints,"
        " mw.base_match_avg_distance, mw.base_match_avg_sprints"
        " FROM target_injuries AS ti"
        " LEFT JOIN training_window AS tw ON tw.player_id = ti.player_id"
        " LEFT JOIN match_window AS mw ON mw.player_id = ti.player_id"
        " ORDER BY ti.injury_date DESC, ti.name ASC"
    )

    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason=reason,
        rows=rows,
        answer=_format_pre_injury_workload_answer(rows),
        answer_reason="Returned a deterministic answer from the direct pre-injury-workload playbook query.",
    )


def _run_current_injury_watch_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    sql_query = (
        "SELECT name, injury_type, injury_part, injury_status, injury_date, expected_return_date "
        "FROM football.player_current_injury_status "
        "WHERE injury_id IS NOT NULL "
        "AND actual_return_date IS NULL "
        "ORDER BY injury_date DESC, expected_return_date ASC NULLS LAST "
        "LIMIT 20"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the current-injury-watch playbook.",
        rows=rows,
        answer=_format_current_injury_watch_answer(rows),
        answer_reason="Returned a deterministic answer from the direct current-injury-watch playbook query.",
    )


def _run_position_availability_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    position_filter = _resolve_position_filter(question)

    if position_filter is not None:
        position_condition = _build_position_sql_condition(position_filter).replace(
            "primary_position",
            "p.primary_position",
        ).replace("secondary_position", "p.secondary_position")
        sql_query = (
            "SELECT p.name, p.primary_position, p.secondary_position, "
            "CASE WHEN pcis.injury_id IS NOT NULL AND pcis.actual_return_date IS NULL THEN TRUE ELSE FALSE END AS unavailable_flag, "
            "pcis.injury_status, pcis.injury_type, pcis.injury_part, pcis.expected_return_date "
            "FROM football.players AS p "
            "LEFT JOIN football.player_current_injury_status AS pcis ON pcis.player_id = p.player_id "
            f"WHERE {position_condition} "
            "ORDER BY unavailable_flag DESC, pcis.expected_return_date ASC NULLS LAST, p.jersey_number ASC NULLS LAST, p.name ASC "
            "LIMIT 20"
        )
        reason = "Answered directly from the position-availability playbook for the requested position group."
    else:
        sql_query = (
            "SELECT p.primary_position AS position, COUNT(*) AS roster_count, "
            "COUNT(*) FILTER (WHERE pcis.injury_id IS NOT NULL AND pcis.actual_return_date IS NULL) AS unavailable_count, "
            "COUNT(*) FILTER (WHERE pcis.injury_status::text = 'rehab' AND pcis.actual_return_date IS NULL) AS rehab_count, "
            "COUNT(*) FILTER (WHERE pcis.injury_id IS NULL OR pcis.actual_return_date IS NOT NULL) AS available_count, "
            "MIN(pcis.expected_return_date) FILTER (WHERE pcis.injury_id IS NOT NULL AND pcis.actual_return_date IS NULL) AS nearest_return_date "
            "FROM football.players AS p "
            "LEFT JOIN football.player_current_injury_status AS pcis ON pcis.player_id = p.player_id "
            "GROUP BY p.primary_position "
            "ORDER BY unavailable_count DESC, rehab_count DESC, roster_count ASC, p.primary_position ASC"
        )
        reason = "Answered directly from the position-availability playbook by grouping current roster availability by position."

    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason=reason,
        rows=rows,
        answer=_format_position_availability_summary_answer(
            rows=rows,
            position_filter=position_filter,
        ),
        answer_reason="Returned a deterministic answer from the direct position-availability playbook query.",
    )


def _should_run_injury_cause_analysis_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    cause_terms = ("부상원인", "원인분석", "원인", "왜다쳤", "왜", "메커니즘")
    return _contains_any(normalized, cause_terms)


def _should_run_pre_injury_workload_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    injury_terms = ("부상", "다쳤", "injury")
    before_terms = ("이전", "직전", "전", "before")
    load_terms = ("강도", "훈련량", "부하", "워크로드", "load", "intensity", "지나치", "높", "경기", "훈련")

    has_injury_term = _contains_any(normalized, injury_terms)
    has_before_term = _contains_any(normalized, before_terms)
    has_load_term = _contains_any(normalized, load_terms)
    return has_injury_term and has_before_term and has_load_term


def _should_run_current_injury_watch_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    injury_terms = ("부상", "재활", "복귀", "injury", "rehab", "결장", "출전불가", "가용")
    roster_terms = ("지금", "현재", "다음경기", "부상상태", "재활중", "이름", "명단", "누구", "누가", "선수", "목록", "출전어려운")
    analysis_terms = (
        "원인",
        "분석",
        "강도",
        "훈련량",
        "부하",
        "활동량",
        "이전",
        "경기",
        "훈련",
        "메커니즘",
        "왜",
        "risk",
        "load",
    )

    has_injury_term = _contains_any(normalized, injury_terms)
    has_roster_term = _contains_any(normalized, roster_terms)
    has_analysis_term = _contains_any(normalized, analysis_terms)
    return has_injury_term and has_roster_term and not has_analysis_term


def _should_run_position_availability_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    availability_terms = (
        "가용",
        "가용인원",
        "출전가능",
        "출전가능해",
        "결장",
        "라인업",
        "부족",
        "공백",
        "못나와",
        "불가",
        "available",
        "availability",
        "몇명",
    )
    injury_terms = ("부상", "재활", "복귀")
    blocked_terms = ("폼", "활동량", "훈련", "load", "경기력", "비교")
    has_position_term = _resolve_position_filter(question) is not None or "포지션별" in normalized
    return (
        has_position_term
        and (_contains_any(normalized, availability_terms) or _contains_any(normalized, injury_terms))
        and not _contains_any(normalized, blocked_terms)
    )


def _should_run_latest_official_match_activity_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    official_terms = ("공식경기", "공식전", "officialmatch")
    activity_terms = ("활동량", "많이뛴", "distance", "스프린트", "workload", "gps", "load", "이동거리")
    training_terms = ("훈련", "training")
    return _contains_any(normalized, official_terms) and _contains_any(normalized, activity_terms) and not _contains_any(
        normalized,
        training_terms,
    )


def _should_run_latest_match_activity_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    latest_terms = ("가장최근", "직전", "마지막", "latest", "최근경기", "최근매치")
    match_terms = ("경기", "match", "매치")
    activity_terms = ("활동량", "많이뛴", "distance", "스프린트", "workload", "gps", "load", "이동거리")
    blocked_terms = ("공식", "훈련", "training", "폼", "요즘", "평균", "21일", "14일", "3주")
    return (
        _contains_any(normalized, latest_terms)
        and _contains_any(normalized, match_terms)
        and _contains_any(normalized, activity_terms)
        and not _contains_any(normalized, blocked_terms)
    )


def _should_run_training_load_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    training_terms = ("훈련", "training", "세션", "session", "gps", "highintensity")
    injury_terms = ("부상", "injury", "다쳤")
    before_terms = ("이전", "직전", "before")
    return _contains_any(normalized, training_terms) and not (
        _contains_any(normalized, injury_terms) and _contains_any(normalized, before_terms)
    )


def _should_run_combined_workload_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    training_terms = ("훈련", "training", "세션")
    match_terms = ("경기", "match", "매치")
    combined_terms = ("합쳐", "합산", "통합", "전체", "combined", "overall", "acwr", "acutechronic")
    load_terms = ("부하", "load", "workload", "활동량", "스파이크", "spike", "과부하", "급격", "리스크", "힘들", "많이뛴")
    injury_terms = ("부상", "injury", "다쳤")
    before_terms = ("이전", "직전", "before")
    return (
        (_contains_any(normalized, combined_terms) or (_contains_any(normalized, training_terms) and _contains_any(normalized, match_terms)))
        and _contains_any(normalized, load_terms)
        and not (_contains_any(normalized, injury_terms) and _contains_any(normalized, before_terms))
    )


def _should_run_recent_match_form_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    form_terms = ("폼", "요즘", "평균", "꾸준", "최근몇경기", "최근3주", "최근21일", "최근14일", "recentform")
    trend_terms = ("올라", "상승", "떨어", "하락", "부진")
    match_terms = ("경기", "match", "매치", "workload", "distance", "스프린트", "이동거리")
    blocked_terms = ("훈련", "training", "부상", "injury", "공식경기", "공식전")
    has_form_term = _contains_any(normalized, form_terms)
    has_trend_term = _contains_any(normalized, trend_terms)
    return (
        (has_form_term or has_trend_term)
        and (has_form_term or _contains_any(normalized, match_terms))
        and not _contains_any(normalized, blocked_terms)
    )


def _should_run_player_profile_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    profile_terms = ("프로필", "선수정보", "기본정보", "등번호", "포지션", "국적", "주발", "profile", "신상")
    blocked_terms = ("평가", "evaluation", "상담", "counseling", "멘탈", "피지컬", "체성분", "체중", "근육량")
    return _contains_any(normalized, profile_terms) and not _contains_any(normalized, blocked_terms)


def _should_run_physical_change_analysis_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    physical_terms = (
        "피지컬",
        "체성분",
        "체중",
        "체지방",
        "근육량",
        "bmi",
        "physical",
        "체력테스트",
        "스프린트테스트",
        "점프",
        "민첩",
    )
    blocked_terms = ("훈련량", "부하", "상담", "평가")
    return _contains_any(normalized, physical_terms) and not _contains_any(normalized, blocked_terms)


def _should_run_evaluation_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    evaluation_terms = ("평가", "평가점수", "코치평가", "coachcomment", "evaluation", "technical", "tactical", "mental점수")
    blocked_terms = ("상담", "counseling", "상담노트")
    return _contains_any(normalized, evaluation_terms) and not _contains_any(normalized, blocked_terms)


def _should_run_counseling_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    counseling_terms = ("상담", "상담노트", "상담기록", "counseling", "멘탈관리", "멘탈상담", "코칭메모")
    blocked_terms = ("훈련량", "평가점수")
    return _contains_any(normalized, counseling_terms) and not _contains_any(normalized, blocked_terms)


def _should_run_player_recent_match_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    match_terms = ("최근경기", "직전경기", "마지막경기", "지난경기", "공식경기", "공식전")
    summary_terms = ("요약", "정리", "기록", "스탯", "stats", "어땠", "어때")
    blocked_terms = ("활동량1위", "활동량", "누구", "top", "leader", "폼", "ranking")
    return _contains_any(normalized, match_terms) and _contains_any(normalized, summary_terms) and not _contains_any(
        normalized,
        blocked_terms,
    )


def _should_run_player_recent_training_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    training_terms = ("최근훈련", "직전훈련", "마지막훈련", "training", "세션")
    summary_terms = ("요약", "정리", "기록", "스탯", "stats", "어땠", "어때")
    blocked_terms = ("훈련량많", "top", "leader", "ranking", "과부하", "급격")
    return _contains_any(normalized, training_terms) and _contains_any(normalized, summary_terms) and not _contains_any(
        normalized,
        blocked_terms,
    )


def _should_run_return_to_play_timeline_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    return_terms = ("복귀예정", "복귀일", "언제복귀", "언제돌아", "returntimeline", "expectedreturn", "복귀")
    blocked_terms = ("원인", "분석", "부하", "활동량")
    return _contains_any(normalized, return_terms) and not _contains_any(normalized, blocked_terms)


def _should_run_physical_leaderboard_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    metric_terms = ("체중", "체지방", "근육량", "bmi")
    ranking_terms = ("가장", "top", "순위", "ranking", "많", "높", "낮", "적")
    blocked_terms = ("변화", "추이", "프로필", "선수정보", "체력테스트", "10m", "30m", "점프")
    return _contains_any(normalized, metric_terms) and _contains_any(normalized, ranking_terms) and not _contains_any(
        normalized,
        blocked_terms,
    )


def _should_run_physical_test_leaderboard_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    metric_terms = ("10m", "30m", "점프", "민첩", "agility", "ttest", "셔틀런", "스프린트테스트", "체력테스트")
    ranking_terms = ("가장", "top", "순위", "ranking", "빠른", "느린", "높은", "낮은", "좋은")
    blocked_terms = ("변화", "추이")
    return _contains_any(normalized, metric_terms) and _contains_any(normalized, ranking_terms) and not _contains_any(
        normalized,
        blocked_terms,
    )


def _should_run_evaluation_leaderboard_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    evaluation_terms = ("평가", "evaluation", "technical", "tactical", "physical", "mental", "코치평가")
    ranking_terms = ("가장", "top", "순위", "ranking", "높은", "낮은", "좋은", "나쁜")
    blocked_terms = ("요약", "코멘트", "comment", "선수정보")
    return _contains_any(normalized, evaluation_terms) and _contains_any(normalized, ranking_terms) and not _contains_any(
        normalized,
        blocked_terms,
    )


def _should_run_counseling_topic_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    counseling_terms = ("상담", "counseling", "멘탈", "코칭메모", "상담노트")
    topic_terms = ("주제", "topic", "이슈", "흐름", "많아", "ranking", "순위", "팀전체")
    return _contains_any(normalized, counseling_terms) and _contains_any(normalized, topic_terms)


def _should_run_team_recent_match_summary_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    team_terms = ("팀", "우리팀", "경기력", "퍼포먼스")
    match_terms = ("최근경기", "마지막경기", "공식전", "경기결과", "팀요약", "matchsummary")
    blocked_terms = ("선수", "비교", "상대팀", "상대로")
    return (_contains_any(normalized, team_terms) or _contains_any(normalized, match_terms)) and _contains_any(
        normalized,
        ("경기", "결과", "요약", "공식전"),
    ) and not _contains_any(normalized, blocked_terms)


def _should_run_position_recent_form_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    position_terms = (
        "센터백",
        "골키퍼",
        "풀백",
        "미드필더",
        "윙어",
        "스트라이커",
        "cb",
        "gk",
        "rb",
        "lb",
        "cm",
        "dm",
        "am",
        "rw",
        "lw",
        "st",
        "cf",
    )
    form_terms = ("폼", "최근", "요즘", "많이뛰", "스프린트", "활동량", "상위", "비교")
    blocked_terms = ("로스터", "명단", "목록", "선수정보")
    return _contains_any(normalized, position_terms) and _contains_any(normalized, form_terms) and not _contains_any(
        normalized,
        blocked_terms,
    )


def _should_run_player_comparison_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    comparison_terms = ("비교", "vs", "누가더", "누가더좋", "누가더낫", "대비")
    blocked_terms = ("상대팀", "포지션별")
    return _contains_any(normalized, comparison_terms) and not _contains_any(normalized, blocked_terms)


def _should_run_opponent_match_lookup_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    opponent_terms = ("상대팀", "상대로", "상대", "전적", "상대결과", "현대고전", "전북현대u18", "수원공고u18")
    match_terms = ("경기", "결과", "요약", "기록", "어땠", "전")
    blocked_terms = ("선수", "비교")
    if _contains_any(normalized, blocked_terms) or not _contains_any(normalized, match_terms):
        return False
    return _contains_any(normalized, opponent_terms) or _resolve_opponent_from_question(question) is not None


def _should_run_roster_lookup_direct(question: str) -> bool:
    normalized = _normalized_question_text(question)
    roster_terms = ("로스터", "명단", "목록", "선수단", "누구있", "누구야", "보여줘", "알려줘")
    general_roster_terms = ("선수단", "우리팀", "팀", "스쿼드")
    filter_terms = (
        "gk",
        "cb",
        "rb",
        "lb",
        "dm",
        "cm",
        "am",
        "rw",
        "lw",
        "st",
        "cf",
        "센터백",
        "골키퍼",
        "풀백",
        "미드필더",
        "윙어",
        "스트라이커",
        "왼발",
        "오른발",
        "양발",
        "active",
        "inactive",
        "임대",
    )
    blocked_terms = ("프로필", "평가", "상담", "최근경기", "최근훈련")
    has_roster_intent = _contains_any(normalized, roster_terms)
    has_filter = _contains_any(normalized, filter_terms)
    has_general_roster_scope = _contains_any(normalized, general_roster_terms)
    return has_roster_intent and (has_filter or has_general_roster_scope) and not _contains_any(
        normalized,
        blocked_terms,
    )


def _normalized_question_text(question: str) -> str:
    return re.sub(r"\s+", "", question).lower()


def _contains_any(normalized_question: str, terms: tuple[str, ...]) -> bool:
    return any(term in normalized_question for term in terms)


def _build_player_name_required_response(
    *,
    question: str,
    answer: str,
    reason: str,
) -> AssistantQueryResponse:
    return _build_answer_only_response(
        question=question,
        answer=answer,
        reason=reason,
    )


def _run_injury_cause_analysis_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)
    if resolved_player is None:
        return _build_answer_only_response(
            question=question,
            answer="부상 원인을 보려면 선수 이름이 필요합니다. 분석할 선수 이름을 함께 적어주세요.",
            reason="Could not resolve a player name from the question for the injury-cause playbook.",
        )

    player_id, player_name = resolved_player
    sql_query = (
        "SELECT p.player_id, p.name, i.injury_date, i.injury_type, i.injury_part, "
        "i.severity_level, i.status, i.expected_return_date, i.actual_return_date, "
        "i.injury_mechanism, i.occurred_during, i.notes "
        "FROM football.injuries AS i "
        "JOIN football.players AS p ON p.player_id = i.player_id "
        f"WHERE p.player_id = '{player_id}' "
        "ORDER BY i.injury_date DESC, i.created_at DESC "
        "LIMIT 1"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the injury-cause-analysis playbook.",
        rows=rows,
        answer=_format_injury_cause_answer(top_row=rows[0]) if rows else f"{player_name}의 부상 기록을 찾지 못했습니다.",
        answer_reason="Returned a deterministic answer from the direct injury-cause playbook query.",
        empty_answer=f"{player_name}의 부상 기록을 찾지 못했습니다.",
        empty_reason="No injury rows were found for the resolved player.",
    )


def _run_player_profile_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)
    if resolved_player is None:
        return _build_player_name_required_response(
            question=question,
            answer="선수 프로필을 보려면 선수 이름이 필요합니다. 선수 이름을 함께 적어주세요.",
            reason="Could not resolve a player name from the question for the player-profile-summary playbook.",
        )

    player_id, player_name = resolved_player
    sql_query = (
        "WITH base_player AS ("
        " SELECT player_id, name, jersey_number, primary_position, secondary_position, foot, nationality, status, joined_at, previous_team"
        " FROM football.players"
        f" WHERE player_id = '{player_id}'"
        "), latest_physical AS ("
        " SELECT player_id, created_at AS physical_profile_date, height_cm, weight_kg, body_fat_percentage, bmi, muscle_mass_kg"
        " FROM football.player_latest_physical_profile"
        f" WHERE player_id = '{player_id}'"
        "), current_injury AS ("
        " SELECT player_id, injury_date, injury_type, injury_part, injury_status, expected_return_date"
        " FROM football.player_current_injury_status"
        f" WHERE player_id = '{player_id}' AND injury_id IS NOT NULL AND actual_return_date IS NULL"
        " ORDER BY injury_date DESC"
        " LIMIT 1"
        "), latest_test AS ("
        " SELECT player_id, test_date AS physical_test_date, sprint_10m, sprint_30m, vertical_jump_cm, agility_t_test_sec"
        " FROM football.physical_tests"
        f" WHERE player_id = '{player_id}'"
        " ORDER BY test_date DESC, physical_test_id DESC"
        " LIMIT 1"
        "), latest_eval AS ("
        " SELECT player_id, evaluation_date, technical, tactical, physical, mental, coach_comment"
        " FROM football.evaluations"
        f" WHERE player_id = '{player_id}'"
        " ORDER BY evaluation_date DESC, evaluation_id DESC"
        " LIMIT 1"
        "), latest_counsel AS ("
        " SELECT player_id, counseling_date, topic, summary"
        " FROM football.counseling_notes"
        f" WHERE player_id = '{player_id}'"
        " ORDER BY counseling_date DESC, counseling_id DESC"
        " LIMIT 1"
        ") "
        "SELECT"
        " bp.name, bp.jersey_number, bp.primary_position, bp.secondary_position, bp.foot, bp.nationality, bp.status, bp.joined_at, bp.previous_team,"
        " lp.physical_profile_date, lp.height_cm, lp.weight_kg, lp.body_fat_percentage, lp.bmi, lp.muscle_mass_kg,"
        " ci.injury_date, ci.injury_type, ci.injury_part, ci.injury_status, ci.expected_return_date,"
        " lt.physical_test_date, lt.sprint_10m, lt.sprint_30m, lt.vertical_jump_cm, lt.agility_t_test_sec,"
        " le.evaluation_date, le.technical, le.tactical, le.physical, le.mental, le.coach_comment,"
        " lc.counseling_date, lc.topic AS counseling_topic, lc.summary AS counseling_summary"
        " FROM base_player AS bp"
        " LEFT JOIN latest_physical AS lp ON lp.player_id = bp.player_id"
        " LEFT JOIN current_injury AS ci ON ci.player_id = bp.player_id"
        " LEFT JOIN latest_test AS lt ON lt.player_id = bp.player_id"
        " LEFT JOIN latest_eval AS le ON le.player_id = bp.player_id"
        " LEFT JOIN latest_counsel AS lc ON lc.player_id = bp.player_id"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the player-profile-summary playbook.",
        rows=rows,
        answer=_format_player_profile_summary_answer(rows[0]) if rows else f"{player_name}의 프로필 데이터를 찾지 못했습니다.",
        answer_reason="Returned a deterministic answer from the direct player-profile-summary playbook query.",
        empty_answer=f"{player_name}의 프로필 데이터를 찾지 못했습니다.",
        empty_reason="No roster rows were found for the resolved player.",
    )


def _run_physical_change_analysis_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)
    if resolved_player is None:
        return _build_player_name_required_response(
            question=question,
            answer="피지컬 변화를 보려면 선수 이름이 필요합니다. 선수 이름을 함께 적어주세요.",
            reason="Could not resolve a player name from the question for the physical-change-analysis playbook.",
        )

    player_id, player_name = resolved_player
    sql_query = (
        "WITH ranked_profiles AS ("
        " SELECT player_id, created_at, weight_kg, body_fat_percentage, bmi, muscle_mass_kg,"
        " ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY created_at DESC, physical_data_id DESC) AS rn"
        " FROM football.physical_profiles"
        f" WHERE player_id = '{player_id}'"
        "), ranked_tests AS ("
        " SELECT player_id, test_date, sprint_10m, sprint_30m, vertical_jump_cm, agility_t_test_sec,"
        " ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY test_date DESC, physical_test_id DESC) AS rn"
        " FROM football.physical_tests"
        f" WHERE player_id = '{player_id}'"
        ") "
        "SELECT"
        " p.name,"
        " lp.created_at AS latest_profile_date, pp.created_at AS previous_profile_date,"
        " lp.weight_kg AS latest_weight_kg, pp.weight_kg AS previous_weight_kg,"
        " lp.body_fat_percentage AS latest_body_fat_percentage, pp.body_fat_percentage AS previous_body_fat_percentage,"
        " lp.bmi AS latest_bmi, pp.bmi AS previous_bmi,"
        " lp.muscle_mass_kg AS latest_muscle_mass_kg, pp.muscle_mass_kg AS previous_muscle_mass_kg,"
        " lt.test_date AS latest_test_date, pt.test_date AS previous_test_date,"
        " lt.sprint_10m AS latest_sprint_10m, pt.sprint_10m AS previous_sprint_10m,"
        " lt.sprint_30m AS latest_sprint_30m, pt.sprint_30m AS previous_sprint_30m,"
        " lt.vertical_jump_cm AS latest_vertical_jump_cm, pt.vertical_jump_cm AS previous_vertical_jump_cm,"
        " lt.agility_t_test_sec AS latest_agility_t_test_sec, pt.agility_t_test_sec AS previous_agility_t_test_sec"
        " FROM football.players AS p"
        " LEFT JOIN ranked_profiles AS lp ON lp.player_id = p.player_id AND lp.rn = 1"
        " LEFT JOIN ranked_profiles AS pp ON pp.player_id = p.player_id AND pp.rn = 2"
        " LEFT JOIN ranked_tests AS lt ON lt.player_id = p.player_id AND lt.rn = 1"
        " LEFT JOIN ranked_tests AS pt ON pt.player_id = p.player_id AND pt.rn = 2"
        f" WHERE p.player_id = '{player_id}'"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the physical-change-analysis playbook.",
        rows=rows,
        answer=_format_physical_change_answer(rows[0]) if rows else f"{player_name}의 피지컬 변화 데이터를 찾지 못했습니다.",
        answer_reason="Returned a deterministic answer from the direct physical-change-analysis playbook query.",
        empty_answer=f"{player_name}의 피지컬 변화 데이터를 찾지 못했습니다.",
        empty_reason="No physical rows were found for the resolved player.",
    )


def _run_evaluation_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)
    if resolved_player is None:
        return _build_player_name_required_response(
            question=question,
            answer="평가 요약을 보려면 선수 이름이 필요합니다. 선수 이름을 함께 적어주세요.",
            reason="Could not resolve a player name from the question for the evaluation-summary playbook.",
        )

    player_id, player_name = resolved_player
    sql_query = (
        "WITH ranked_evaluations AS ("
        " SELECT player_id, evaluation_date, technical, tactical, physical, mental, coach_comment,"
        " ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY evaluation_date DESC, evaluation_id DESC) AS rn"
        " FROM football.evaluations"
        f" WHERE player_id = '{player_id}'"
        ") "
        "SELECT"
        " p.name,"
        " le.evaluation_date AS latest_evaluation_date, pe.evaluation_date AS previous_evaluation_date,"
        " le.technical AS latest_technical, pe.technical AS previous_technical,"
        " le.tactical AS latest_tactical, pe.tactical AS previous_tactical,"
        " le.physical AS latest_physical, pe.physical AS previous_physical,"
        " le.mental AS latest_mental, pe.mental AS previous_mental,"
        " le.coach_comment AS latest_coach_comment"
        " FROM football.players AS p"
        " LEFT JOIN ranked_evaluations AS le ON le.player_id = p.player_id AND le.rn = 1"
        " LEFT JOIN ranked_evaluations AS pe ON pe.player_id = p.player_id AND pe.rn = 2"
        f" WHERE p.player_id = '{player_id}'"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the evaluation-summary playbook.",
        rows=rows,
        answer=_format_evaluation_summary_answer(rows[0]) if rows else f"{player_name}의 평가 데이터를 찾지 못했습니다.",
        answer_reason="Returned a deterministic answer from the direct evaluation-summary playbook query.",
        empty_answer=f"{player_name}의 평가 데이터를 찾지 못했습니다.",
        empty_reason="No evaluation rows were found for the resolved player.",
    )


def _run_counseling_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)
    if resolved_player is None:
        return _build_player_name_required_response(
            question=question,
            answer="상담 기록을 보려면 선수 이름이 필요합니다. 선수 이름을 함께 적어주세요.",
            reason="Could not resolve a player name from the question for the counseling-summary playbook.",
        )

    player_id, player_name = resolved_player
    sql_query = (
        "SELECT p.name, c.counseling_date, c.topic, c.summary "
        "FROM football.counseling_notes AS c "
        "JOIN football.players AS p ON p.player_id = c.player_id "
        f"WHERE p.player_id = '{player_id}' "
        "ORDER BY c.counseling_date DESC, c.counseling_id DESC "
        "LIMIT 3"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the counseling-summary playbook.",
        rows=rows,
        answer=_format_counseling_summary_answer(rows) if rows else f"{player_name}의 상담 기록을 찾지 못했습니다.",
        answer_reason="Returned a deterministic answer from the direct counseling-summary playbook query.",
        empty_answer=f"{player_name}의 상담 기록을 찾지 못했습니다.",
        empty_reason="No counseling rows were found for the resolved player.",
    )


def _run_player_recent_match_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)
    if resolved_player is None:
        return _build_player_name_required_response(
            question=question,
            answer="선수 최근 경기 요약을 보려면 선수 이름이 필요합니다. 선수 이름을 함께 적어주세요.",
            reason="Could not resolve a player name from the question for the player-recent-match-summary playbook.",
        )

    player_id, player_name = resolved_player
    row_limit = 3 if _contains_any(_normalized_question_text(question), ("요약", "정리", "최근", "지난", "보여")) else 1
    official_filter = "AND pmf.match_type = '공식' " if _contains_any(_normalized_question_text(question), ("공식경기", "공식전", "공식")) else ""
    sql_query = (
        "SELECT pmf.player_name, pmf.match_date, pmf.match_type, pmf.opponent_team, pmf.minutes_played, "
        "pmf.goals, pmf.assists, pmf.shots, pmf.pass_accuracy, pmf.cross_accuracy, pmf.total_distance, pmf.sprint_count "
        "FROM football.player_match_facts AS pmf "
        f"WHERE pmf.player_id = '{player_id}' "
        f"{official_filter}"
        "ORDER BY pmf.match_date DESC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the player-recent-match-summary playbook.",
        rows=rows,
        answer=_format_player_recent_match_summary_answer(rows) if rows else f"{player_name}의 최근 경기 기록을 찾지 못했습니다.",
        answer_reason="Returned a deterministic answer from the direct player-recent-match-summary playbook query.",
        empty_answer=f"{player_name}의 최근 경기 기록을 찾지 못했습니다.",
        empty_reason="No recent match rows were found for the resolved player.",
    )


def _run_player_recent_training_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)
    if resolved_player is None:
        return _build_player_name_required_response(
            question=question,
            answer="선수 최근 훈련 요약을 보려면 선수 이름이 필요합니다. 선수 이름을 함께 적어주세요.",
            reason="Could not resolve a player name from the question for the player-recent-training-summary playbook.",
        )

    player_id, player_name = resolved_player
    row_limit = 3 if _contains_any(_normalized_question_text(question), ("요약", "정리", "최근", "세션", "보여")) else 1
    sql_query = (
        "SELECT p.name, t.training_date, t.session_name, t.training_focus, t.intensity_level, "
        "tgs.total_distance, tgs.sprint_count, tgs.accel_count, tgs.decel_count "
        "FROM football.training_gps_stats AS tgs "
        "JOIN football.trainings AS t ON t.training_id = tgs.training_id "
        "JOIN football.players AS p ON p.player_id = tgs.player_id "
        f"WHERE p.player_id = '{player_id}' "
        "ORDER BY t.training_date DESC, t.training_id DESC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the player-recent-training-summary playbook.",
        rows=rows,
        answer=_format_player_recent_training_summary_answer(rows) if rows else f"{player_name}의 최근 훈련 기록을 찾지 못했습니다.",
        answer_reason="Returned a deterministic answer from the direct player-recent-training-summary playbook query.",
        empty_answer=f"{player_name}의 최근 훈련 기록을 찾지 못했습니다.",
        empty_reason="No recent training rows were found for the resolved player.",
    )


def _run_return_to_play_timeline_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_player = _resolve_player_from_question(question)
    if resolved_player is not None:
        player_id, player_name = resolved_player
        sql_query = (
            "SELECT name, injury_date, injury_type, injury_part, injury_status, expected_return_date "
            "FROM football.player_current_injury_status "
            f"WHERE player_id = '{player_id}' AND injury_id IS NOT NULL AND actual_return_date IS NULL "
            "ORDER BY injury_date DESC "
            "LIMIT 1"
        )
        reason = "Answered directly from the return-to-play playbook for the resolved player."
    else:
        row_limit = max(3, _requested_result_limit(question))
        sql_query = (
            "SELECT name, injury_date, injury_type, injury_part, injury_status, expected_return_date "
            "FROM football.player_current_injury_status "
            "WHERE injury_id IS NOT NULL AND actual_return_date IS NULL "
            "ORDER BY expected_return_date ASC NULLS LAST, injury_date DESC "
            f"LIMIT {row_limit}"
        )
        reason = "Answered directly from the team return-to-play playbook."
        player_name = None
    rows = _execute_read_only_sql(sql_query)
    empty_answer = f"{player_name}의 현재 복귀 추적 데이터가 없습니다." if player_name else "현재 복귀 일정을 추적 중인 부상 선수는 없습니다."
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason=reason,
        rows=rows,
        answer=_format_return_to_play_timeline_answer(rows) if rows else empty_answer,
        answer_reason="Returned a deterministic answer from the direct return-to-play playbook query.",
        empty_answer=empty_answer,
        empty_reason="No rows were returned for the return-to-play playbook query.",
    )


def _run_physical_leaderboard_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    metric, direction = _resolve_physical_metric(question)
    row_limit = _requested_result_limit(question)
    sql_query = (
        "SELECT name, height_cm, weight_kg, body_fat_percentage, bmi, muscle_mass_kg, created_at "
        "FROM football.player_latest_physical_profile "
        f"ORDER BY {metric} {direction} NULLS LAST, name ASC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the physical-leaderboard playbook.",
        rows=rows,
        answer=_format_physical_leaderboard_answer(rows=rows, metric=metric, direction=direction),
        answer_reason="Returned a deterministic answer from the direct physical-leaderboard playbook query.",
    )


def _run_physical_test_leaderboard_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    metric, direction = _resolve_physical_test_metric(question)
    row_limit = _requested_result_limit(question)
    sql_query = (
        "SELECT p.name, pt.test_date, pt.sprint_10m, pt.sprint_30m, pt.vertical_jump_cm, pt.agility_t_test_sec "
        "FROM football.physical_tests AS pt "
        "JOIN football.players AS p ON p.player_id = pt.player_id "
        "WHERE pt.test_date = (SELECT MAX(test_date) FROM football.physical_tests) "
        f"ORDER BY pt.{metric} {direction} NULLS LAST, p.name ASC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the physical-test-leaderboard playbook.",
        rows=rows,
        answer=_format_physical_test_leaderboard_answer(rows=rows, metric=metric, direction=direction),
        answer_reason="Returned a deterministic answer from the direct physical-test-leaderboard playbook query.",
    )


def _run_evaluation_leaderboard_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    metric, direction = _resolve_evaluation_metric(question)
    row_limit = _requested_result_limit(question)
    sql_query = (
        "SELECT p.name, e.evaluation_date, e.technical, e.tactical, e.physical, e.mental "
        "FROM football.evaluations AS e "
        "JOIN football.players AS p ON p.player_id = e.player_id "
        "WHERE e.evaluation_date = (SELECT MAX(evaluation_date) FROM football.evaluations) "
        f"ORDER BY e.{metric} {direction} NULLS LAST, p.name ASC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the evaluation-leaderboard playbook.",
        rows=rows,
        answer=_format_evaluation_leaderboard_answer(rows=rows, metric=metric, direction=direction),
        answer_reason="Returned a deterministic answer from the direct evaluation-leaderboard playbook query.",
    )


def _run_counseling_topic_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    row_limit = max(3, _requested_result_limit(question))
    sql_query = (
        "SELECT topic, COUNT(*) AS note_count, MAX(counseling_date) AS latest_date "
        "FROM football.counseling_notes "
        "WHERE counseling_date >= (SELECT MAX(counseling_date) FROM football.counseling_notes) - INTERVAL '60 days' "
        "GROUP BY topic "
        "ORDER BY note_count DESC, latest_date DESC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the counseling-topic-summary playbook.",
        rows=rows,
        answer=_format_counseling_topic_summary_answer(rows),
        answer_reason="Returned a deterministic answer from the direct counseling-topic-summary playbook query.",
    )


def _run_roster_lookup_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    position_filter = _resolve_position_filter(question)
    foot_filter = _resolve_foot_filter(question)
    status_filter = _resolve_status_filter(question)
    conditions: list[str] = []
    if position_filter is not None:
        conditions.append(_build_position_sql_condition(position_filter))
    if foot_filter is not None:
        conditions.append(f"foot = '{foot_filter}'")
    if status_filter is not None:
        conditions.append(f"status = '{status_filter}'")
    where_sql = f"WHERE {' AND '.join(conditions)} " if conditions else ""
    row_limit = max(5, _requested_result_limit(question))
    sql_query = (
        "SELECT name, jersey_number, primary_position, secondary_position, foot, nationality, status "
        "FROM football.players "
        f"{where_sql}"
        "ORDER BY jersey_number ASC NULLS LAST, name ASC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the roster-lookup playbook.",
        rows=rows,
        answer=_format_roster_lookup_answer(
            rows=rows,
            position_filter=position_filter,
            foot_filter=foot_filter,
            status_filter=status_filter,
        ),
        answer_reason="Returned a deterministic answer from the direct roster-lookup playbook query.",
    )


def _run_team_recent_match_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    normalized = _normalized_question_text(question)
    official_filter = "WHERE m.match_type = '공식' " if _contains_any(normalized, ("공식전", "공식경기", "공식")) else ""
    row_limit = max(1, _requested_result_limit(question))
    if _contains_any(normalized, ("최근", "요약", "흐름", "3경기", "비교")):
        row_limit = max(row_limit, 3)
    sql_query = (
        "SELECT m.match_date, m.match_type, ot.opponent_team_name, m.goals_for, m.goals_against, "
        "m.possession_for, m.possession_against, mts.shots, mts.shots_on_target, mts.pass_accuracy, mts.cross_accuracy, mts.duel_win_rate, mts.yellow_cards "
        "FROM football.matches AS m "
        "LEFT JOIN football.opponent_teams AS ot ON ot.opponent_team_id = m.opponent_team_id "
        "LEFT JOIN football.match_team_stats AS mts ON mts.match_id = m.match_id "
        f"{official_filter}"
        "ORDER BY m.match_date DESC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the team-recent-match-summary playbook.",
        rows=rows,
        answer=_format_team_recent_match_summary_answer(rows),
        answer_reason="Returned a deterministic answer from the direct team-recent-match-summary playbook query.",
    )


def _run_position_recent_form_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    position_filter = _resolve_position_filter(question)
    if position_filter is None:
        return _build_player_name_required_response(
            question=question,
            answer="포지션별 최근 폼을 보려면 포지션을 함께 적어주세요. 예: 센터백, 풀백, 윙어.",
            reason="Could not resolve a position from the question for the position-recent-form playbook.",
        )
    row_limit = max(3, _requested_result_limit(question))
    metric, order_clause = _resolve_position_form_order(question)
    position_condition = _build_position_sql_condition(position_filter).replace("primary_position", "p.primary_position").replace("secondary_position", "p.secondary_position")
    sql_query = (
        "WITH anchor AS (SELECT MAX(match_date) AS max_match_date FROM football.matches) "
        "SELECT pmf.player_name, COUNT(*) AS recent_matches, AVG(pmf.total_distance) AS avg_total_distance, "
        "AVG(pmf.sprint_count) AS avg_sprint_count, AVG(pmf.minutes_played) AS avg_minutes "
        "FROM football.player_match_facts AS pmf "
        "JOIN football.players AS p ON p.player_id = pmf.player_id "
        "CROSS JOIN anchor AS a "
        "WHERE pmf.match_date > a.max_match_date - INTERVAL '21 days' "
        f"AND {position_condition} "
        "GROUP BY pmf.player_id, pmf.player_name "
        f"ORDER BY {order_clause} "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the position-recent-form playbook.",
        rows=rows,
        answer=_format_position_recent_form_answer(rows=rows, position_filter=position_filter, metric=metric),
        answer_reason="Returned a deterministic answer from the direct position-recent-form playbook query.",
    )


def _run_player_comparison_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_players = _resolve_players_from_question(question, limit=2)
    if len(resolved_players) < 2:
        return _build_player_name_required_response(
            question=question,
            answer="선수 비교를 하려면 비교할 선수 이름 두 명을 함께 적어주세요.",
            reason="Could not resolve two player names from the question for the player-comparison playbook.",
        )

    player_ids = "', '".join(player_id for player_id, _ in resolved_players)
    sql_query = (
        "WITH recent_match_window AS ("
        " SELECT pmf.player_id, pmf.player_name, COUNT(*) AS recent_matches, AVG(pmf.total_distance) AS avg_total_distance, "
        "AVG(pmf.sprint_count) AS avg_sprint_count, AVG(pmf.minutes_played) AS avg_minutes, SUM(pmf.goals) AS total_goals, SUM(pmf.assists) AS total_assists "
        "FROM football.player_match_facts AS pmf "
        "WHERE pmf.match_date > (SELECT MAX(match_date) FROM football.matches) - INTERVAL '21 days' "
        f"AND pmf.player_id IN ('{player_ids}') "
        "GROUP BY pmf.player_id, pmf.player_name"
        "), latest_eval AS ("
        " SELECT e.player_id, e.evaluation_date, e.technical, e.tactical, e.physical, e.mental, "
        "ROW_NUMBER() OVER (PARTITION BY e.player_id ORDER BY e.evaluation_date DESC, e.evaluation_id DESC) AS rn "
        "FROM football.evaluations AS e "
        f"WHERE e.player_id IN ('{player_ids}')"
        ") "
        "SELECT p.name, rm.recent_matches, rm.avg_total_distance, rm.avg_sprint_count, rm.avg_minutes, rm.total_goals, rm.total_assists, "
        "le.evaluation_date, le.technical, le.tactical, le.physical, le.mental "
        "FROM football.players AS p "
        "LEFT JOIN recent_match_window AS rm ON rm.player_id = p.player_id "
        "LEFT JOIN latest_eval AS le ON le.player_id = p.player_id AND le.rn = 1 "
        f"WHERE p.player_id IN ('{player_ids}') "
        "ORDER BY p.name ASC"
    )
    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the player-comparison playbook.",
        rows=rows,
        answer=_format_player_comparison_answer(rows),
        answer_reason="Returned a deterministic answer from the direct player-comparison playbook query.",
    )


def _run_opponent_match_lookup_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    resolved_opponent = _resolve_opponent_from_question(question)
    if resolved_opponent is None:
        return _build_player_name_required_response(
            question=question,
            answer="상대팀 기준 조회를 하려면 상대팀 이름을 함께 적어주세요.",
            reason="Could not resolve an opponent name from the question for the opponent-match-lookup playbook.",
        )
    opponent_id, opponent_name = resolved_opponent
    row_limit = max(1, _requested_result_limit(question))
    if _contains_any(_normalized_question_text(question), ("전적", "최근", "요약", "흐름")):
        row_limit = max(row_limit, 3)
    sql_query = (
        "SELECT m.match_date, m.match_type, ot.opponent_team_name, m.goals_for, m.goals_against, "
        "m.possession_for, m.possession_against, mts.shots, mts.shots_on_target, mts.pass_accuracy, mts.duel_win_rate "
        "FROM football.matches AS m "
        "JOIN football.opponent_teams AS ot ON ot.opponent_team_id = m.opponent_team_id "
        "LEFT JOIN football.match_team_stats AS mts ON mts.match_id = m.match_id "
        f"WHERE ot.opponent_team_id = '{opponent_id}' "
        "ORDER BY m.match_date DESC "
        f"LIMIT {row_limit}"
    )
    rows = _execute_read_only_sql(sql_query)
    empty_answer = f"{opponent_name} 상대 경기 기록을 찾지 못했습니다."
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the opponent-match-lookup playbook.",
        rows=rows,
        answer=_format_opponent_match_lookup_answer(rows) if rows else empty_answer,
        answer_reason="Returned a deterministic answer from the direct opponent-match-lookup playbook query.",
        empty_answer=empty_answer,
    )


def _run_activity_leader_playbook(
    *,
    question: str,
    match_label: str,
    match_filter_sql: str,
    cte_name: str,
    reason: str,
) -> AssistantQueryResponse:
    sql_query = (
        f"WITH {cte_name} AS ("
        " SELECT match_id, match_date"
        " FROM football.matches"
        f" {match_filter_sql}"
        " ORDER BY match_date DESC"
        " LIMIT 1"
        ") "
        "SELECT tm.match_date, pmf.player_name, pmf.total_distance, pmf.sprint_count, pmf.minutes_played "
        "FROM football.player_match_facts AS pmf "
        f"JOIN {cte_name} AS tm ON tm.match_id = pmf.match_id "
        "ORDER BY pmf.total_distance DESC NULLS LAST, pmf.sprint_count DESC NULLS LAST "
        "LIMIT 1"
    )
    rows = _execute_read_only_sql(sql_query)
    empty_answer = f"{match_label} 활동량 데이터를 찾지 못했습니다."
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason=reason,
        rows=rows,
        answer=_format_activity_leader_answer(top_row=rows[0], match_label=match_label) if rows else empty_answer,
        answer_reason="Returned a deterministic answer from the direct activity-leader playbook query.",
        empty_answer=empty_answer,
        empty_reason="No rows were returned for the direct playbook query.",
    )


def _run_training_load_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    mode = _detect_training_load_mode(question)
    row_limit = _requested_result_limit(question)

    if mode == "latest":
        sql_query = (
            "WITH latest_training AS ("
            " SELECT training_id, training_date, intensity_level, session_name"
            " FROM football.trainings"
            " ORDER BY training_date DESC, training_id DESC"
            " LIMIT 1"
            ") "
            "SELECT lt.training_date, lt.intensity_level, lt.session_name, p.name, "
            "tgs.total_distance, tgs.sprint_count, tgs.accel_count, tgs.decel_count "
            "FROM football.training_gps_stats AS tgs "
            "JOIN latest_training AS lt ON lt.training_id = tgs.training_id "
            "JOIN football.players AS p ON p.player_id = tgs.player_id "
            f"ORDER BY {_training_order_clause(question, aggregate=False)} "
            f"LIMIT {row_limit}"
        )
        reason = "Answered directly from the latest-training-load playbook."
    elif mode == "trend":
        sql_query = (
            "WITH anchor AS ("
            " SELECT MAX(training_date) AS max_training_date"
            " FROM football.trainings"
            "), training_windows AS ("
            " SELECT"
            "   p.player_id,"
            "   p.name,"
            "   COUNT(*) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '14 days' AND t.training_date <= a.max_training_date) AS recent_sessions,"
            "   AVG(tgs.total_distance) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '14 days' AND t.training_date <= a.max_training_date) AS recent_avg_total_distance,"
            "   AVG(tgs.sprint_count) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '14 days' AND t.training_date <= a.max_training_date) AS recent_avg_sprint_count,"
            "   AVG(tgs.accel_count) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '14 days' AND t.training_date <= a.max_training_date) AS recent_avg_accel_count,"
            "   AVG(tgs.decel_count) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '14 days' AND t.training_date <= a.max_training_date) AS recent_avg_decel_count,"
            "   SUM(CASE WHEN t.training_date > a.max_training_date - INTERVAL '14 days' AND t.training_date <= a.max_training_date AND t.intensity_level::text = 'high' THEN 1 ELSE 0 END) AS recent_high_sessions,"
            "   COUNT(*) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '28 days' AND t.training_date <= a.max_training_date - INTERVAL '14 days') AS prior_sessions,"
            "   AVG(tgs.total_distance) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '28 days' AND t.training_date <= a.max_training_date - INTERVAL '14 days') AS prior_avg_total_distance,"
            "   AVG(tgs.sprint_count) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '28 days' AND t.training_date <= a.max_training_date - INTERVAL '14 days') AS prior_avg_sprint_count,"
            "   MAX(t.training_date) FILTER (WHERE t.training_date > a.max_training_date - INTERVAL '14 days' AND t.training_date <= a.max_training_date) AS latest_training_date"
            " FROM football.training_gps_stats AS tgs"
            " JOIN football.trainings AS t ON t.training_id = tgs.training_id"
            " JOIN football.players AS p ON p.player_id = tgs.player_id"
            " CROSS JOIN anchor AS a"
            " WHERE t.training_date > a.max_training_date - INTERVAL '28 days'"
            "   AND t.training_date <= a.max_training_date"
            " GROUP BY p.player_id, p.name"
            ") "
            "SELECT"
            " name, recent_sessions, recent_avg_total_distance, prior_avg_total_distance,"
            " recent_avg_sprint_count, prior_avg_sprint_count, recent_avg_accel_count, recent_avg_decel_count,"
            " recent_high_sessions, latest_training_date,"
            " CASE WHEN prior_avg_total_distance > 0 THEN recent_avg_total_distance / prior_avg_total_distance END AS distance_ratio,"
            " CASE WHEN prior_avg_sprint_count > 0 THEN recent_avg_sprint_count / prior_avg_sprint_count END AS sprint_ratio"
            " FROM training_windows"
            " WHERE recent_sessions > 0"
            f" ORDER BY {_training_trend_order_clause(question)} "
            f"LIMIT {row_limit}"
        )
        reason = "Answered directly from the training-load trend playbook."
    else:
        sql_query = (
            "WITH anchor AS ("
            " SELECT MAX(training_date) AS max_training_date"
            " FROM football.trainings"
            "), recent_training AS ("
            " SELECT t.training_id, t.training_date, t.intensity_level"
            " FROM football.trainings AS t"
            " CROSS JOIN anchor AS a"
            " WHERE t.training_date >= a.max_training_date - INTERVAL '14 days'"
            "   AND t.training_date <= a.max_training_date"
            ") "
            "SELECT p.name, COUNT(*) AS recent_sessions, AVG(tgs.total_distance) AS avg_total_distance, "
            "AVG(tgs.sprint_count) AS avg_sprint_count, AVG(tgs.accel_count) AS avg_accel_count, "
            "AVG(tgs.decel_count) AS avg_decel_count, "
            "SUM(CASE WHEN rt.intensity_level::text = 'high' THEN 1 ELSE 0 END) AS high_sessions, "
            "MAX(rt.training_date) AS latest_training_date "
            "FROM football.training_gps_stats AS tgs "
            "JOIN recent_training AS rt ON rt.training_id = tgs.training_id "
            "JOIN football.players AS p ON p.player_id = tgs.player_id "
            "GROUP BY p.player_id, p.name "
            "HAVING COUNT(*) > 0 "
            f"ORDER BY {_training_order_clause(question, aggregate=True)} "
            f"LIMIT {row_limit}"
        )
        reason = "Answered directly from the recent-training-load playbook."

    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason=reason,
        rows=rows,
        answer=_format_training_load_answer(rows=rows, mode=mode, question=question),
        answer_reason="Returned a deterministic answer from the direct training-load playbook query.",
    )


def _run_combined_workload_summary_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    mode = _detect_combined_workload_mode(question)
    resolved_player = _resolve_player_from_question(question)
    player_where_sql = f"WHERE p.player_id = '{resolved_player[0]}' " if resolved_player is not None else ""
    row_limit = 1 if resolved_player is not None else max(3, _requested_result_limit(question))
    sql_query = (
        "WITH anchor AS ("
        " SELECT GREATEST("
        "   COALESCE((SELECT MAX(training_date) FROM football.trainings), DATE '1900-01-01'),"
        "   COALESCE((SELECT MAX(match_date) FROM football.matches), DATE '1900-01-01')"
        " ) AS snapshot_date"
        "), training_sessions AS ("
        " SELECT"
        "   tgs.player_id,"
        "   t.training_date AS session_date,"
        "   'training' AS session_source,"
        "   tgs.total_distance,"
        "   tgs.sprint_count,"
        "   tgs.hi_accel_count,"
        "   tgs.hi_decel_count,"
        "   COALESCE(tgs.play_time_min, 0) AS play_time_min,"
        "   tgs.max_speed,"
        "   CASE"
        "     WHEN t.intensity_level::text = 'low' THEN 0.88"
        "     WHEN t.intensity_level::text = 'high' THEN 1.15"
        "     ELSE 1.0"
        "   END AS intensity_multiplier"
        " FROM football.training_gps_stats AS tgs"
        " JOIN football.trainings AS t ON t.training_id = tgs.training_id"
        "), match_sessions AS ("
        " SELECT"
        "   mgs.player_id,"
        "   m.match_date AS session_date,"
        "   'match' AS session_source,"
        "   mgs.total_distance,"
        "   mgs.sprint_count,"
        "   mgs.hi_accel_count,"
        "   mgs.hi_decel_count,"
        "   mgs.play_time_min,"
        "   mgs.max_speed,"
        "   1.12 AS intensity_multiplier"
        " FROM football.match_gps_stats AS mgs"
        " JOIN football.matches AS m ON m.match_id = mgs.match_id"
        "), sessions AS ("
        " SELECT"
        "   player_id, session_date, session_source, total_distance, sprint_count,"
        "   ((total_distance * 18.0) + (play_time_min * 0.45) + (sprint_count * 3.0) + (hi_accel_count * 1.4) + (hi_decel_count * 1.4) + (max_speed * 0.18)) * intensity_multiplier AS session_load"
        " FROM training_sessions"
        " UNION ALL "
        " SELECT"
        "   player_id, session_date, session_source, total_distance, sprint_count,"
        "   ((total_distance * 20.0) + (play_time_min * 0.55) + (sprint_count * 3.4) + (hi_accel_count * 1.8) + (hi_decel_count * 1.8) + (max_speed * 0.22)) * intensity_multiplier AS session_load"
        " FROM match_sessions"
        "), player_load AS ("
        " SELECT"
        "   p.player_id,"
        "   p.name,"
        "   COUNT(*) FILTER (WHERE s.session_date > a.snapshot_date - INTERVAL '7 days' AND s.session_date <= a.snapshot_date) AS sessions_7d,"
        "   COUNT(*) FILTER (WHERE s.session_date > a.snapshot_date - INTERVAL '7 days' AND s.session_date <= a.snapshot_date AND s.session_source = 'training') AS training_sessions_7d,"
        "   COUNT(*) FILTER (WHERE s.session_date > a.snapshot_date - INTERVAL '7 days' AND s.session_date <= a.snapshot_date AND s.session_source = 'match') AS match_sessions_7d,"
        "   COALESCE(SUM(s.session_load) FILTER (WHERE s.session_date > a.snapshot_date - INTERVAL '7 days' AND s.session_date <= a.snapshot_date), 0) AS acute_load_7d,"
        "   COALESCE(SUM(s.total_distance) FILTER (WHERE s.session_date > a.snapshot_date - INTERVAL '7 days' AND s.session_date <= a.snapshot_date), 0) AS total_distance_7d,"
        "   COALESCE(SUM(s.sprint_count) FILTER (WHERE s.session_date > a.snapshot_date - INTERVAL '7 days' AND s.session_date <= a.snapshot_date), 0) AS sprint_count_7d,"
        "   COALESCE(SUM(s.session_load) FILTER (WHERE s.session_date > a.snapshot_date - INTERVAL '28 days' AND s.session_date <= a.snapshot_date - INTERVAL '7 days'), 0) / 3.0 AS chronic_load_baseline,"
        "   MAX(s.session_date) FILTER (WHERE s.session_date > a.snapshot_date - INTERVAL '28 days' AND s.session_date <= a.snapshot_date) AS latest_session_date"
        " FROM football.players AS p"
        " CROSS JOIN anchor AS a"
        " LEFT JOIN sessions AS s ON s.player_id = p.player_id"
        "   AND s.session_date > a.snapshot_date - INTERVAL '28 days'"
        "   AND s.session_date <= a.snapshot_date"
        f" {player_where_sql}"
        " GROUP BY p.player_id, p.name"
        ") "
        "SELECT"
        " name, sessions_7d, training_sessions_7d, match_sessions_7d, acute_load_7d, chronic_load_baseline,"
        " CASE WHEN chronic_load_baseline > 0 THEN acute_load_7d / chronic_load_baseline END AS acute_chronic_ratio,"
        " total_distance_7d, sprint_count_7d, latest_session_date"
        " FROM player_load"
        " WHERE sessions_7d > 0"
        f" ORDER BY {_combined_workload_order_clause(question=question, mode=mode)} "
        f"LIMIT {row_limit}"
    )

    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason="Answered directly from the combined-workload playbook.",
        rows=rows,
        answer=_format_combined_workload_summary_answer(
            rows=rows,
            mode=mode,
            question=question,
            player_name=resolved_player[1] if resolved_player is not None else None,
        ),
        answer_reason="Returned a deterministic answer from the direct combined-workload playbook query.",
    )


def _run_recent_match_form_playbook(
    *,
    question: str,
) -> AssistantQueryResponse:
    mode = _detect_recent_match_form_mode(question)
    row_limit = _requested_result_limit(question)

    if mode in {"trend_up", "trend_down"}:
        order_direction = "ASC" if mode == "trend_down" else "DESC"
        sql_query = (
            "WITH anchor AS ("
            " SELECT MAX(match_date) AS max_match_date"
            " FROM football.matches"
            "), match_windows AS ("
            " SELECT"
            "   pmf.player_id,"
            "   pmf.player_name,"
            "   COUNT(*) FILTER (WHERE pmf.match_date > a.max_match_date - INTERVAL '21 days' AND pmf.match_date <= a.max_match_date) AS recent_matches,"
            "   AVG(pmf.total_distance) FILTER (WHERE pmf.match_date > a.max_match_date - INTERVAL '21 days' AND pmf.match_date <= a.max_match_date) AS recent_avg_total_distance,"
            "   AVG(pmf.sprint_count) FILTER (WHERE pmf.match_date > a.max_match_date - INTERVAL '21 days' AND pmf.match_date <= a.max_match_date) AS recent_avg_sprint_count,"
            "   COUNT(*) FILTER (WHERE pmf.match_date > a.max_match_date - INTERVAL '42 days' AND pmf.match_date <= a.max_match_date - INTERVAL '21 days') AS prior_matches,"
            "   AVG(pmf.total_distance) FILTER (WHERE pmf.match_date > a.max_match_date - INTERVAL '42 days' AND pmf.match_date <= a.max_match_date - INTERVAL '21 days') AS prior_avg_total_distance,"
            "   AVG(pmf.sprint_count) FILTER (WHERE pmf.match_date > a.max_match_date - INTERVAL '42 days' AND pmf.match_date <= a.max_match_date - INTERVAL '21 days') AS prior_avg_sprint_count,"
            "   MAX(pmf.match_date) FILTER (WHERE pmf.match_date > a.max_match_date - INTERVAL '21 days' AND pmf.match_date <= a.max_match_date) AS latest_match_date"
            " FROM football.player_match_facts AS pmf"
            " CROSS JOIN anchor AS a"
            " WHERE pmf.match_date > a.max_match_date - INTERVAL '42 days'"
            "   AND pmf.match_date <= a.max_match_date"
            " GROUP BY pmf.player_id, pmf.player_name"
            ") "
            "SELECT"
            " player_name, recent_matches, prior_matches, recent_avg_total_distance, prior_avg_total_distance,"
            " recent_avg_sprint_count, prior_avg_sprint_count, latest_match_date,"
            " CASE WHEN prior_avg_total_distance > 0 THEN recent_avg_total_distance / prior_avg_total_distance END AS distance_ratio,"
            " CASE WHEN prior_avg_sprint_count > 0 THEN recent_avg_sprint_count / prior_avg_sprint_count END AS sprint_ratio"
            " FROM match_windows"
            " WHERE recent_matches > 0"
            "   AND prior_matches > 0"
            f" ORDER BY {_recent_match_trend_order_clause(question, order_direction=order_direction)} "
            f"LIMIT {row_limit}"
        )
        reason = "Answered directly from the recent-match-form trend playbook."
    else:
        sql_query = (
            "WITH anchor AS ("
            " SELECT MAX(match_date) AS max_match_date"
            " FROM football.matches"
            "), recent_matches AS ("
            " SELECT m.match_id, m.match_date"
            " FROM football.matches AS m"
            " CROSS JOIN anchor AS a"
            " WHERE m.match_date >= a.max_match_date - INTERVAL '21 days'"
            "   AND m.match_date <= a.max_match_date"
            ") "
            "SELECT pmf.player_name, COUNT(*) AS recent_matches, AVG(pmf.total_distance) AS avg_total_distance, "
            "AVG(pmf.sprint_count) AS avg_sprint_count, MAX(pmf.match_date) AS latest_match_date "
            "FROM football.player_match_facts AS pmf "
            "JOIN recent_matches AS rm ON rm.match_id = pmf.match_id "
            "GROUP BY pmf.player_id, pmf.player_name "
            "HAVING COUNT(*) > 0 "
            f"ORDER BY {_recent_match_form_order_clause(question)} "
            f"LIMIT {row_limit}"
        )
        reason = "Answered directly from the recent-match-form playbook."

    rows = _execute_read_only_sql(sql_query)
    return _build_direct_playbook_response(
        question=question,
        sql_query=sql_query,
        sql_reason=reason,
        rows=rows,
        answer=_format_recent_match_form_answer(rows=rows, mode=mode, question=question),
        answer_reason="Returned a deterministic answer from the direct recent-match-form playbook query.",
    )


def _detect_training_load_mode(question: str) -> str:
    normalized = _normalized_question_text(question)
    trend_terms = ("급격", "오른", "증가", "overreaching", "의심", "과부하", "스파이크", "spike", "위험")
    latest_terms = ("가장최근", "마지막", "오늘", "latest", "세션", "session")
    if _contains_any(normalized, trend_terms):
        return "trend"
    if _contains_any(normalized, latest_terms):
        return "latest"
    return "recent"


def _detect_combined_workload_mode(question: str) -> str:
    normalized = _normalized_question_text(question)
    trend_terms = ("급격", "오른", "증가", "과부하", "스파이크", "spike", "위험", "acwr", "acutechronic", "ratio")
    return "trend" if _contains_any(normalized, trend_terms) else "recent"


def _detect_recent_match_form_mode(question: str) -> str:
    normalized = _normalized_question_text(question)
    decline_terms = ("떨어", "하락", "부진", "나빠")
    improvement_terms = ("올라", "상승")
    if _contains_any(normalized, decline_terms):
        return "trend_down"
    if _contains_any(normalized, improvement_terms):
        return "trend_up"
    return "leaderboard"


def _requested_result_limit(question: str) -> int:
    normalized = _normalized_question_text(question)
    multi_terms = ("상위", "top", "players", "순", "목록", "명단", "보여", "비교", "leaders")
    return 3 if _contains_any(normalized, multi_terms) else 1


def _resolve_physical_metric(question: str) -> tuple[str, str]:
    normalized = _normalized_question_text(question)
    if "체지방" in normalized:
        direction = "ASC" if _contains_any(normalized, ("낮", "적", "lean")) else "DESC"
        return "body_fat_percentage", direction
    if "bmi" in normalized:
        direction = "ASC" if _contains_any(normalized, ("낮", "적")) else "DESC"
        return "bmi", direction
    if "체중" in normalized:
        direction = "ASC" if _contains_any(normalized, ("낮", "적", "가벼")) else "DESC"
        return "weight_kg", direction
    return "muscle_mass_kg", "ASC" if _contains_any(normalized, ("낮", "적")) else "DESC"


def _resolve_physical_test_metric(question: str) -> tuple[str, str]:
    normalized = _normalized_question_text(question)
    if "30m" in normalized:
        if _contains_any(normalized, ("느린", "늦", "높")):
            return "sprint_30m", "DESC"
        return "sprint_30m", "ASC"
    if _contains_any(normalized, ("점프", "vertical")):
        return "vertical_jump_cm", "ASC" if _contains_any(normalized, ("낮", "작")) else "DESC"
    if _contains_any(normalized, ("민첩", "agility", "ttest")):
        return "agility_t_test_sec", "DESC" if _contains_any(normalized, ("느린", "늦")) else "ASC"
    return "sprint_10m", "DESC" if _contains_any(normalized, ("느린", "늦", "높")) else "ASC"


def _resolve_evaluation_metric(question: str) -> tuple[str, str]:
    normalized = _normalized_question_text(question)
    if "technical" in normalized or "기술" in normalized:
        metric = "technical"
    elif "tactical" in normalized or "전술" in normalized:
        metric = "tactical"
    elif "mental" in normalized or "멘탈" in normalized:
        metric = "mental"
    else:
        metric = "physical"
    direction = "ASC" if _contains_any(normalized, ("낮", "나쁜", "부진")) else "DESC"
    return metric, direction


def _resolve_position_form_order(question: str) -> tuple[str, str]:
    normalized = _normalized_question_text(question)
    if _contains_any(normalized, ("스프린트", "sprint")):
        return "avg_sprint_count", "avg_sprint_count DESC NULLS LAST, avg_total_distance DESC NULLS LAST, recent_matches DESC"
    if _contains_any(normalized, ("출전", "minutes", "시간")):
        return "avg_minutes", "avg_minutes DESC NULLS LAST, avg_total_distance DESC NULLS LAST, recent_matches DESC"
    return "avg_total_distance", "avg_total_distance DESC NULLS LAST, avg_sprint_count DESC NULLS LAST, recent_matches DESC"


def _resolve_position_filter(question: str) -> str | None:
    normalized = _normalized_question_text(question)
    position_map = {
        "gk": ("gk", "골키퍼"),
        "cb": ("cb", "센터백"),
        "rb": ("rb", "라이트백"),
        "lb": ("lb", "레프트백"),
        "dm": ("dm", "수비형미드필더"),
        "cm": ("cm", "중앙미드필더"),
        "am": ("am", "공격형미드필더"),
        "rw": ("rw", "라이트윙"),
        "lw": ("lw", "레프트윙"),
        "st": ("st", "스트라이커"),
        "cf": ("cf", "센터포워드"),
    }
    for code, terms in position_map.items():
        if _contains_any(normalized, terms):
            return code.upper()
    if "풀백" in normalized:
        return "FULLBACK"
    if "윙어" in normalized:
        return "WINGER"
    if "미드필더" in normalized:
        return "MIDFIELDER"
    return None


def _resolve_foot_filter(question: str) -> str | None:
    normalized = _normalized_question_text(question)
    if "왼발" in normalized:
        return "left"
    if "오른발" in normalized:
        return "right"
    if "양발" in normalized:
        return "both"
    return None


def _resolve_status_filter(question: str) -> str | None:
    normalized = _normalized_question_text(question)
    if "inactive" in normalized or "비활성" in normalized:
        return "inactive"
    if "임대" in normalized or "loan" in normalized:
        return "loan"
    if "active" in normalized or "활동가능" in normalized:
        return "active"
    return None


def _build_position_sql_condition(position_filter: str) -> str:
    group_map = {
        "FULLBACK": ("RB", "LB"),
        "WINGER": ("RW", "LW"),
        "MIDFIELDER": ("DM", "CM", "AM"),
    }
    if position_filter in group_map:
        codes = "', '".join(group_map[position_filter])
        return f"(primary_position IN ('{codes}') OR secondary_position IN ('{codes}'))"
    return f"(primary_position = '{position_filter}' OR secondary_position = '{position_filter}')"


def _training_order_clause(question: str, *, aggregate: bool) -> str:
    normalized = _normalized_question_text(question)
    if _contains_any(normalized, ("가속", "accel", "감속", "decel")):
        if aggregate:
            return "avg_accel_count DESC NULLS LAST, avg_decel_count DESC NULLS LAST, avg_total_distance DESC NULLS LAST"
        return "tgs.accel_count DESC NULLS LAST, tgs.decel_count DESC NULLS LAST, tgs.total_distance DESC NULLS LAST"
    if _contains_any(normalized, ("highintensity", "intensity", "강도", "스프린트", "sprint")):
        if aggregate:
            return "high_sessions DESC NULLS LAST, avg_sprint_count DESC NULLS LAST, avg_total_distance DESC NULLS LAST"
        return "tgs.sprint_count DESC NULLS LAST, tgs.total_distance DESC NULLS LAST, tgs.accel_count DESC NULLS LAST"
    if aggregate:
        return "avg_total_distance DESC NULLS LAST, avg_sprint_count DESC NULLS LAST, recent_sessions DESC"
    return "tgs.total_distance DESC NULLS LAST, tgs.sprint_count DESC NULLS LAST, tgs.accel_count DESC NULLS LAST"


def _training_trend_order_clause(question: str) -> str:
    normalized = _normalized_question_text(question)
    if _contains_any(normalized, ("스프린트", "sprint")):
        return "sprint_ratio DESC NULLS LAST, distance_ratio DESC NULLS LAST, recent_high_sessions DESC NULLS LAST"
    return "distance_ratio DESC NULLS LAST, sprint_ratio DESC NULLS LAST, recent_high_sessions DESC NULLS LAST"


def _combined_workload_order_clause(*, question: str, mode: str) -> str:
    normalized = _normalized_question_text(question)
    if mode == "trend":
        if _contains_any(normalized, ("스프린트", "sprint")):
            return "acute_chronic_ratio DESC NULLS LAST, sprint_count_7d DESC NULLS LAST, acute_load_7d DESC NULLS LAST"
        if _contains_any(normalized, ("이동거리", "distance")):
            return "acute_chronic_ratio DESC NULLS LAST, total_distance_7d DESC NULLS LAST, acute_load_7d DESC NULLS LAST"
        return "acute_chronic_ratio DESC NULLS LAST, acute_load_7d DESC NULLS LAST, total_distance_7d DESC NULLS LAST"
    if _contains_any(normalized, ("스프린트", "sprint")):
        return "sprint_count_7d DESC NULLS LAST, acute_load_7d DESC NULLS LAST, total_distance_7d DESC NULLS LAST"
    if _contains_any(normalized, ("이동거리", "distance")):
        return "total_distance_7d DESC NULLS LAST, acute_load_7d DESC NULLS LAST, sprint_count_7d DESC NULLS LAST"
    return "acute_load_7d DESC NULLS LAST, total_distance_7d DESC NULLS LAST, sprint_count_7d DESC NULLS LAST"


def _recent_match_form_order_clause(question: str) -> str:
    normalized = _normalized_question_text(question)
    if _contains_any(normalized, ("스프린트", "sprint")):
        return "recent_matches DESC, avg_sprint_count DESC NULLS LAST, avg_total_distance DESC NULLS LAST"
    return "recent_matches DESC, avg_total_distance DESC NULLS LAST, avg_sprint_count DESC NULLS LAST"


def _recent_match_trend_order_clause(question: str, *, order_direction: str) -> str:
    normalized = _normalized_question_text(question)
    if _contains_any(normalized, ("스프린트", "sprint")):
        return (
            f"sprint_ratio {order_direction} NULLS LAST, "
            f"distance_ratio {order_direction} NULLS LAST, "
            "recent_matches DESC"
        )
    return (
        f"distance_ratio {order_direction} NULLS LAST, "
        f"sprint_ratio {order_direction} NULLS LAST, "
        "recent_matches DESC"
    )


def _chat_with_llama(*, system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": settings.llama_model,
        "stream": False,
        "format": "json",
        "keep_alive": "15m",
        "options": {
            "temperature": 0.1,
            "num_predict": 320,
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    response = _ollama_request("/api/chat", payload)
    message = response.get("message", {})
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(status_code=502, detail="Assistant returned an empty model response.")
    return content


def _force_answer_from_evidence(
    *,
    question: str,
    previous_steps: Sequence[AssistantQueryStep],
) -> str | None:
    preview_fallback = _build_fallback_answer_from_preview(previous_steps)
    if not any(step.action == "sql" and step.row_count is not None for step in previous_steps):
        return None
    if preview_fallback and _should_prefer_preview_fallback(previous_steps):
        return preview_fallback

    try:
        raw_response = _chat_with_llama(
            system_prompt=FINAL_ANSWER_SYSTEM_PROMPT,
            user_prompt=_build_final_answer_prompt(
                question=question,
                previous_steps=previous_steps,
            ),
        )
    except (AssistantAgentError, HTTPException):
        return None

    payload = _parse_agent_payload(raw_response)
    answer = _normalize_optional_text(payload.get("answer"))
    if answer:
        if preview_fallback and _answer_needs_more_evidence(answer):
            return preview_fallback
        return answer

    if str(payload.get("action", "")).strip().lower() == "answer":
        answer = _normalize_optional_text(payload.get("answer"))
        if answer:
            if preview_fallback and _answer_needs_more_evidence(answer):
                return preview_fallback
            return answer

    return preview_fallback


def _ollama_request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    headers = {"Accept": "application/json"}
    method = "GET"
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"

    request = Request(
        url=f"{settings.llama_base_url.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=settings.llama_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise AssistantAgentError(_extract_remote_error(raw) or f"Ollama request failed with status {exc.code}.") from exc
    except URLError as exc:
        raise AssistantAgentError(
            f"Ollama is not reachable at {settings.llama_base_url}. Start the Ollama app/server first."
        ) from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssistantAgentError("Ollama returned a non-JSON response.") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        raise AssistantAgentError(str(parsed["error"]))
    if not isinstance(parsed, dict):
        raise AssistantAgentError("Ollama returned an unexpected response shape.")
    return parsed


def _validate_read_only_sql(sql_query: str) -> str:
    normalized_query = sql_query.strip()
    if not normalized_query:
        raise HTTPException(status_code=400, detail="Assistant generated an empty SQL query.")
    if "--" in normalized_query or "/*" in normalized_query:
        raise HTTPException(status_code=400, detail="SQL comments are not allowed.")

    statement = normalized_query[:-1] if normalized_query.endswith(";") else normalized_query
    if ";" in statement:
        raise HTTPException(status_code=400, detail="Only a single SQL statement is allowed.")

    lowered = re.sub(r"\s+", " ", statement).strip().lower()
    if not lowered.startswith(("select ", "with ")):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")

    for pattern in BLOCKED_SQL_PATTERNS:
        if re.search(pattern, lowered):
            raise HTTPException(status_code=400, detail="Blocked SQL pattern detected in assistant query.")

    return statement


def _validate_sql_against_catalog(
    sql_query: str,
    schema_catalog: dict[str, dict[str, Any]],
) -> str | None:
    cte_names = _extract_cte_names(sql_query)
    alias_map, referenced_names, unknown_object_names = _extract_referenced_objects(
        sql_query,
        schema_catalog,
        cte_names=cte_names,
    )
    if unknown_object_names:
        return _format_unknown_object_error(unknown_object_names[0], schema_catalog=schema_catalog)

    referenced_objects = {object_name for object_name in alias_map.values() if object_name}
    if not referenced_objects:
        return None

    for alias, column_name in QUALIFIED_IDENTIFIER_PATTERN.findall(sql_query):
        normalized_alias = alias.lower()
        normalized_column = column_name.lower()
        if normalized_alias == "football":
            continue

        object_name = alias_map.get(normalized_alias)
        if not object_name:
            continue

        if normalized_column not in schema_catalog[object_name]["column_names_lower"]:
            return _format_unknown_column_error(
                normalized_column,
                referenced_objects=referenced_objects,
                schema_catalog=schema_catalog,
            )

    known_columns = set().union(
        *(schema_catalog[object_name]["column_names_lower"] for object_name in referenced_objects)
    )
    stripped_query = SQL_STRING_PATTERN.sub(" ", sql_query)
    stripped_query = QUALIFIED_IDENTIFIER_PATTERN.sub(" ", stripped_query)
    excluded_names = set(SQL_RESERVED_TOKENS)
    excluded_names.update(alias_map.keys())
    excluded_names.update(cte_names)
    excluded_names.update(referenced_names)
    excluded_names.update(_extract_as_aliases(sql_query))
    excluded_names.add("football")

    for match in IDENTIFIER_PATTERN.finditer(stripped_query):
        token = match.group(1).lower()
        if token in excluded_names or token in known_columns:
            continue
        if _is_function_call(stripped_query, match.end()):
            continue
        return _format_unknown_column_error(
            token,
            referenced_objects=referenced_objects,
            schema_catalog=schema_catalog,
        )

    return None


def _validate_sql_against_playbooks(
    sql_query: str,
    active_playbooks: set[str],
) -> str | None:
    lowered = sql_query.lower()

    if "latest_official_match_activity_leader" in active_playbooks:
        if "football.player_match_facts" in lowered and not any(
            marker in lowered
            for marker in ("football.matches", "match_date", "latest_official_match", "latest_match")
        ):
            return (
                "For latest official-match activity questions, first isolate the latest official match via football.matches "
                "with WHERE match_type = '공식', then join or filter football.player_match_facts by that match_id."
            )
        if "match_type = '공식'" not in sql_query and 'match_type = "공식"' not in sql_query:
            return (
                "This question is about the latest official match. Add a football.matches filter with "
                "match_type = '공식' before selecting the latest match_id."
            )

    if "latest_match_activity_leader" in active_playbooks:
        if "football.player_match_facts" in lowered and not any(
            marker in lowered
            for marker in ("football.matches", "match_date", "latest_match")
        ):
            return (
                "For latest-match activity questions, first isolate the latest match via football.matches "
                "(for example with a latest_match CTE ordered by match_date DESC LIMIT 1), then join or filter "
                "football.player_match_facts by that match_id."
            )

    return None


def _execute_read_only_sql(sql_query: str) -> list[dict[str, object | None]]:
    limit = settings.assistant_sql_max_rows + 1
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            rows = cursor.fetchmany(limit)

    safe_rows = [_json_safe(row) for row in rows[: settings.assistant_sql_max_rows]]
    return safe_rows


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _resolve_player_from_question(question: str) -> tuple[str, str] | None:
    resolved = _resolve_players_from_question(question, limit=1)
    return resolved[0] if resolved else None


def _resolve_players_from_question(question: str, *, limit: int = 2) -> list[tuple[str, str]]:
    normalized_question = question.casefold()
    rows = [
        (player_id, name)
        for player_id, name in _fetch_player_lookup_index()
        if name.casefold() in normalized_question
    ]
    rows.sort(key=lambda item: (-len(item[1]), item[1]))
    resolved: list[tuple[str, str]] = []
    seen_names: set[str] = set()
    for player_id, name in rows:
        if name in seen_names:
            continue
        seen_names.add(name)
        resolved.append((player_id, name))
        if len(resolved) >= limit:
            break
    return resolved


def _resolve_opponent_from_question(question: str) -> tuple[str, str] | None:
    normalized_question = question.casefold()
    matches = [
        (opponent_id, opponent_name)
        for opponent_id, opponent_name in _fetch_opponent_lookup_index()
        if opponent_name.casefold() in normalized_question
    ]
    if not matches:
        return None
    matches.sort(key=lambda item: (-len(item[1]), item[1]))
    return matches[0]
