from __future__ import annotations

from collections.abc import Sequence
import json
import re
from typing import Any

from fastapi import HTTPException

from ...schemas import AssistantQueryStep


def _build_user_prompt(
    *,
    question: str,
    schema_context: dict[str, Any],
    previous_steps: Sequence[AssistantQueryStep],
    join_hints: str,
) -> str:
    history = _format_step_history(previous_steps)
    return (
        f"User question:\n{question}\n\n"
        "Relevant schema catalog and query playbooks (JSON):\n"
        f"{json.dumps(schema_context, ensure_ascii=False, separators=(',', ':'))}\n\n"
        f"{join_hints}\n\n"
        f"Previous steps and results:\n{history}\n\n"
        "Return JSON only."
    )


def _build_final_answer_prompt(
    *,
    question: str,
    previous_steps: Sequence[AssistantQueryStep],
) -> str:
    history = _format_step_history(previous_steps)
    return (
        f"User question:\n{question}\n\n"
        f"SQL evidence and step history:\n{history}\n\n"
        "Return JSON only."
    )


def _format_step_history(steps: Sequence[AssistantQueryStep]) -> str:
    if not steps:
        return "No previous steps yet."

    lines: list[str] = []
    for step in steps:
        lines.append(f"Step {step.step} action={step.action}")
        if step.reason:
            lines.append(f"Reason: {step.reason}")
        if step.sql:
            lines.append(f"SQL: {step.sql}")
        if step.row_count is not None:
            lines.append(f"Row count: {step.row_count}")
        if step.error:
            lines.append(f"Error: {step.error}")
        if step.preview:
            preview_json = json.dumps(step.preview, ensure_ascii=False, default=str, separators=(",", ":"))
            lines.append(f"Preview: {preview_json}")
        lines.append("")
    return "\n".join(lines).strip()


def _extract_remote_error(raw: str) -> str | None:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip() or None
    if isinstance(parsed, dict) and parsed.get("error"):
        return str(parsed["error"]).strip()
    return raw.strip() or None


def _parse_agent_payload(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise HTTPException(status_code=502, detail="Assistant response was not valid JSON.")
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Assistant response was not parseable JSON.") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=502, detail="Assistant response must be a JSON object.")
    return parsed
